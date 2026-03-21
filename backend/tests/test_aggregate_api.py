from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import ROOT_DIR, Settings, get_settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.models import Base
from backend.app.services import standardize_workbook


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'aggregate_api'
SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'
DESKTOP_ROOT = Path.home() / 'Desktop' / '202602\u793e\u4fdd\u516c\u79ef\u91d1\u53f0\u8d26' / '202602\u793e\u4fdd\u516c\u79ef\u91d1\u6c47\u603b'

SAMPLE_KEYWORD = '\u6df1\u5733\u521b\u9020\u6b22\u4e50'
COMPANY_NAME = '\u521b\u9020\u6b22\u4e50'
APP_NAME = '\u5feb\u901f\u805a\u5408\u6d4b\u8bd5'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def find_template(keyword: str) -> Path:
    settings = get_settings()
    configured = [settings.salary_template_file, settings.final_tool_template_file]
    for path in configured:
        if path is not None and path.exists() and keyword in path.name:
            return path
    if DESKTOP_ROOT.exists():
        for path in sorted(DESKTOP_ROOT.glob('*.xlsx')):
            if keyword in path.name:
                return path
    pytest.skip(f'Template containing {keyword!r} was not found in configured paths or {DESKTOP_ROOT}.')


def build_test_context(test_name: str, *, salary_template: Path, final_tool_template: Path):
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'aggregate.db'
    settings = Settings(
        app_name=APP_NAME,
        app_version='0.2.0',
        database_url=f'sqlite:///{database_path.as_posix()}',
        upload_dir=str(artifacts_dir / 'uploads'),
        samples_dir=str(artifacts_dir / 'samples'),
        templates_dir=str(artifacts_dir / 'templates'),
        outputs_dir=str(artifacts_dir / 'outputs'),
        salary_template_path=str(salary_template),
        final_tool_template_path=str(final_tool_template),
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
    return TestClient(app), settings, session_factory


def make_employee_master_csv(sample_path: Path) -> bytes:
    standardized = standardize_workbook(sample_path, region='shenzhen', company_name=COMPANY_NAME)
    first = standardized.records[0]
    return (
        '\u5de5\u53f7,\u59d3\u540d,\u8eab\u4efd\u8bc1\u53f7,\u516c\u53f8\u540d\u79f0,\u90e8\u95e8,\u662f\u5426\u5728\u804c\n'
        f"E9001,{first.values['person_name']},{first.values['id_number']},{COMPANY_NAME},\u8fd0\u8425,\u662f\n"
    ).encode('utf-8-sig')


def test_aggregate_endpoint_exports_both_templates_without_employee_master() -> None:
    salary_template = find_template('\u85aa\u916c')
    tool_template = find_template('\u6700\u7ec8\u7248')
    sample_path = find_sample(SAMPLE_KEYWORD)
    client, _settings, _session_factory = build_test_context(
        'aggregate_without_master',
        salary_template=salary_template,
        final_tool_template=tool_template,
    )

    with client:
        response = client.post(
            '/api/v1/aggregate',
            data={'batch_name': 'quick-aggregate-no-master'},
            files=[
                (
                    'files',
                    (
                        sample_path.name,
                        sample_path.read_bytes(),
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    ),
                )
            ],
        )

    assert response.status_code == 201
    payload = response.json()['data']
    assert payload['batch_name'] == 'quick-aggregate-no-master'
    assert payload['status'] == 'exported'
    assert payload['export_status'] == 'completed'
    assert payload['blocked_reason'] is None
    assert payload['employee_master'] is None
    assert payload['matched_count'] == 0
    assert payload['unmatched_count'] >= 1
    assert len(payload['source_files']) == 1
    assert payload['source_files'][0]['region'] == 'shenzhen'
    assert payload['source_files'][0]['company_name'] == COMPANY_NAME
    assert payload['source_files'][0]['normalized_record_count'] >= 1
    assert len(payload['artifacts']) == 2
    assert all(item['status'] == 'completed' for item in payload['artifacts'])
    assert all(Path(item['file_path']).exists() for item in payload['artifacts'])



def test_aggregate_endpoint_imports_employee_master_and_matches_records() -> None:
    salary_template = find_template('\u85aa\u916c')
    tool_template = find_template('\u6700\u7ec8\u7248')
    sample_path = find_sample(SAMPLE_KEYWORD)
    employee_csv = make_employee_master_csv(sample_path)
    client, _settings, _session_factory = build_test_context(
        'aggregate_with_master',
        salary_template=salary_template,
        final_tool_template=tool_template,
    )

    with client:
        response = client.post(
            '/api/v1/aggregate',
            data={'batch_name': 'quick-aggregate-with-master'},
            files=[
                (
                    'files',
                    (
                        sample_path.name,
                        sample_path.read_bytes(),
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    ),
                ),
                ('employee_master_file', ('employee_master.csv', employee_csv, 'text/csv')),
            ],
        )

    assert response.status_code == 201
    payload = response.json()['data']
    assert payload['batch_name'] == 'quick-aggregate-with-master'
    assert payload['status'] == 'exported'
    assert payload['export_status'] == 'completed'
    assert payload['employee_master'] is not None
    assert payload['employee_master']['created_count'] == 1
    assert payload['matched_count'] >= 1
    assert payload['source_files'][0]['region'] == 'shenzhen'
    assert payload['source_files'][0]['company_name'] == COMPANY_NAME
    assert len(payload['artifacts']) == 2
    assert all(item['status'] == 'completed' for item in payload['artifacts'])
    assert all(Path(item['file_path']).exists() for item in payload['artifacts'])
