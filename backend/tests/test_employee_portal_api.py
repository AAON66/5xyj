"""Tests for the employee portal API (token-bound self-service endpoint).

Covers PORTAL-01 through PORTAL-05:
- Insurance breakdown fields in response
- Housing fund fields in response
- Multi-period ordering (billing_period DESC)
- Data isolation (employee A cannot see employee B's data)
- Auth enforcement (401 without token)
- Regression: old POST /self-service/query still works
"""
from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.auth import issue_access_token
from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.models import Base, EmployeeMaster, ImportBatch, NormalizedRecord
from backend.app.models.enums import BatchStatus


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'employee_portal_api'
TEST_SECRET = 'test-portal-secret-key-minimum-32-bytes!'


def build_test_context(test_name: str, *, auth_enabled: bool = True):
    """Create isolated test context with auth enabled by default."""
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'portal.db'
    settings = Settings(
        app_name='portal-test',
        app_version='0.2.0',
        auth_enabled=auth_enabled,
        auth_secret_key=TEST_SECRET,
        employee_token_expire_minutes=30,
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


def issue_employee_token(employee_id: str) -> str:
    """Issue a JWT token for the given employee_id with role=employee."""
    token, _exp = issue_access_token(TEST_SECRET, sub=employee_id, role='employee', expire_minutes=30)
    return token


def seed_employee_and_records(
    session_factory,
    *,
    employee_id: str,
    person_name: str,
    id_number: str,
    billing_periods: list[str] | None = None,
):
    """Create an EmployeeMaster + ImportBatch + NormalizedRecords for testing."""
    if billing_periods is None:
        billing_periods = ['202602', '202601']

    db: Session = session_factory()
    try:
        # Create employee master
        employee = EmployeeMaster(
            employee_id=employee_id,
            person_name=person_name,
            id_number=id_number,
            company_name='test-company',
            department='test-dept',
            active=True,
        )
        db.add(employee)
        db.flush()

        # Create import batch
        batch = ImportBatch(
            batch_name='portal-test-batch',
            status=BatchStatus.MATCHED,
        )
        db.add(batch)
        db.flush()

        record_ids = []
        for period in billing_periods:
            record = NormalizedRecord(
                batch_id=batch.id,
                source_file_id=_make_fake_source_file_id(db, batch.id),
                source_row_number=10,
                person_name=person_name,
                id_number=id_number,
                employee_id=employee_id,
                company_name='test-company',
                region='shenzhen',
                billing_period=period,
                period_start=f'{period}01',
                period_end=f'{period}28',
                source_file_name='test.xlsx',
                total_amount=Decimal('1000.00'),
                company_total_amount=Decimal('700.00'),
                personal_total_amount=Decimal('300.00'),
                housing_fund_personal=Decimal('120.00'),
                housing_fund_company=Decimal('120.00'),
                housing_fund_total=Decimal('240.00'),
                payment_base=Decimal('8000.00'),
                pension_company=Decimal('320.00'),
                pension_personal=Decimal('160.00'),
                medical_company=Decimal('80.00'),
                medical_personal=Decimal('40.00'),
                unemployment_company=Decimal('16.00'),
                unemployment_personal=Decimal('8.00'),
                injury_company=Decimal('4.00'),
                maternity_amount=Decimal('0.00'),
            )
            db.add(record)
            db.flush()
            record_ids.append(record.id)

        db.commit()
        return employee.id, batch.id, record_ids
    finally:
        db.close()


def _make_fake_source_file_id(db: Session, batch_id: str) -> str:
    """Create a minimal SourceFile row and return its id."""
    from backend.app.models.source_file import SourceFile
    sf = SourceFile(
        batch_id=batch_id,
        file_name='test.xlsx',
        file_path='/fake/path',
        file_size=1024,
        region='shenzhen',
        company_name='test-company',
    )
    db.add(sf)
    db.flush()
    return sf.id


# ---------------------------------------------------------------------------
# Test 1 (PORTAL-01/05): Insurance breakdown fields
# ---------------------------------------------------------------------------

def test_portal_returns_insurance_breakdown() -> None:
    client, _settings, session_factory = build_test_context('insurance_breakdown')
    token = issue_employee_token('EMP001')
    seed_employee_and_records(
        session_factory,
        employee_id='EMP001',
        person_name='portal-user',
        id_number='440101199001010011',
        billing_periods=['202602'],
    )

    with client:
        response = client.get(
            '/api/v1/employees/self-service/my-records',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 200
    data = response.json()['data']
    assert data['record_count'] >= 1
    record = data['records'][0]
    # Verify insurance breakdown fields exist and have correct values
    assert record['pension_company'] == '320.00'
    assert record['pension_personal'] == '160.00'
    assert record['medical_company'] == '80.00'
    assert record['medical_personal'] == '40.00'
    assert record['unemployment_company'] == '16.00'
    assert record['unemployment_personal'] == '8.00'
    assert record['injury_company'] == '4.00'
    assert record['maternity_amount'] == '0.00'
    assert record['payment_base'] == '8000.00'


# ---------------------------------------------------------------------------
# Test 2 (PORTAL-02): Housing fund fields
# ---------------------------------------------------------------------------

def test_portal_returns_housing_fund() -> None:
    client, _settings, session_factory = build_test_context('housing_fund')
    token = issue_employee_token('EMP002')
    seed_employee_and_records(
        session_factory,
        employee_id='EMP002',
        person_name='hf-user',
        id_number='440101199202020022',
        billing_periods=['202602'],
    )

    with client:
        response = client.get(
            '/api/v1/employees/self-service/my-records',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 200
    record = response.json()['data']['records'][0]
    assert record['housing_fund_personal'] == '120.00'
    assert record['housing_fund_company'] == '120.00'
    assert record['housing_fund_total'] == '240.00'


# ---------------------------------------------------------------------------
# Test 3 (PORTAL-03): Multi-period ordering
# ---------------------------------------------------------------------------

def test_portal_returns_multiple_periods() -> None:
    client, _settings, session_factory = build_test_context('multi_period')
    token = issue_employee_token('EMP003')
    seed_employee_and_records(
        session_factory,
        employee_id='EMP003',
        person_name='mp-user',
        id_number='440101199303030033',
        billing_periods=['202602', '202601'],
    )

    with client:
        response = client.get(
            '/api/v1/employees/self-service/my-records',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 200
    data = response.json()['data']
    assert data['record_count'] == 2
    # billing_period should be in descending order (newest first)
    assert data['records'][0]['billing_period'] >= data['records'][1]['billing_period']


# ---------------------------------------------------------------------------
# Test 4 (PORTAL-04 / D-12): Data isolation
# ---------------------------------------------------------------------------

def test_employee_cannot_access_others() -> None:
    client, _settings, session_factory = build_test_context('data_isolation')
    # Seed employee A
    seed_employee_and_records(
        session_factory,
        employee_id='EMP_A',
        person_name='employee-a',
        id_number='440101199001010011',
        billing_periods=['202602'],
    )
    # Seed employee B
    _, _, b_record_ids = seed_employee_and_records(
        session_factory,
        employee_id='EMP_B',
        person_name='employee-b',
        id_number='440101199202020022',
        billing_periods=['202602'],
    )

    token_a = issue_employee_token('EMP_A')

    with client:
        response = client.get(
            '/api/v1/employees/self-service/my-records',
            headers={'Authorization': f'Bearer {token_a}'},
        )

    assert response.status_code == 200
    data = response.json()['data']
    # All returned records must belong to employee A
    for record in data['records']:
        assert record['employee_id'] == 'EMP_A'
    # None of B's record IDs should appear
    returned_ids = {r['normalized_record_id'] for r in data['records']}
    for b_id in b_record_ids:
        assert b_id not in returned_ids


# ---------------------------------------------------------------------------
# Test 5 (PORTAL-04): Auth required
# ---------------------------------------------------------------------------

def test_portal_requires_auth() -> None:
    client, _settings, _session_factory = build_test_context('auth_required')

    with client:
        response = client.get('/api/v1/employees/self-service/my-records')

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test 6: Old endpoint regression
# ---------------------------------------------------------------------------

def test_old_query_endpoint_still_works() -> None:
    client, _settings, _session_factory = build_test_context('old_endpoint', auth_enabled=False)

    with client:
        response = client.post(
            '/api/v1/employees/self-service/query',
            json={'person_name': 'nobody', 'id_number': '000000000000000000'},
        )

    # Should return 404 (not found), not 405 or 500
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'not_found'
