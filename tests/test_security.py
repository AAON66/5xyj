"""Comprehensive security tests for Phase 3: SEC-01/02/03/04."""

from __future__ import annotations

import json

import pytest
from backend.app.models.audit_log import AuditLog
from backend.app.services.audit_service import log_audit


# ---------------------------------------------------------------------------
# SEC-02: Login rate limiting
# ---------------------------------------------------------------------------

class TestLoginRateLimiting:
    """Login endpoint rate limiting (per D-04)."""

    @pytest.fixture(autouse=True)
    def _reset_login_limiter(self):
        """Reset the module-level login rate limiter between tests."""
        from backend.app.api.v1.auth import _login_rate_limiter
        _login_rate_limiter._records.clear()
        yield
        _login_rate_limiter._records.clear()

    def test_login_rate_limit_blocks_after_5_failures(self, test_client, db_session, seed_test_admin):
        """5 consecutive wrong-password attempts lock the username for 15 min."""
        for _ in range(5):
            resp = test_client.post("/api/v1/auth/login", json={
                "username": "testadmin", "password": "wrongpass"
            })
            assert resp.status_code == 401

        # 6th attempt should be rate-limited
        resp = test_client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "wrongpass"
        })
        assert resp.status_code == 429

    def test_login_rate_limit_resets_on_success(self, test_client, db_session, seed_test_admin):
        """Successful login resets the failure counter."""
        # 4 failures
        for _ in range(4):
            test_client.post("/api/v1/auth/login", json={
                "username": "testadmin", "password": "wrongpass"
            })

        # 1 success
        resp = test_client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "testpass123"
        })
        assert resp.status_code == 200

        # 1 more failure should NOT trigger lockout (counter was reset)
        resp = test_client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "wrongpass"
        })
        assert resp.status_code == 401  # not 429

    def test_login_rate_limit_key_is_username(self, test_client, db_session, seed_test_admin, seed_test_hr):
        """Different usernames have independent failure counters."""
        # 5 failures for testadmin
        for _ in range(5):
            test_client.post("/api/v1/auth/login", json={
                "username": "testadmin", "password": "wrongpass"
            })

        # testhr should NOT be locked
        resp = test_client.post("/api/v1/auth/login", json={
            "username": "testhr", "password": "hrpass123"
        })
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# SEC-03: Audit logging
# ---------------------------------------------------------------------------

class TestAuditLogging:
    """Audit log creation for key operations."""

    def test_login_success_creates_audit_log(self, test_client, db_session, seed_test_admin):
        test_client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "testpass123"
        })
        logs = db_session.query(AuditLog).filter(AuditLog.action == "login").all()
        assert len(logs) >= 1
        assert logs[0].actor_username == "testadmin"
        assert logs[0].success is True

    def test_login_failed_creates_audit_log(self, test_client, db_session, seed_test_admin):
        test_client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "wrongpass"
        })
        logs = db_session.query(AuditLog).filter(AuditLog.action == "login_failed").all()
        assert len(logs) >= 1
        assert logs[0].actor_username == "testadmin"
        assert logs[0].success is False

    def test_login_failed_audit_no_password(self, test_client, db_session, seed_test_admin):
        """Audit log detail for failed login must NOT contain password (review concern #3)."""
        test_client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "my-secret-pass"
        })
        log = db_session.query(AuditLog).filter(AuditLog.action == "login_failed").first()
        assert log is not None
        assert "my-secret-pass" not in (log.detail or "")
        assert "password" not in (log.detail or "").lower() or "password" not in json.loads(log.detail or "{}")

    def test_employee_verify_failed_audit_no_id_number(
        self, test_client, db_session, seed_test_employee
    ):
        """Audit log detail for failed employee verify must NOT contain full ID number."""
        test_client.post("/api/v1/auth/employee-verify", json={
            "employee_id": "EMP001",
            "id_number": "999999999999999999",
            "person_name": "Wrong Name",
        })
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "employee_verify_failed"
        ).first()
        assert log is not None
        # Full ID number should not appear in detail
        assert "999999999999999999" not in (log.detail or "")


# ---------------------------------------------------------------------------
# SEC-01: Endpoint authentication
# ---------------------------------------------------------------------------

class TestEndpointAuthentication:
    """PII endpoints require authentication."""

    @pytest.mark.parametrize("path", [
        "/api/v1/employees",
        "/api/v1/audit-logs",
        "/api/v1/users/",
    ])
    def test_pii_endpoints_require_auth(self, test_client, path):
        """Unauthenticated requests to PII endpoints return 401."""
        resp = test_client.get(path)
        assert resp.status_code in (401, 403), f"{path} returned {resp.status_code}"


# ---------------------------------------------------------------------------
# auth_enabled=false dev mode (per D-02)
# ---------------------------------------------------------------------------

class TestAuthDisabledMode:
    """When auth_enabled=False, security features don't block normal flow."""

    def test_auth_disabled_pii_endpoints_accessible(self, test_client_auth_disabled):
        """With auth disabled, PII endpoints are accessible without token."""
        resp = test_client_auth_disabled.get("/api/v1/employees")
        assert resp.status_code == 200

    def test_auth_disabled_audit_log_still_records(self, test_client_auth_disabled, db_session):
        """Audit logging still works with auth disabled."""
        log_audit(db_session, action="test_action", actor_username="local-dev",
                  actor_role="admin", success=True)
        logs = db_session.query(AuditLog).filter(AuditLog.action == "test_action").all()
        assert len(logs) == 1

    def test_auth_disabled_rate_limiter_still_works(self, test_client_auth_disabled, db_session):
        """Rate limiter works even with auth disabled."""
        from backend.app.services.rate_limiter import RateLimiter
        rl = RateLimiter(max_failures=3, lockout_seconds=60)
        for _ in range(3):
            rl.record_failure("test-key")
        assert rl.is_locked("test-key")


# ---------------------------------------------------------------------------
# SEC-04: ID number masking
# ---------------------------------------------------------------------------

class TestIdNumberMasking:
    """Role-based ID number masking in API responses."""

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

    def test_admin_role_sees_full_id(self, test_client, db_session, seed_test_admin, seed_test_employee):
        token = self._get_admin_token(test_client, seed_test_admin)
        resp = test_client.get("/api/v1/employees", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) > 0
        # Admin sees full id_number
        assert items[0]["id_number"] == "110101199001011234"

    def test_hr_role_sees_full_id(self, test_client, db_session, seed_test_hr, seed_test_employee):
        token = self._get_hr_token(test_client, seed_test_hr)
        resp = test_client.get("/api/v1/employees", headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) > 0
        # HR sees full id_number
        assert items[0]["id_number"] == "110101199001011234"


# ---------------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------------

class TestCorsConfiguration:
    """CORS no longer hardcodes wildcard origin."""

    def test_cors_uses_settings_not_wildcard(self):
        """Verify main.py uses runtime_settings.backend_cors_origins."""
        import inspect
        from backend.app.main import create_app
        source = inspect.getsource(create_app)
        assert "runtime_settings.backend_cors_origins" in source
        assert 'allow_origins=["*"]' not in source
