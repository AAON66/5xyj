from __future__ import annotations

import json
import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.models import Base
from backend.app.models.employee_master import EmployeeMaster
from backend.tests.support.export_fixtures import require_sample_workbook, resolve_required_export_templates


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'dashboard_api'
SAMPLE_KEYWORD = '\u6df1\u5733\u521b\u9020\u6b22\u4e50'
COMPANY_NAME = '\u521b\u9020\u6b22\u4e50'
APP_NAME = '\u770b\u677f\u6d4b\u8bd5'


def build_test_context(test_name: str) -> tuple[TestClient, Settings, object]:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    templates = resolve_required_export_templates()
    database_path = artifacts_dir / 'dashboard.db'
    settings = Settings(
        app_name=APP_NAME,
        app_version='0.2.0',
        auth_enabled=False,
        database_url=f'sqlite:///{database_path.as_posix()}',
        upload_dir=str(artifacts_dir / 'uploads'),
        samples_dir=str(artifacts_dir / 'samples'),
        templates_dir=str(artifacts_dir / 'templates'),
        outputs_dir=str(artifacts_dir / 'outputs'),
        salary_template_path=str(templates.salary),
        final_tool_template_path=str(templates.final_tool),
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


def create_batch(client: TestClient, sample_path) -> str:
    response = client.post(
        '/api/v1/imports',
        data={
            'batch_name': 'dashboard-batch',
            'regions': json.dumps(['shenzhen'], ensure_ascii=False),
            'company_names': json.dumps([COMPANY_NAME], ensure_ascii=False),
        },
        files=[('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))],
    )
    assert response.status_code == 201
    return response.json()['data']['id']


def seed_employee_for_match(session_factory, *, employee_id: str, person_name: str, id_number: str) -> None:
    db: Session = session_factory()
    try:
        db.add(
            EmployeeMaster(
                employee_id=employee_id,
                person_name=person_name,
                id_number=id_number,
                company_name=COMPANY_NAME,
                active=True,
            )
        )
        db.commit()
    finally:
        db.close()


def test_dashboard_overview_returns_zero_counts_for_empty_workspace() -> None:
    client, _settings, _session_factory = build_test_context('empty')

    with client:
        response = client.get('/api/v1/dashboard/overview')

    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['totals']['total_batches'] == 0
    assert payload['totals']['total_source_files'] == 0
    assert payload['totals']['total_normalized_records'] == 0
    assert payload['totals']['total_validation_issues'] == 0
    assert payload['totals']['total_match_results'] == 0
    assert payload['totals']['total_export_jobs'] == 0
    assert payload['recent_batches'] == []
    assert payload['batch_status_counts']['uploaded'] == 0
    assert payload['match_status_counts']['matched'] == 0
    assert payload['export_status_counts']['completed'] == 0



def test_dashboard_overview_aggregates_batch_runtime_counts() -> None:
    client, _settings, session_factory = build_test_context('populated')
    sample_path = require_sample_workbook(SAMPLE_KEYWORD)

    with client:
        batch_id = create_batch(client, sample_path)
        preview_response = client.post(f'/api/v1/imports/{batch_id}/parse')
        preview_record = preview_response.json()['data']['source_files'][0]['preview_records'][0]

    seed_employee_for_match(
        session_factory,
        employee_id='01620',
        person_name=preview_record['values']['person_name'],
        id_number=preview_record['values']['id_number'],
    )

    with client:
        validate_response = client.post(f'/api/v1/imports/{batch_id}/validate')
        match_response = client.post(f'/api/v1/imports/{batch_id}/match')
        export_response = client.post(f'/api/v1/imports/{batch_id}/export')
        overview_response = client.get('/api/v1/dashboard/overview')

    assert validate_response.status_code == 200
    assert match_response.status_code == 200
    assert export_response.status_code == 200

    payload = overview_response.json()['data']
    assert payload['totals']['total_batches'] == 1
    assert payload['totals']['total_source_files'] == 1
    assert payload['totals']['total_normalized_records'] > 0
    assert payload['totals']['total_match_results'] > 0
    assert payload['totals']['total_export_jobs'] == 1
    assert payload['totals']['active_employee_masters'] == 1
    assert payload['batch_status_counts']['exported'] == 1
    assert payload['match_status_counts']['matched'] >= 1
    assert payload['export_status_counts']['completed'] == 1
    assert payload['recent_batches'][0]['batch_id'] == batch_id
    assert payload['recent_batches'][0]['status'] == 'exported'
    assert payload['recent_batches'][0]['file_count'] == 1
    assert payload['recent_batches'][0]['export_job_count'] == 1
    assert payload['recent_batches'][0]['match_result_count'] > 0
