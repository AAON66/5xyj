from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.models import Base
from backend.app.models import EmployeeMasterAudit
from backend.app.models.employee_master import EmployeeMaster
from backend.app.models.enums import EmployeeAuditAction
from backend.app.services.batch_runtime_service import _build_missing_housing_warning_contexts
from backend.app.services import standardize_workbook


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'validation_matching_api'
SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'
HOUSING_SAMPLES_DIR = ROOT_DIR / 'data' / 'samples' / '\u516c\u79ef\u91d1'

GUANGZHOU_KEYWORD = '\u5e7f\u5206'
XIAMEN_KEYWORD = '\u53a6\u95e8202602\u793e\u4fdd\u8d26\u5355.xlsx'
XIAMEN_SUPPLEMENT_KEYWORD = '\u53a6\u95e8202602\u793e\u4fdd\u8d26\u5355\uff08\u8865\u7f341\u6708\u5165\u804c2\u4eba\uff09'
CHANGSHA_KEYWORD = '\u957f\u6c99202602\u793e\u4fdd\u8d26\u5355'
SHENZHEN_KEYWORD = '\u6df1\u5733\u521b\u9020\u6b22\u4e50'
SHENZHEN_MISSING_HOUSING_KEYWORD = '\u6df1\u5733\u96f6\u4e00\u8fd0\u8425202602'
XIAMEN_HOUSING_KEYWORD = '\u53a6\u95e8\u516c\u79ef\u91d1202602'
GUANGZHOU_COMPANY = '\u5e7f\u5206\u793a\u4f8b'
XIAMEN_COMPANY = '\u53a6\u95e8\u793a\u4f8b'
CHANGSHA_COMPANY = '\u957f\u6c99\u793a\u4f8b'
SHENZHEN_COMPANY = '\u521b\u9020\u6b22\u4e50'
SHENZHEN_MISSING_HOUSING_COMPANY = '\u96f6\u4e00\u8fd0\u8425'
OTHER_COMPANY = '\u5176\u5b83\u516c\u53f8'
APP_NAME = '\u6821\u9a8c\u5339\u914d\u6d4b\u8bd5'


