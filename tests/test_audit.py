"""Tests for audit log model, service, and API endpoint."""

import json

import pytest
from backend.app.models.audit_log import AuditLog
from backend.app.services.audit_service import log_audit


class TestLogAuditService:
    """Unit tests for the log_audit helper function."""

    def test_log_audit_writes_to_db(self, db_session):
        log_audit(
            db_session,
            action="login",
            actor_username="admin",
            actor_role="admin",
            ip_address="127.0.0.1",
            success=True,
        )
        rows = db_session.query(AuditLog).all()
        assert len(rows) == 1
        assert rows[0].action == "login"
        assert rows[0].actor_username == "admin"
        assert rows[0].actor_role == "admin"
        assert rows[0].ip_address == "127.0.0.1"
        assert rows[0].success is True

    def test_log_audit_detail_json(self, db_session):
        log_audit(
            db_session,
            action="export",
            actor_username="hr_user",
            actor_role="hr",
            detail={"export_type": "salary", "record_count": 42},
            success=True,
        )
        row = db_session.query(AuditLog).first()
        parsed = json.loads(row.detail)
        assert parsed["export_type"] == "salary"
        assert parsed["record_count"] == 42

    def test_log_audit_detail_none(self, db_session):
        log_audit(
            db_session,
            action="login",
            actor_username="admin",
            actor_role="admin",
            success=True,
        )
        row = db_session.query(AuditLog).first()
        assert row.detail is None

    def test_log_audit_resource_fields(self, db_session):
        log_audit(
            db_session,
            action="user_create",
            actor_username="admin",
            actor_role="admin",
            resource_type="user",
            resource_id="new_user",
            success=True,
        )
        row = db_session.query(AuditLog).first()
        assert row.resource_type == "user"
        assert row.resource_id == "new_user"


class TestAuditLogModel:
    """Tests for AuditLog ORM model constraints."""

    def test_audit_log_no_updated_at(self):
        """AuditLog must not have updated_at (per D-08: append-only)."""
        assert not hasattr(AuditLog, "updated_at")

    def test_audit_log_has_created_at(self):
        assert hasattr(AuditLog, "created_at")

    def test_audit_log_tablename(self):
        assert AuditLog.__tablename__ == "audit_logs"


class TestAuditLogAPI:
    """Tests for the audit log query endpoint."""

    def _get_admin_token(self, client, seed_test_admin):
        resp = client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "testpass123"
        })
        return resp.json()["data"]["access_token"]

    def _get_hr_token(self, client, seed_test_hr):
        resp = client.post("/api/v1/auth/login", json={
            "username": "testhr", "password": "hrpass123"
        })
        return resp.json()["data"]["access_token"]

    def test_list_audit_logs(self, test_client, db_session, seed_test_admin):
        # Seed some audit data
        log_audit(db_session, action="login", actor_username="admin",
                  actor_role="admin", success=True)
        log_audit(db_session, action="export", actor_username="admin",
                  actor_role="admin", success=True)

        token = self._get_admin_token(test_client, seed_test_admin)
        resp = test_client.get("/api/v1/audit-logs", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        # At least the 2 seeded + login audit from token generation
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_list_audit_logs_filter_action(self, test_client, db_session, seed_test_admin):
        log_audit(db_session, action="login", actor_username="admin",
                  actor_role="admin", success=True)
        log_audit(db_session, action="export", actor_username="admin",
                  actor_role="admin", success=True)

        token = self._get_admin_token(test_client, seed_test_admin)
        resp = test_client.get("/api/v1/audit-logs?action=export", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        for item in data["items"]:
            assert item["action"] == "export"

    def test_list_audit_logs_admin_only(self, test_client, db_session, seed_test_admin, seed_test_hr):
        token = self._get_hr_token(test_client, seed_test_hr)
        resp = test_client.get("/api/v1/audit-logs", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 403

    def test_list_audit_logs_unauthenticated(self, test_client):
        resp = test_client.get("/api/v1/audit-logs")
        assert resp.status_code == 401

    def test_audit_no_delete_endpoint(self, test_client, seed_test_admin):
        token = self._get_admin_token(test_client, seed_test_admin)
        resp = test_client.delete("/api/v1/audit-logs", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 405

    def test_audit_no_put_endpoint(self, test_client, seed_test_admin):
        token = self._get_admin_token(test_client, seed_test_admin)
        resp = test_client.put("/api/v1/audit-logs", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 405
