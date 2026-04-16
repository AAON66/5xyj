"""Tests for Feishu OAuth, feature flags, sync endpoints, and settings CRUD."""

from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy.orm import Session

from backend.app.models.sync_config import SyncConfig
from backend.app.models.sync_job import SyncJob
from backend.app.models.user import User
from backend.app.services.user_service import hash_password
from tests.conftest import TEST_SECRET_KEY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login_admin(client) -> str:
    """Login as admin and return bearer token."""
    resp = client.post("/api/v1/auth/login", json={"username": "testadmin", "password": "testpass123"})
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_mock_httpx_client(open_id: str = "ou_test123", name: str = "Test User"):
    """Create a mock httpx.AsyncClient that returns valid Feishu OAuth responses."""
    mock_http = AsyncMock()

    # Mock app_access_token response
    app_token_resp = MagicMock()
    app_token_resp.json.return_value = {"code": 0, "app_access_token": "mock_token", "expire": 7200}
    app_token_resp.raise_for_status = MagicMock()

    # Mock user info response
    user_resp = MagicMock()
    user_resp.json.return_value = {
        "code": 0,
        "data": {
            "open_id": open_id,
            "union_id": "un_test",
            "name": name,
            "email": "test@example.com",
        },
    }
    user_resp.raise_for_status = MagicMock()

    mock_http.post = AsyncMock(side_effect=[app_token_resp, user_resp])

    return mock_http


# ---------------------------------------------------------------------------
# Feature Flag Tests
# ---------------------------------------------------------------------------