def build_test_context(test_name: str):
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'runtime.db'
    settings = Settings(
        app_name=APP_NAME,
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
    return TestClient(app), settings, session_factory


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def find_housing_sample(keyword: str) -> Path:
    for path in sorted(HOUSING_SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Housing sample containing {keyword!r} was not found in {HOUSING_SAMPLES_DIR}.')


def create_batch(client: TestClient, files: list[tuple[Path, str, str]], batch_name: str = 'runtime-batch') -> str:
    response = client.post(
        '/api/v1/imports',
        data={
            'batch_name': batch_name,
            'regions': json.dumps([item[1] for item in files], ensure_ascii=False),
            'company_names': json.dumps([item[2] for item in files], ensure_ascii=False),
        },
        files=[
            ('files', (sample_path.name, sample_path.read_bytes(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
            for sample_path, _region, _company in files
        ],
    )
    assert response.status_code == 201
    return response.json()['data']['id']


def seed_employees(session_factory, employees: list[EmployeeMaster]) -> None:
    db: Session = session_factory()
    try:
        db.add_all(employees)
        db.commit()
    finally:
        db.close()


def seed_employee_audits(session_factory, audits: list[EmployeeMasterAudit]) -> None:
    db: Session = session_factory()
    try:
        db.add_all(audits)
        db.commit()
    finally:
        db.close()


def test_validate_batch_endpoint_returns_issue_summary_for_multiple_regions() -> None:
    client, _settings, _session_factory = build_test_context('validate_multi_region')
    guangzhou = find_sample(GUANGZHOU_KEYWORD)
    xiamen = find_sample(XIAMEN_KEYWORD)

    with client:
        batch_id = create_batch(
            client,
            [
                (guangzhou, 'guangzhou', GUANGZHOU_COMPANY),
                (xiamen, 'xiamen', XIAMEN_COMPANY),
            ],
            batch_name='validate-batch',
        )
        validate_response = client.post(f'/api/v1/imports/{batch_id}/validate')
        get_response = client.get(f'/api/v1/imports/{batch_id}/validation')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert validate_response.status_code == 200
    validate_payload = validate_response.json()['data']
    assert validate_payload['batch_id'] == batch_id
    assert validate_payload['status'] == 'validated'
    assert len(validate_payload['source_files']) == 2
    assert validate_payload['total_issue_count'] == 0
    assert all(item['issue_count'] == 0 for item in validate_payload['source_files'])
    assert all(item['raw_sheet_name'] for item in validate_payload['source_files'])

    assert get_response.status_code == 200
    assert get_response.json()['data']['total_issue_count'] == 0
    assert detail_response.json()['data']['status'] == 'validated'



def test_match_batch_endpoint_blocks_when_employee_master_is_missing() -> None:
    client, _settings, _session_factory = build_test_context('match_blocked')
    changsha = find_sample(CHANGSHA_KEYWORD)

    with client:
        batch_id = create_batch(client, [(changsha, 'changsha', CHANGSHA_COMPANY)], batch_name='blocked-batch')
        match_response = client.post(f'/api/v1/imports/{batch_id}/match')
        get_response = client.get(f'/api/v1/imports/{batch_id}/match')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert match_response.status_code == 200
    match_payload = match_response.json()['data']
    assert match_payload['status'] == 'blocked'
    assert match_payload['employee_master_available'] is False
    assert match_payload['employee_master_count'] == 0
    assert match_payload['blocked_reason']
    assert match_payload['total_records'] > 0

    assert get_response.status_code == 200
    assert get_response.json()['data']['status'] == 'blocked'
    assert detail_response.json()['data']['status'] == 'blocked'


def test_match_batch_endpoint_uses_historical_employee_audit_snapshot_when_active_master_is_missing() -> None:
    client, _settings, session_factory = build_test_context('match_historical_audit_snapshot')
    guangzhou = find_sample(GUANGZHOU_KEYWORD)
    standardized = standardize_workbook(guangzhou, region='guangzhou', company_name=GUANGZHOU_COMPANY)
    first = standardized.records[0]

    seed_employee_audits(
        session_factory,
        [
            EmployeeMasterAudit(
                employee_master_id=None,
                employee_id_snapshot='H1001',
                action=EmployeeAuditAction.MANUAL_CREATE,
                note='Recovered historical employee identity.',
                snapshot={
                    'employee_id': 'H1001',
                    'person_name': first.values['person_name'],
                    'id_number': first.values['id_number'],
                    'company_name': OTHER_COMPANY,
                    'active': True,
                },
            )
        ],
    )

    with client:
        batch_id = create_batch(client, [(guangzhou, 'guangzhou', GUANGZHOU_COMPANY)], batch_name='historical-match-batch')
        match_response = client.post(f'/api/v1/imports/{batch_id}/match')
        get_response = client.get(f'/api/v1/imports/{batch_id}/match')

    assert match_response.status_code == 200
    payload = match_response.json()['data']
    assert payload['status'] == 'matched'
    assert payload['employee_master_available'] is True
    assert payload['employee_master_count'] == 1
    file_results = payload['source_files'][0]['results']
    indexed = {item['source_row_number']: item for item in file_results}
    assert indexed[first.source_row_number]['match_status'] == 'matched'
    assert indexed[first.source_row_number]['employee_id'] == 'H1001'
    assert get_response.status_code == 200
    assert get_response.json()['data']['matched_count'] >= 1


def test_build_missing_housing_warning_contexts_flags_outlier_when_company_has_uploaded_housing_data() -> None:
    social_source = SimpleNamespace(source_kind='social_security', region='shenzhen', company_name='零一运营')
    housing_source = SimpleNamespace(source_kind='housing_fund', region='shenzhen', company_name='零一运营')

    def social_record(*, record_id: str, row_number: int, person_name: str, id_number: str, has_housing: bool):
        return SimpleNamespace(
            id=record_id,
            source_file=social_source,
            source_file_id='social-file',
            source_row_number=row_number,
            person_name=person_name,
            id_number=id_number,
            housing_fund_personal=Decimal('175') if has_housing else None,
            housing_fund_company=Decimal('175') if has_housing else None,
            housing_fund_total=Decimal('350') if has_housing else None,
            raw_payload={'merged_sources': [{'source_kind': 'housing_fund'}]} if has_housing else {'merged_sources': []},
        )

    records = [
        social_record(record_id='r1', row_number=1, person_name='甲', id_number='440101199001010011', has_housing=True),
        social_record(record_id='r2', row_number=2, person_name='乙', id_number='440101199001010022', has_housing=True),
        social_record(record_id='r3', row_number=3, person_name='丙', id_number='440101199001010033', has_housing=True),
        social_record(record_id='r4', row_number=4, person_name='丁', id_number='440101199001010044', has_housing=False),
        SimpleNamespace(
            id='housing-row',
            source_file=housing_source,
            source_file_id='housing-file',
            source_row_number=1,
            person_name='甲',
            id_number='440101199001010011',
            housing_fund_personal=Decimal('175'),
            housing_fund_company=Decimal('175'),
            housing_fund_total=Decimal('350'),
            raw_payload={'merged_sources': [{'source_kind': 'housing_fund'}]},
        ),
    ]

    warnings = _build_missing_housing_warning_contexts(records)

    assert len(warnings) == 1
    assert warnings[0].normalized_record_id == 'r4'
    assert warnings[0].issue.issue_type == 'missing_housing_match'
    assert warnings[0].issue.severity == 'warning'



def test_match_batch_endpoint_returns_matched_duplicate_and_unmatched_results() -> None:
    client, _settings, session_factory = build_test_context('match_results')
    guangzhou = find_sample(GUANGZHOU_KEYWORD)
    standardized = standardize_workbook(guangzhou, region='guangzhou', company_name=GUANGZHOU_COMPANY)
    assert len(standardized.records) >= 3
    first, second, third = standardized.records[:3]

    seed_employees(
        session_factory,
        [
            EmployeeMaster(
                employee_id='E1001',
                person_name=first.values['person_name'],
                id_number=first.values['id_number'],
                company_name=OTHER_COMPANY,
                active=True,
            ),
            EmployeeMaster(
                employee_id='E2001',
                person_name=second.values['person_name'],
                id_number=second.values['id_number'],
                company_name=GUANGZHOU_COMPANY,
                active=True,
            ),
            EmployeeMaster(
                employee_id='E2002',
                person_name=second.values['person_name'],
                id_number=second.values['id_number'],
                company_name=GUANGZHOU_COMPANY,
                active=True,
            ),
        ],
    )

    with client:
        batch_id = create_batch(client, [(guangzhou, 'guangzhou', GUANGZHOU_COMPANY)], batch_name='match-batch')
        match_response = client.post(f'/api/v1/imports/{batch_id}/match')
        get_response = client.get(f'/api/v1/imports/{batch_id}/match')
        detail_response = client.get(f'/api/v1/imports/{batch_id}')

    assert match_response.status_code == 200
    payload = match_response.json()['data']
    assert payload['status'] == 'matched'
    assert payload['employee_master_available'] is True
    assert payload['employee_master_count'] == 3
    assert payload['matched_count'] >= 1
    assert payload['duplicate_count'] >= 1
    assert payload['unmatched_count'] >= 1

    file_results = payload['source_files'][0]['results']
    indexed = {item['source_row_number']: item for item in file_results}
    assert indexed[first.source_row_number]['match_status'] == 'matched'
    assert indexed[first.source_row_number]['employee_id'] == 'E1001'
    assert indexed[second.source_row_number]['match_status'] == 'duplicate'
    assert indexed[second.source_row_number]['candidate_employee_ids'] == ['E2001', 'E2002']
    assert indexed[third.source_row_number]['match_status'] == 'unmatched'

    assert get_response.status_code == 200
    get_payload = get_response.json()['data']
    assert get_payload['matched_count'] == payload['matched_count']
    assert get_payload['duplicate_count'] == payload['duplicate_count']
    assert get_payload['unmatched_count'] == payload['unmatched_count']
    assert detail_response.json()['data']['status'] == 'matched'


@pytest.mark.parametrize(
    ('method', 'path', 'name'),
    [
        ('post', '/api/v1/imports/missing-batch/validate', 'missing_validate_post'),
        ('get', '/api/v1/imports/missing-batch/validation', 'missing_validation_get'),
        ('post', '/api/v1/imports/missing-batch/match', 'missing_match_post'),
        ('get', '/api/v1/imports/missing-batch/match', 'missing_match_get'),
    ],
)
def test_validation_and_match_endpoints_return_not_found_for_unknown_batch(method: str, path: str, name: str) -> None:
    client, _settings, _session_factory = build_test_context(name)

    with client:
        response = getattr(client, method)(path)

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'not_found'
