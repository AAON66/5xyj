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
from backend.app.models import Base

ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'mapping_api'
SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'


def build_test_client(test_name: str) -> tuple[TestClient, Settings]:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'mappings.db'
    settings = Settings(
        app_name='映射测试',
        app_version='0.2.0',
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


def test_mapping_api_persists_and_applies_manual_override() -> None:
    client, _ = build_test_client('manual_override')
    sample_path = find_sample('深圳')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'shenzhen', 'company_names': '深圳公司'},
        )
        batch_id = created.json()['data']['id']

        parse_response = client.post(f'/api/v1/imports/{batch_id}/parse')
        assert parse_response.status_code == 200

        mappings_response = client.get(f'/api/v1/mappings?batch_id={batch_id}')
        assert mappings_response.status_code == 200
        mappings_payload = mappings_response.json()['data']
        assert mappings_payload['items']
        assert 'person_name' in mappings_payload['available_canonical_fields']

        person_name_mapping = next(item for item in mappings_payload['items'] if item['canonical_field'] == 'person_name')
        patch_response = client.patch(
            f"/api/v1/mappings/{person_name_mapping['id']}",
            json={'canonical_field': 'employee_id'},
        )
        assert patch_response.status_code == 200
        assert patch_response.json()['data']['canonical_field'] == 'employee_id'
        assert patch_response.json()['data']['mapping_source'] == 'manual'
        assert patch_response.json()['data']['manually_overridden'] is True

        preview_response = client.get(f'/api/v1/imports/{batch_id}/preview')
        assert preview_response.status_code == 200
        file_preview = preview_response.json()['data']['source_files'][0]
        updated_mapping = next(
            item for item in file_preview['header_mappings'] if item['raw_header_signature'] == person_name_mapping['raw_header_signature']
        )
        assert updated_mapping['canonical_field'] == 'employee_id'
        assert updated_mapping['mapping_source'] == 'manual'
        first_record = file_preview['preview_records'][0]
        assert first_record['values']['employee_id'] == first_record['raw_values'][person_name_mapping['raw_header_signature']]


def test_mapping_api_lists_second_region_batch() -> None:
    client, _ = build_test_client('list_second_region')
    sample_path = find_sample('广分')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
            data={'regions': 'guangzhou', 'company_names': '广州分公司'},
        )
        batch_id = created.json()['data']['id']
        parse_response = client.post(f'/api/v1/imports/{batch_id}/parse')
        assert parse_response.status_code == 200

        mappings_response = client.get(f'/api/v1/mappings?batch_id={batch_id}')

    assert mappings_response.status_code == 200
    payload = mappings_response.json()['data']
    assert payload['items']
    assert any(item['source_file_name'] == sample_path.name for item in payload['items'])
    assert any(item['canonical_field'] == 'person_name' for item in payload['items'])


def test_mapping_api_rejects_unknown_canonical_field() -> None:
    client, _ = build_test_client('invalid_canonical_field')
    sample_path = find_sample('深圳')

    with client:
        created = client.post(
            '/api/v1/imports',
            files=[('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
        )
        batch_id = created.json()['data']['id']
        client.post(f'/api/v1/imports/{batch_id}/parse')
        mappings_response = client.get(f'/api/v1/mappings?batch_id={batch_id}')
        mapping_id = mappings_response.json()['data']['items'][0]['id']

        patch_response = client.patch(f'/api/v1/mappings/{mapping_id}', json={'canonical_field': 'not_a_field'})

    assert patch_response.status_code == 400
    assert patch_response.json()['error']['code'] == 'http_error'