class TestFeatureFlags:
    def test_feature_flags_endpoint_returns_flags(self, test_client_feishu):
        resp = test_client_feishu.get("/api/v1/system/features")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["feishu_sync_enabled"] is True
        assert data["feishu_oauth_enabled"] is True
        assert data["feishu_credentials_configured"] is True

    def test_feature_flags_disabled_by_default(self, test_client):
        resp = test_client.get("/api/v1/system/features")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["feishu_sync_enabled"] is False

    def test_sync_endpoints_return_404_when_disabled(self, test_client, seed_test_admin):
        token = _login_admin(test_client)
        resp = test_client.post(
            "/api/v1/feishu/sync/push",
            json={"config_id": "fake"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "FEATURE_DISABLED"

    def test_settings_endpoints_return_404_when_disabled(self, test_client, seed_test_admin):
        token = _login_admin(test_client)
        resp = test_client.get(
            "/api/v1/feishu/settings/configs",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "FEATURE_DISABLED"

    def test_oauth_callback_returns_404_when_disabled(self, test_client):
        resp = test_client.post(
            "/api/v1/auth/feishu/callback",
            json={"code": "test", "state": "test"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# OAuth State Validation Tests (H2)
# ---------------------------------------------------------------------------

class TestOAuthStateValidation:
    def test_oauth_authorize_url_sets_state_cookie(self, test_client_feishu):
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["url"].startswith("https://accounts.feishu.cn/")
        # Check cookie is set
        assert "feishu_oauth_state" in test_client_feishu.cookies

    def test_oauth_callback_rejects_invalid_state(self, test_client_feishu):
        # No cookie set -- should reject
        resp = test_client_feishu.post(
            "/api/v1/auth/feishu/callback",
            json={"code": "mock", "state": "wrong_state"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_STATE"

    def test_oauth_callback_rejects_mismatched_state(self, test_client_feishu):
        # Get valid cookie
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        assert resp.status_code == 200
        # POST with a DIFFERENT state than what was in the URL
        resp2 = test_client_feishu.post(
            "/api/v1/auth/feishu/callback",
            json={"code": "mock", "state": "totally_different_state"},
        )
        assert resp2.status_code == 400
        assert resp2.json()["error"]["code"] == "INVALID_STATE"

    def test_oauth_callback_validates_state(self, test_client_feishu, db_session):
        # Step 1: Get authorize URL and extract state
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        assert resp.status_code == 200
        url = resp.json()["data"]["url"]
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        state = qs["state"][0]

        # Step 2: Mock httpx to return valid responses
        mock_http = _make_mock_httpx_client()

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert "access_token" in data


# ---------------------------------------------------------------------------
# OAuth User Creation Tests
# ---------------------------------------------------------------------------

class TestOAuthUserCreation:
    def test_oauth_callback_creates_new_user(self, test_client_feishu, db_session):
        # Get authorize URL for valid state
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        url = resp.json()["data"]["url"]
        state = parse_qs(urlparse(url).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_new_user_123", name="New Feishu User")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data["role"] == "employee"  # new user default per D-11
            assert "access_token" in data

        # Verify user created in DB
        user = db_session.query(User).filter(User.feishu_open_id == "ou_new_user_123").first()
        assert user is not None
        assert user.role == "employee"
        assert user.display_name == "New Feishu User"

    def test_oauth_callback_existing_user(self, test_client_feishu, db_session):
        # Pre-create user with feishu binding
        existing_user = User(
            username="existing_feishu_user",
            hashed_password=hash_password("doesntmatter"),
            role="hr",
            display_name="Existing HR",
            is_active=True,
            must_change_password=False,
            feishu_open_id="ou_existing",
            feishu_union_id="un_existing",
        )
        db_session.add(existing_user)
        db_session.commit()

        # Get state
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_existing", name="Existing HR")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data["role"] == "hr"  # existing bound user keeps role


# ---------------------------------------------------------------------------
# Settings Endpoint Tests
# ---------------------------------------------------------------------------

class TestSettingsEndpoints:
    def test_sync_config_crud(self, test_client_feishu, seed_test_admin, db_session):
        token = _login_admin(test_client_feishu)
        headers = _auth_headers(token)

        # CREATE
        resp = test_client_feishu.post(
            "/api/v1/feishu/settings/configs",
            json={
                "name": "Test Config",
                "app_token": "app_tok_123",
                "table_id": "tbl_456",
                "granularity": "detail",
                "field_mapping": {},
            },
            headers=headers,
        )
        assert resp.status_code == 201
        config_data = resp.json()["data"]
        config_id = config_data["id"]
        assert config_data["name"] == "Test Config"

        # LIST
        resp = test_client_feishu.get("/api/v1/feishu/settings/configs", headers=headers)
        assert resp.status_code == 200
        configs = resp.json()["data"]
        assert len(configs) >= 1

        # UPDATE
        resp = test_client_feishu.put(
            f"/api/v1/feishu/settings/configs/{config_id}",
            json={"name": "Updated Config"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Config"

        # DELETE
        resp = test_client_feishu.delete(
            f"/api/v1/feishu/settings/configs/{config_id}",
            headers=headers,
        )
        assert resp.status_code == 204

    def test_sync_config_field_mapping_save(self, test_client_feishu, seed_test_admin, db_session):
        token = _login_admin(test_client_feishu)
        headers = _auth_headers(token)

        # Create config
        resp = test_client_feishu.post(
            "/api/v1/feishu/settings/configs",
            json={
                "name": "Mapping Test",
                "app_token": "app_tok",
                "table_id": "tbl_123",
                "granularity": "detail",
            },
            headers=headers,
        )
        config_id = resp.json()["data"]["id"]

        # Save mapping
        resp = test_client_feishu.post(
            f"/api/v1/feishu/settings/configs/{config_id}/mapping",
            json={"field_mapping": {"person_name": "姓名", "id_number": "身份证号"}},
            headers=headers,
        )
        assert resp.status_code == 200
        mapping = resp.json()["data"]["field_mapping"]
        assert mapping["person_name"] == "姓名"

    def test_credentials_endpoint_validates_only(self, test_client_feishu, seed_test_admin):
        """PUT /credentials validates but does NOT store to DB (M3)."""
        token = _login_admin(test_client_feishu)
        headers = _auth_headers(token)

        # Mock the httpx call to avoid real API call
        with patch("backend.app.api.v1.feishu_settings.httpx.AsyncClient") as MockClient:
            mock_http = AsyncMock()
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"code": 0, "tenant_access_token": "tok", "expire": 7200}
            mock_resp.raise_for_status = MagicMock()
            mock_http.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = test_client_feishu.put(
                "/api/v1/feishu/settings/credentials",
                json={"app_id": "cli_test", "app_secret": "secret_test"},
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.json()["data"]["valid"] is True

    def test_feature_flags_via_settings_endpoint(self, test_client_feishu, seed_test_admin):
        """Feature flags available via /feishu/settings/features (admin-gated)."""
        token = _login_admin(test_client_feishu)
        headers = _auth_headers(token)
        resp = test_client_feishu.get("/api/v1/feishu/settings/features", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["feishu_sync_enabled"] is True


# ---------------------------------------------------------------------------
# Sync History Pagination Tests (M5)
# ---------------------------------------------------------------------------

class TestSyncHistoryPagination:
    def test_sync_history_pagination(self, test_client_feishu, seed_test_admin, db_session):
        token = _login_admin(test_client_feishu)
        headers = _auth_headers(token)

        # Need a config first for FK
        config = SyncConfig(
            name="History Test Config",
            app_token="app_tok",
            table_id="tbl_hist",
            granularity="detail",
            field_mapping={},
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        # Create 5 sync jobs
        for i in range(5):
            job = SyncJob(
                config_id=config.id,
                direction="push",
                status="success",
                total_records=10,
                success_records=10,
                failed_records=0,
                triggered_by=f"test_{i}",
            )
            db_session.add(job)
        db_session.commit()

        # Page 1: limit=2, offset=0
        resp = test_client_feishu.get(
            "/api/v1/feishu/sync/history?limit=2&offset=0",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2

        # Page 2: limit=2, offset=2
        resp = test_client_feishu.get(
            "/api/v1/feishu/sync/history?limit=2&offset=2",
            headers=headers,
        )
        assert resp.status_code == 200
        data2 = resp.json()["data"]
        assert len(data2) == 2

        # Page 3: limit=2, offset=4
        resp = test_client_feishu.get(
            "/api/v1/feishu/sync/history?limit=2&offset=4",
            headers=headers,
        )
        assert resp.status_code == 200
        data3 = resp.json()["data"]
        assert len(data3) == 1  # only 5 total, 4 already shown


# ---------------------------------------------------------------------------
# RBAC Tests
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# OAuth Auto-Binding Tests (Phase 22)
# ---------------------------------------------------------------------------

class TestOAuthAutoBinding:
    """Test: unique name match auto-binds feishu_open_id to User (D-01 layer 2, D-02)."""

    def test_auto_bind_unique_match(self, test_client_feishu, db_session, seed_employee_master):
        """Feishu name uniquely matches one EmployeeMaster -> auto_bound + feishu_open_id written."""
        # Get authorize URL for valid state
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_auto_bind_123", name="Test User")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data["status"] == "auto_bound"
            assert "access_token" in data

        # Verify feishu_open_id written to user
        user = db_session.query(User).filter(User.feishu_open_id == "ou_auto_bind_123").first()
        assert user is not None
        assert user.display_name == "Test User"

    def test_matched_existing_bound_user(self, test_client_feishu, db_session):
        """open_id already bound to a user -> status=matched, role preserved (D-01 layer 1, D-11)."""
        existing_user = User(
            username="bound_user",
            hashed_password=hash_password("pass"),
            role="hr",
            display_name="Bound HR",
            is_active=True,
            must_change_password=False,
            feishu_open_id="ou_already_bound",
            feishu_union_id="un_bound",
        )
        db_session.add(existing_user)
        db_session.commit()

        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_already_bound", name="Bound HR")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data["status"] == "matched"
            assert data["role"] == "hr"

    def test_new_user_no_match(self, test_client_feishu, db_session):
        """No EmployeeMaster match and no bound user -> status=new_user, employee role (D-01 layer 4, D-12)."""
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_brand_new", name="Unknown Person")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data["status"] == "new_user"
            assert data["role"] == "employee"
            assert "access_token" in data

    def test_new_user_default_employee_role(self, test_client_feishu, db_session):
        """New user created via OAuth always gets employee role (D-12, D-13)."""
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_role_test", name="Role Test")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data["role"] == "employee"

        user = db_session.query(User).filter(User.feishu_open_id == "ou_role_test").first()
        assert user is not None
        assert user.role == "employee"


class TestOAuthPendingCandidates:
    """Test: multiple EmployeeMaster matches -> pending_candidates with masked employee_id (D-01 layer 3, D-04, D-06)."""

    def test_pending_candidates_multiple_matches(self, test_client_feishu, db_session, seed_multiple_employees_same_name):
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_pending_123", name="Duplicate Name")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data["status"] == "pending_candidates"
            assert "pending_token" in data
            assert len(data["candidates"]) == 2

            # Verify employee_id is masked (only last 4 chars visible)
            for c in data["candidates"]:
                assert "employee_master_id" in c
                assert "person_name" in c
                assert "employee_id_masked" in c
                assert c["employee_id_masked"].startswith("****")
                assert len(c["employee_id_masked"]) == 8  # ****XXXX for 7-char IDs

            # Verify no access_token returned for pending state
            assert "access_token" not in data


class TestConfirmBind:
    """Test: confirm-bind endpoint validates pending_token and completes binding (D-05)."""

    def test_confirm_bind_success(self, test_client_feishu, db_session, seed_multiple_employees_same_name):
        """Valid pending_token + employee_master_id -> binding + JWT."""
        # First trigger pending_candidates
        resp = test_client_feishu.get("/api/v1/auth/feishu/authorize-url")
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_confirm_123", name="Duplicate Name")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/callback",
                json={"code": "mock_code", "state": state},
            )
            data = resp2.json()["data"]
            pending_token = data["pending_token"]
            emp_id = data["candidates"][0]["employee_master_id"]

        # Confirm bind
        resp3 = test_client_feishu.post(
            "/api/v1/auth/feishu/confirm-bind",
            json={"pending_token": pending_token, "employee_master_id": emp_id},
        )
        assert resp3.status_code == 200
        data3 = resp3.json()["data"]
        assert "access_token" in data3
        assert data3["status"] == "bound"

        # Verify user has feishu_open_id
        user = db_session.query(User).filter(User.feishu_open_id == "ou_confirm_123").first()
        assert user is not None

    def test_confirm_bind_invalid_token(self, test_client_feishu, db_session):
        """Invalid/expired pending_token -> rejection."""
        resp = test_client_feishu.post(
            "/api/v1/auth/feishu/confirm-bind",
            json={"pending_token": "invalid.token.here", "employee_master_id": "fake-id"},
        )
        assert resp.status_code == 400

    def test_confirm_bind_expired_token(self, test_client_feishu, db_session, seed_multiple_employees_same_name):
        """Expired pending_token -> rejection."""
        import jwt as pyjwt
        from tests.conftest import TEST_SECRET_KEY

        # Create an already-expired token
        from datetime import datetime, timedelta, timezone
        expired_payload = {
            "feishu_open_id": "ou_expired",
            "feishu_union_id": "un_expired",
            "feishu_name": "Expired User",
            "purpose": "confirm_bind",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = pyjwt.encode(expired_payload, TEST_SECRET_KEY, algorithm="HS256")

        resp = test_client_feishu.post(
            "/api/v1/auth/feishu/confirm-bind",
            json={"pending_token": expired_token, "employee_master_id": "fake-id"},
        )
        assert resp.status_code == 400

    def test_confirm_bind_rejects_already_bound_open_id(self, test_client_feishu, db_session, seed_multiple_employees_same_name):
        """open_id already bound to another user -> 409 conflict (T-22-06)."""
        import jwt as pyjwt
        from tests.conftest import TEST_SECRET_KEY
        from datetime import datetime, timedelta, timezone

        # Pre-create a user with this open_id bound
        existing = User(
            username="already_bound",
            hashed_password=hash_password("pass"),
            role="employee",
            display_name="Already Bound",
            is_active=True,
            must_change_password=False,
            feishu_open_id="ou_conflict",
        )
        db_session.add(existing)
        db_session.commit()

        # Create a valid pending token for the same open_id
        payload = {
            "feishu_open_id": "ou_conflict",
            "feishu_union_id": "un_conflict",
            "feishu_name": "Duplicate Name",
            "purpose": "confirm_bind",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        token = pyjwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")
        emp_id = str(seed_multiple_employees_same_name[0].id)

        resp = test_client_feishu.post(
            "/api/v1/auth/feishu/confirm-bind",
            json={"pending_token": token, "employee_master_id": emp_id},
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Bind / Unbind Endpoint Tests (Phase 22 Task 2)
# ---------------------------------------------------------------------------

class TestFeishuBind:
    """Test: bind-authorize-url, bind-callback, unbind endpoints."""

    def test_bind_authorize_url_requires_auth(self, test_client_feishu):
        """No token -> 401."""
        resp = test_client_feishu.get("/api/v1/auth/feishu/bind-authorize-url")
        assert resp.status_code == 401

    def test_bind_authorize_url_returns_url(self, test_client_feishu, seed_test_admin):
        """Authenticated user -> returns feishu authorize URL."""
        token = _login_admin(test_client_feishu)
        resp = test_client_feishu.get(
            "/api/v1/auth/feishu/bind-authorize-url",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "url" in data
        assert "feishu.cn" in data["url"]
        assert "feishu_oauth_state" in test_client_feishu.cookies

    def test_bind_callback_writes_open_id(self, test_client_feishu, seed_test_admin, db_session):
        """Mock httpx + valid state -> feishu_open_id written to current user."""
        token = _login_admin(test_client_feishu)

        # Get bind authorize URL (sets state cookie)
        resp = test_client_feishu.get(
            "/api/v1/auth/feishu/bind-authorize-url",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        url = resp.json()["data"]["url"]
        state = parse_qs(urlparse(url).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_bind_test", name="Admin Feishu")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/bind-callback",
                json={"code": "mock_code", "state": state},
                headers=_auth_headers(token),
            )
            assert resp2.status_code == 200
            data = resp2.json()["data"]
            assert data.get("feishu_name") == "Admin Feishu"

        # Verify in DB
        admin_user = db_session.query(User).filter(User.username == "testadmin").first()
        assert admin_user.feishu_open_id == "ou_bind_test"
        assert admin_user.feishu_union_id == "un_test"

    def test_bind_callback_rejects_already_bound(self, test_client_feishu, seed_test_admin, db_session):
        """open_id already bound to another user -> 409."""
        # Pre-bind another user with this open_id
        other_user = User(
            username="other_bound",
            hashed_password=hash_password("pass"),
            role="employee",
            display_name="Other",
            is_active=True,
            must_change_password=False,
            feishu_open_id="ou_already_taken",
        )
        db_session.add(other_user)
        db_session.commit()

        token = _login_admin(test_client_feishu)
        resp = test_client_feishu.get(
            "/api/v1/auth/feishu/bind-authorize-url",
            headers=_auth_headers(token),
        )
        state = parse_qs(urlparse(resp.json()["data"]["url"]).query)["state"][0]

        mock_http = _make_mock_httpx_client(open_id="ou_already_taken", name="Taken")

        with patch("backend.app.services.feishu_oauth_service.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            resp2 = test_client_feishu.post(
                "/api/v1/auth/feishu/bind-callback",
                json={"code": "mock_code", "state": state},
                headers=_auth_headers(token),
            )
            assert resp2.status_code == 409

    def test_unbind_clears_feishu_ids(self, test_client_feishu, seed_test_admin, db_session):
        """Unbind -> feishu_open_id and feishu_union_id set to null."""
        # First bind the admin
        admin = db_session.query(User).filter(User.username == "testadmin").first()
        admin.feishu_open_id = "ou_to_unbind"
        admin.feishu_union_id = "un_to_unbind"
        db_session.commit()

        token = _login_admin(test_client_feishu)
        resp = test_client_feishu.post(
            "/api/v1/auth/feishu/unbind",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

        db_session.refresh(admin)
        assert admin.feishu_open_id is None
        assert admin.feishu_union_id is None

    def test_unbind_requires_auth(self, test_client_feishu):
        """No token -> 401."""
        resp = test_client_feishu.post("/api/v1/auth/feishu/unbind")
        assert resp.status_code == 401

    def test_me_returns_feishu_bound(self, test_client_feishu, seed_test_admin, db_session):
        """/me returns feishu_bound status."""
        token = _login_admin(test_client_feishu)

        # Before binding
        resp = test_client_feishu.get("/api/v1/auth/me", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["feishu_bound"] is False

        # Bind
        admin = db_session.query(User).filter(User.username == "testadmin").first()
        admin.feishu_open_id = "ou_me_test"
        db_session.commit()

        # After binding
        resp2 = test_client_feishu.get("/api/v1/auth/me", headers=_auth_headers(token))
        data2 = resp2.json()["data"]
        assert data2["feishu_bound"] is True


# ---------------------------------------------------------------------------
# RBAC Tests
# ---------------------------------------------------------------------------

class TestFeishuRBAC:
    def test_sync_push_requires_admin_or_hr(self, test_client_feishu, db_session):
        """Unauthenticated request to sync push should fail."""
        resp = test_client_feishu.post(
            "/api/v1/feishu/sync/push",
            json={"config_id": "fake"},
        )
        assert resp.status_code == 401

    def test_settings_requires_admin(self, test_client_feishu, seed_test_hr, db_session):
        """HR should not be able to access settings (admin-only)."""
        resp = test_client_feishu.post(
            "/api/v1/auth/login",
            json={"username": "testhr", "password": "hrpass123"},
        )
        token = resp.json()["data"]["access_token"]
        headers = _auth_headers(token)

        resp = test_client_feishu.get("/api/v1/feishu/settings/configs", headers=headers)
        assert resp.status_code == 403
