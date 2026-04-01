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
