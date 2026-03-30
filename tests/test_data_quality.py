"""Tests for data quality API endpoint (DATA-03)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from backend.app.models.import_batch import ImportBatch
from backend.app.models.normalized_record import NormalizedRecord
from backend.app.models.enums import BatchStatus

from tests.conftest import TEST_SECRET_KEY


def _create_batch(db: Session, name: str = "quality-batch") -> ImportBatch:
    batch = ImportBatch(batch_name=name, status=BatchStatus.UPLOADED)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def _create_record(db: Session, batch: ImportBatch, **kwargs) -> NormalizedRecord:
    defaults = dict(
        batch_id=batch.id,
        source_file_id=str(uuid.uuid4()),
        source_row_number=1,
        person_name="Zhang San",
        id_number="110101199001011234",
        employee_id="EMP001",
        company_name="TestCo",
        region="shenzhen",
        billing_period="202602",
        payment_base=5000.0,
        total_amount=1000.0,
        company_total_amount=700.0,
        personal_total_amount=300.0,
    )
    defaults.update(kwargs)
    record = NormalizedRecord(**defaults)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _get_hr_token(client, seed_test_hr):
    resp = client.post("/api/v1/auth/login", json={"username": "testhr", "password": "hrpass123"})
    return resp.json()["data"]["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestMissingFields:
    def test_missing_fields(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        # Record with missing person_name
        _create_record(db_session, batch, person_name=None, id_number="111", employee_id="E1")
        # Record with missing id_number
        _create_record(db_session, batch, person_name="B", id_number=None, employee_id="E2")
        # Complete record
        _create_record(db_session, batch, person_name="C", id_number="333", employee_id="E3")

        resp = test_client.get("/api/v1/dashboard/quality", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_missing"] == 2


class TestAnomalousAmounts:
    def test_anomalous_amounts_low(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, payment_base=50, id_number="111")  # Below 100 threshold
        _create_record(db_session, batch, payment_base=5000, id_number="222")  # Normal

        resp = test_client.get("/api/v1/dashboard/quality", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_anomalous"] == 1

    def test_anomalous_amounts_high(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, payment_base=90000, id_number="111")  # Above 80000 threshold
        _create_record(db_session, batch, payment_base=5000, id_number="222")  # Normal

        resp = test_client.get("/api/v1/dashboard/quality", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_anomalous"] == 1


class TestDuplicateRecords:
    def test_duplicate_records_by_id_number(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        # Same id_number + billing_period = duplicate
        _create_record(db_session, batch, id_number="330101199001011234", billing_period="202602", person_name="A")
        _create_record(db_session, batch, id_number="330101199001011234", billing_period="202602", person_name="A2")

        resp = test_client.get("/api/v1/dashboard/quality", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_duplicates"] > 0

    def test_duplicate_records_fallback_person_name(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        # No id_number, same person_name + company_name + billing_period = fallback duplicate
        _create_record(db_session, batch, id_number=None, person_name="Zhang San", company_name="Co1", billing_period="202602")
        _create_record(db_session, batch, id_number=None, person_name="Zhang San", company_name="Co1", billing_period="202602")

        resp = test_client.get("/api/v1/dashboard/quality", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_duplicates"] > 0

    def test_no_false_positive_same_name_different_id(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        # Same person_name but DIFFERENT id_number => NOT duplicates
        _create_record(db_session, batch, id_number="AAA111", person_name="Li Si", billing_period="202602")
        _create_record(db_session, batch, id_number="BBB222", person_name="Li Si", billing_period="202602")

        resp = test_client.get("/api/v1/dashboard/quality", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_duplicates"] == 0

    def test_no_quality_issues(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, person_name="A", id_number="111", employee_id="E1", payment_base=5000, billing_period="202601")
        _create_record(db_session, batch, person_name="B", id_number="222", employee_id="E2", payment_base=6000, billing_period="202602")

        resp = test_client.get("/api/v1/dashboard/quality", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_missing"] == 0
        assert data["total_anomalous"] == 0
        assert data["total_duplicates"] == 0
