"""Tests for ImportBatch.created_by injection (DATA-04)."""

from __future__ import annotations

import io

import pytest
from sqlalchemy.orm import Session

from backend.app.models.import_batch import ImportBatch
from backend.app.models.enums import BatchStatus

from tests.conftest import TEST_SECRET_KEY


def _get_hr_token(client, seed_test_hr):
    resp = client.post("/api/v1/auth/login", json={"username": "testhr", "password": "hrpass123"})
    return resp.json()["data"]["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_minimal_xlsx() -> bytes:
    """Create a minimal valid xlsx file for upload."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["name", "value"])
    ws.append(["test", 123])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestCreatedBy:
    def test_created_by_populated(self, test_client, db_session, seed_test_hr):
        """Import batch created via API should have created_by set to User.id."""
        token = _get_hr_token(test_client, seed_test_hr)
        xlsx_bytes = _create_minimal_xlsx()

        resp = test_client.post(
            "/api/v1/imports",
            headers=_auth_headers(token),
            files=[("files", ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))],
            data={"batch_name": "created-by-test"},
        )
        assert resp.status_code == 201

        batch_id = resp.json()["data"]["id"]
        batch = db_session.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        assert batch is not None
        assert batch.created_by == seed_test_hr.id

    def test_legacy_null(self, db_session):
        """Legacy ImportBatch records (inserted directly) should have null created_by."""
        batch = ImportBatch(batch_name="legacy-batch", status=BatchStatus.UPLOADED)
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)
        assert batch.created_by is None

    def test_list_batches_shows_operator(self, test_client, db_session, seed_test_hr):
        """List endpoint should include created_by_name for batches with creator."""
        token = _get_hr_token(test_client, seed_test_hr)
        xlsx_bytes = _create_minimal_xlsx()

        # Create a batch via API
        create_resp = test_client.post(
            "/api/v1/imports",
            headers=_auth_headers(token),
            files=[("files", ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))],
            data={"batch_name": "operator-test"},
        )
        assert create_resp.status_code == 201

        # List batches
        list_resp = test_client.get("/api/v1/imports", headers=_auth_headers(token))
        assert list_resp.status_code == 200
        batches = list_resp.json()["data"]
        # Find our batch
        our_batch = next((b for b in batches if b["batch_name"] == "operator-test"), None)
        assert our_batch is not None
        assert our_batch["created_by_name"] == "Test HR"
