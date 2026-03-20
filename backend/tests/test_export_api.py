from __future__ import annotations

import json
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
from backend.app.models.employee_master import EmployeeMaster
from backend.app.services import standardize_workbook


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'export_api'
SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'
DESKTOP_ROOT = Path.home() / 'Desktop' / '202602???????' / '202602???????'

SAMPLE_KEYWORD = '\u6df1\u5733\u521b\u9020\u6b22\u4e50'
COMPANY_NAME = '\u521b\u9020\u6b22\u4e50'
APP_NAME = '\u5bfc\u51fa\u6d4b\u8bd5'


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


def build_test_context(test_name: str, *, salary_template: Path | None, final_tool_template: Path | None):
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'export.db'
    settings = Settings(
        app_name=APP_NAME,
        app_version='0.2.0',
        database_url=f'sqlite:///{database_path.as_posix()}',
        upload_dir=str(artifacts_dir / 'uploads'),
        samples_dir=str(artifacts_dir / 'samples'),
        templates_dir=str(artifacts_dir / 'templates'),
        outputs_dir=str(artifacts_dir / 'outputs'),
        salary_template_path=str(salary_template) if salary_template is not None else None,
        final_tool_template_path=str(final_tool_template) if final_tool_template is not None else None,
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


def create_batch(client: TestClient, sample_path: Path) -> str:
    response = client.post(
        '/api/v1/imports',
        data={
            'batch_name': 'export-batch',
            'regions': json.dumps(['shenzhen'], ensure_ascii=False),
            'company_names': json.dumps([COMPANY_NAME], ensure_ascii=False),
        },
        files=[('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
    )
    assert response.status_code == 201
    return response.json()['data']['id']


def seed_employee_for_first_record(session_factory, sample_path: Path) -> None:
    standardized = standardize_workbook(sample_path, region='shenzhen', company_name=COMPANY_NAME)
    first = standardized.records[0]
    db: Session = session_factory()
    try:
        db.add(
            EmployeeMaster(
                employee_id='01620',
                person_name=first.values['person_name'],
                id_number=first.values['id_number'],
                company_name=COMPANY_NAME,
                active=True,
            )
        )
        db.commit()
    finally:
        db.close()


def test_export_batch_endpoint_writes_both_template_outputs() -> None:
    salary_template = find_template('\u85aa\u916c')
    tool_template = find_template('\u6700\u7ec8\u7248')
    sample_path = find_sample(SAMPLE_KEYWORD)
    client, _settings, session_factory = build_test_context(
        'export_success',
        salary_template=salary_template,
        final_tool_template=tool_template,
    )
    seed_employee_for_first_record(session_factory, sample_path)

    with client:
        batch_id = create_batch(client, sample_path)
        match_response = client.post(f'/api/v1/imports/{batch_id}/match')
        export_response = client.post(f'/api/v1/imports/{batch_id}/export')
        get_response = client.get(f'/api/v1/imports/{batch_id}/export')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert match_response.status_code == 200
    assert export_response.status_code == 200
    payload = export_response.json()['data']
    assert payload['batch_id'] == batch_id
    assert payload['status'] == 'exported'
    assert payload['export_status'] == 'completed'
    assert len(payload['artifacts']) == 2
    assert all(item['status'] == 'completed' for item in payload['artifacts'])
    assert all(Path(item['file_path']).exists() for item in payload['artifacts'])

    get_payload = get_response.json()['data']
    assert get_payload['export_job_id'] == payload['export_job_id']
    assert get_payload['export_status'] == 'completed'
    assert len(get_payload['artifacts']) == 2
    assert detail_response.json()['data']['status'] == 'exported'



def test_export_batch_endpoint_fails_when_any_template_is_missing() -> None:
    salary_template = find_template('\u85aa\u916c')
    sample_path = find_sample(SAMPLE_KEYWORD)
    missing_tool = ARTIFACTS_ROOT / 'missing-template.xlsx'
    client, _settings, session_factory = build_test_context(
        'export_failed',
        salary_template=salary_template,
        final_tool_template=missing_tool,
    )
    seed_employee_for_first_record(session_factory, sample_path)

    with client:
        batch_id = create_batch(client, sample_path)
        match_response = client.post(f'/api/v1/imports/{batch_id}/match')
        export_response = client.post(f'/api/v1/imports/{batch_id}/export')
        get_response = client.get(f'/api/v1/imports/{batch_id}/export')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert match_response.status_code == 200
    assert export_response.status_code == 200
    payload = export_response.json()['data']
    assert payload['status'] == 'failed'
    assert payload['export_status'] == 'failed'
    salary_artifact = next(item for item in payload['artifacts'] if item['template_type'] == 'salary')
    tool_artifact = next(item for item in payload['artifacts'] if item['template_type'] == 'final_tool')
    assert salary_artifact['status'] == 'completed'
    assert tool_artifact['status'] == 'failed'
    assert tool_artifact['error_message']

    get_payload = get_response.json()['data']
    assert get_payload['export_status'] == 'failed'
    assert detail_response.json()['data']['status'] == 'failed'



def test_export_batch_endpoint_blocks_when_matching_has_not_run() -> None:
    salary_template = find_template('\u85aa\u916c')
    tool_template = find_template('\u6700\u7ec8\u7248')
    sample_path = find_sample(SAMPLE_KEYWORD)
    client, _settings, _session_factory = build_test_context(
        'export_blocked',
        salary_template=salary_template,
        final_tool_template=tool_template,
    )

    with client:
        batch_id = create_batch(client, sample_path)
        export_response = client.post(f'/api/v1/imports/{batch_id}/export')
        get_response = client.get(f'/api/v1/imports/{batch_id}/export')

    assert export_response.status_code == 409
    assert export_response.json()['error']['code'] == 'http_error'
    assert 'matching' in export_response.json()['error']['message'].lower()
    assert get_response.status_code == 200
    assert get_response.json()['data']['export_job_id'] is None
    assert get_response.json()['data']['blocked_reason']
