"""Tests for data management API endpoints (DATA-01, DATA-02)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from backend.app.core.auth import issue_access_token
from backend.app.models.import_batch import ImportBatch
from backend.app.models.normalized_record import NormalizedRecord
from backend.app.models.enums import BatchStatus

from tests.conftest import TEST_SECRET_KEY


def _create_batch(db: Session, name: str = "test-batch") -> ImportBatch:
    batch = ImportBatch(batch_name=name, status=BatchStatus.UPLOADED)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def _create_record(
    db: Session,
    batch: ImportBatch,
    *,
    person_name: str = "Zhang San",
    id_number: str = "110101199001011234",
    employee_id: str = "EMP001",
    company_name: str = "CompanyA",
    region: str = "shenzhen",
    billing_period: str = "202602",
    payment_base: float = 5000.0,
    total_amount: float = 1000.0,
    company_total_amount: float = 700.0,
    personal_total_amount: float = 300.0,
) -> NormalizedRecord:
    record = NormalizedRecord(
        batch_id=batch.id,
        source_file_id=str(uuid.uuid4()),
        source_row_number=1,
        person_name=person_name,
        id_number=id_number,
        employee_id=employee_id,
        company_name=company_name,
        region=region,
        billing_period=billing_period,
        payment_base=payment_base,
        total_amount=total_amount,
        company_total_amount=company_total_amount,
        personal_total_amount=personal_total_amount,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _get_hr_token(client, seed_test_hr):
    resp = client.post("/api/v1/auth/login", json={"username": "testhr", "password": "hrpass123"})
    return resp.json()["data"]["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestFilterRecords:
    def test_filter_records_by_region(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, region="shenzhen", person_name="A")
        _create_record(db_session, batch, region="shenzhen", person_name="B", id_number="222")
        _create_record(db_session, batch, region="guangzhou", person_name="C", id_number="333")

        resp = test_client.get(
            "/api/v1/data-management/records?region=shenzhen",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 0
        assert data["page_size"] == 20
        for item in data["items"]:
            assert item["region"] == "shenzhen"


class TestFilterOptions:
    def test_filter_options_regions(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, region="shenzhen", person_name="A")
        _create_record(db_session, batch, region="guangzhou", person_name="B", id_number="222")

        resp = test_client.get(
            "/api/v1/data-management/filter-options",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "shenzhen" in data["regions"]
        assert "guangzhou" in data["regions"]

    def test_filter_options_cascading_companies(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, region="shenzhen", company_name="SZ-Co", person_name="A")
        _create_record(db_session, batch, region="guangzhou", company_name="GZ-Co", person_name="B", id_number="222")

        resp = test_client.get(
            "/api/v1/data-management/filter-options?region=shenzhen",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "SZ-Co" in data["companies"]
        assert "GZ-Co" not in data["companies"]

    def test_filter_options_cascading_periods(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, region="shenzhen", company_name="CompanyA", billing_period="202601", person_name="A")
        _create_record(db_session, batch, region="shenzhen", company_name="CompanyA", billing_period="202602", person_name="B", id_number="222")
        _create_record(db_session, batch, region="shenzhen", company_name="CompanyB", billing_period="202603", person_name="C", id_number="333")

        resp = test_client.get(
            "/api/v1/data-management/filter-options?region=shenzhen&company_name=CompanyA",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert set(data["periods"]) == {"202601", "202602"}
        assert "202603" not in data["periods"]


class TestEmployeeSummary:
    def test_employee_summary(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, person_name="A", employee_id="E1", company_total_amount=700, personal_total_amount=300, total_amount=1000)
        _create_record(db_session, batch, person_name="A", employee_id="E1", company_total_amount=800, personal_total_amount=200, total_amount=1000, billing_period="202603", id_number="222")

        resp = test_client.get(
            "/api/v1/data-management/summary/employees",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1
        # Find the E1 summary
        e1 = next((i for i in data["items"] if i["employee_id"] == "E1"), None)
        assert e1 is not None
        assert e1["company_total"] == 1500.0
        assert e1["personal_total"] == 500.0
        assert e1["total"] == 2000.0


class TestPeriodSummary:
    def test_period_summary(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        _create_record(db_session, batch, billing_period="202602", person_name="A")
        _create_record(db_session, batch, billing_period="202601", person_name="B", id_number="222")
        _create_record(db_session, batch, billing_period="202602", person_name="C", id_number="333")

        resp = test_client.get(
            "/api/v1/data-management/summary/periods",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        # Should be sorted DESC
        assert data["items"][0]["billing_period"] == "202602"
        assert data["items"][0]["total_count"] == 2
        assert data["items"][1]["billing_period"] == "202601"
        assert data["items"][1]["total_count"] == 1


class TestPagination:
    def test_records_pagination(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        for i in range(25):
            _create_record(
                db_session, batch,
                person_name=f"Person{i:03d}",
                id_number=f"ID{i:03d}",
                employee_id=f"E{i:03d}",
            )

        resp = test_client.get(
            "/api/v1/data-management/records?page_size=10",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 10
        assert data["total"] == 25

    def test_records_deterministic_sort(self, test_client, db_session, seed_test_hr):
        token = _get_hr_token(test_client, seed_test_hr)
        batch = _create_batch(db_session)
        for i in range(15):
            _create_record(
                db_session, batch,
                person_name=f"Person{i:03d}",
                id_number=f"ID{i:03d}",
                employee_id=f"E{i:03d}",
            )

        resp0 = test_client.get(
            "/api/v1/data-management/records?page=0&page_size=10",
            headers=_auth_headers(token),
        )
        resp1 = test_client.get(
            "/api/v1/data-management/records?page=1&page_size=10",
            headers=_auth_headers(token),
        )
        ids_page0 = {item["id"] for item in resp0.json()["data"]["items"]}
        ids_page1 = {item["id"] for item in resp1.json()["data"]["items"]}
        assert len(ids_page0 & ids_page1) == 0, "Pages should not overlap"
