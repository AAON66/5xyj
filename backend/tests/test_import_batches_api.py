from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.services import import_service as import_service_module
from backend.app.services.region_detection_service import RegionDetectionResult
from backend.app.models import Base


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'import_batches_api'
SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'


def build_test_client(test_name: str) -> tuple[TestClient, Settings]:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'imports.db'
    settings = Settings(
        app_name='导入测试',
        app_version='0.2.0',
        auth_enabled=False,
        database_url=f'sqlite:///{database_path.as_posix()}',
        upload_dir=str(artifacts_dir / 'uploads'),
        samples_dir=str(artifacts_dir / 'samples'),
        templates_dir=str(artifacts_dir / 'templates'),
        outputs_dir=str(artifacts_dir / 'outputs'),
        log_format='plain',
    )

    engine = create_database_engine(settings)
    session_factory = create_session_factory(settings)
    Base.metadata.create_all(engine)

    app = create_app(settings)

    def override_get_db():
        db: Session = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, settings


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def test_create_import_batch_persists_files_and_metadata() -> None:
    client, settings = build_test_client('create_batch')

    with client:
        response = client.post(
            '/api/v1/imports',
            data={
                'batch_name': '2026-02 社保批次',
                'regions': '["guangzhou", "hangzhou"]',
                'company_names': '["广分", "杭州聚变"]',
            },
            files=[
                ('files', ('guangzhou.xlsx', b'sheet-a', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
                ('files', ('hangzhou.xls', b'sheet-bb', 'application/vnd.ms-excel')),
            ],
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload['success'] is True
    assert payload['message'] == 'Import batch created.'
    assert payload['data']['batch_name'] == '2026-02 社保批次'
    assert payload['data']['status'] == 'uploaded'
    assert payload['data']['file_count'] == 2

    source_files = payload['data']['source_files']
    assert [item['region'] for item in source_files] == ['guangzhou', 'hangzhou']
    assert [item['company_name'] for item in source_files] == ['广分', '杭州聚变']
    assert [item['file_size'] for item in source_files] == [7, 8]

    batch_dir = settings.upload_path / payload['data']['id']
    assert batch_dir.exists()
    assert len(list(batch_dir.iterdir())) == 2
    assert all(Path(item['file_path']).exists() for item in source_files)


def test_list_and_detail_import_batches_return_saved_batch() -> None:
    client, _ = build_test_client('list_detail')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[('files', ('wuhan.xlsx', b'row-data', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'wuhan', 'company_names': '武汉公司'},
        )
        batch_id = created.json()['data']['id']

        list_response = client.get('/api/v1/imports')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert list_response.status_code == 200
    assert list_response.json()['success'] is True
    assert list_response.json()['data'][0]['id'] == batch_id
    assert list_response.json()['data'][0]['file_count'] == 1

    assert detail_response.status_code == 200
    assert detail_response.json()['data']['id'] == batch_id
    assert detail_response.json()['data']['source_files'][0]['region'] == 'wuhan'
    assert detail_response.json()['data']['source_files'][0]['company_name'] == '武汉公司'


def test_delete_import_batch_removes_batch_and_uploaded_files() -> None:
    client, settings = build_test_client('delete_batch')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[('files', ('wuhan.xlsx', b'row-data', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'wuhan', 'company_names': '武汉公司'},
        )
        batch_id = created.json()['data']['id']
        batch_dir = settings.upload_path / batch_id

        delete_response = client.delete(f'/api/v1/imports/{batch_id}')
        list_response = client.get('/api/v1/imports')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert delete_response.status_code == 204
    assert not batch_dir.exists()
    assert list_response.status_code == 200
    assert list_response.json()['data'] == []
    assert detail_response.status_code == 404


def test_bulk_delete_import_batches_removes_multiple_batches_and_reports_missing_ids() -> None:
    client, settings = build_test_client('bulk_delete_batches')

    with client:
        created_a = client.post(
            '/api/v1/imports',
            files=[('files', ('a.xlsx', b'a-data', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'guangzhou', 'company_names': 'A'},
        )
        created_b = client.post(
            '/api/v1/imports',
            files=[('files', ('b.xlsx', b'b-data', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'hangzhou', 'company_names': 'B'},
        )
        batch_a = created_a.json()['data']['id']
        batch_b = created_b.json()['data']['id']

        batch_a_dir = settings.upload_path / batch_a
        batch_b_dir = settings.upload_path / batch_b

        delete_response = client.post('/api/v1/imports/bulk-delete', json={'batch_ids': [batch_a, 'missing-batch', batch_b]})
        list_response = client.get('/api/v1/imports')

    assert delete_response.status_code == 200
    payload = delete_response.json()['data']
    assert payload['deleted_count'] == 2
    assert payload['deleted_ids'] == [batch_a, batch_b]
    assert payload['missing_ids'] == ['missing-batch']
    assert not batch_a_dir.exists()
    assert not batch_b_dir.exists()
    assert list_response.json()['data'] == []


def test_parse_and_preview_import_batch_return_normalized_preview() -> None:
    client, _ = build_test_client('parse_preview')
    sample_path = find_sample('深圳创造欢乐')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'shenzhen', 'company_names': '创造欢乐'},
        )
        batch_id = created.json()['data']['id']

        parse_response = client.post(f'/api/v1/imports/{batch_id}/parse')
        preview_response = client.get(f'/api/v1/imports/{batch_id}/preview')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert parse_response.status_code == 200
    parse_payload = parse_response.json()['data']
    assert parse_payload['batch_id'] == batch_id
    assert parse_payload['status'] == 'normalized'
    assert len(parse_payload['source_files']) == 1
    file_preview = parse_payload['source_files'][0]
    assert file_preview['raw_sheet_name'] == '申报明细'
    assert file_preview['normalized_record_count'] > 0
    assert file_preview['filtered_row_count'] > 0
    assert any(item['canonical_field'] == 'person_name' for item in file_preview['header_mappings'])
    assert any(item['reason'] == 'group_header' for item in file_preview['filtered_rows'])
    assert file_preview['preview_records'][0]['values']['person_name']
    assert '基本养老保险（单位） / 费率' in file_preview['preview_records'][0]['unmapped_values']

    assert preview_response.status_code == 200
    preview_payload = preview_response.json()['data']
    assert preview_payload['batch_id'] == batch_id
    assert preview_payload['source_files'][0]['raw_sheet_name'] == '申报明细'
    assert preview_payload['source_files'][0]['preview_records'][0]['values']['person_name'] == file_preview['preview_records'][0]['values']['person_name']

    assert detail_response.status_code == 200
    assert detail_response.json()['data']['status'] == 'normalized'


def test_parse_import_batch_returns_not_found_for_unknown_batch() -> None:
    client, _ = build_test_client('parse_missing')

    with client:
        response = client.post('/api/v1/imports/missing-batch/parse')

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'not_found'


def test_preview_import_batch_returns_not_found_for_unknown_batch() -> None:
    client, _ = build_test_client('preview_missing')

    with client:
        response = client.get('/api/v1/imports/missing-batch/preview')

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'not_found'


def test_preview_import_batch_can_scope_to_single_source_file() -> None:
    client, _ = build_test_client('preview_single_source_file')
    shenzhen_sample = find_sample('深圳创造欢乐')
    guangzhou_sample = find_sample('广分')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[
                ('files', (shenzhen_sample.name, shenzhen_sample.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
                ('files', (guangzhou_sample.name, guangzhou_sample.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
            ],
            data={'regions': '["shenzhen", "guangzhou"]', 'company_names': '["深圳公司", "广州分公司"]'},
        )
        batch_payload = created.json()['data']
        batch_id = batch_payload['id']
        second_source_file_id = batch_payload['source_files'][1]['id']

        client.post(f'/api/v1/imports/{batch_id}/parse')
        preview_response = client.get(f'/api/v1/imports/{batch_id}/preview', params={'source_file_id': second_source_file_id})

    assert preview_response.status_code == 200
    payload = preview_response.json()['data']
    assert len(payload['source_files']) == 1
    assert payload['source_files'][0]['source_file_id'] == second_source_file_id
    assert payload['source_files'][0]['file_name'] == guangzhou_sample.name


def test_preview_import_batch_rejects_unknown_source_file() -> None:
    client, _ = build_test_client('preview_unknown_source_file')
    sample_path = find_sample('深圳创造欢乐')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'shenzhen', 'company_names': '创造欢乐'},
        )
        batch_id = created.json()['data']['id']
        client.post(f'/api/v1/imports/{batch_id}/parse')
        response = client.get(f'/api/v1/imports/{batch_id}/preview', params={'source_file_id': 'missing-source-file'})

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'not_found'


def test_create_import_batch_rejects_invalid_extension() -> None:
    client, settings = build_test_client('invalid_extension')

    with client:
        response = client.post(
            '/api/v1/imports',
            files=[('files', ('notes.txt', b'bad', 'text/plain'))],
        )

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'http_error'
    assert '.txt' in response.json()['error']['message']
    assert not any(settings.upload_path.iterdir())


def test_create_import_batch_rejects_metadata_length_mismatch() -> None:
    client, _ = build_test_client('metadata_mismatch')

    with client:
        response = client.post(
            '/api/v1/imports',
            data={
                'regions': '["guangzhou", "hangzhou"]',
                'company_names': '["only-one", "two", "three"]',
            },
            files=[
                ('files', ('g1.xlsx', b'one', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
                ('files', ('g2.xlsx', b'two', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
            ],
        )

    assert response.status_code == 400
    assert 'company_names' in response.json()['error']['message']



def test_create_import_batch_prefers_filename_region_before_workbook_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = build_test_client('filename_region_fast_path')

    def fail_if_called(*args, **kwargs):
        raise AssertionError('Workbook region detection should not run when filename already reveals the region.')

    monkeypatch.setattr(import_service_module, 'detect_region_for_workbook', fail_if_called)

    with client:
        response = client.post(
            '/api/v1/imports',
            files=[
                (
                    'files',
                    ('深圳无限增长202602公积金账单.xlsx', b'not-a-real-workbook-but-good-enough', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                )
            ],
        )

    assert response.status_code == 201
    payload = response.json()['data']
    assert payload['source_files'][0]['region'] == 'shenzhen'



def test_create_import_batch_falls_back_to_workbook_region_detection_when_filename_is_generic(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = build_test_client('generic_filename_region_fallback')

    def fake_detection(*args, **kwargs):
        return RegionDetectionResult(
            region='xiamen',
            confidence=0.95,
            source='rule',
            reason='test-fallback',
            local_confidence=0.95,
            llm_confidence=None,
        )

    monkeypatch.setattr(import_service_module, 'detect_region_for_workbook', fake_detection)

    with client:
        response = client.post(
            '/api/v1/imports',
            files=[
                (
                    'files',
                    ('generic.xlsx', b'not-a-real-workbook-but-good-enough', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                )
            ],
        )

    assert response.status_code == 201
    payload = response.json()['data']
    assert payload['source_files'][0]['region'] == 'xiamen'
