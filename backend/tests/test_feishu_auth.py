"""Smoke tests for Feishu OAuth authentication endpoints.

Covers three minimal paths per Phase 24 Plan 01 Task 1:
1. authorize-url returns signed URL + state_signed envelope
2. callback success path (monkeypatched _fetch_feishu_user_info) creates a new_user
3. callback rejects invalid state_signed with 400 + code=INVALID_STATE

HTTP to accounts.feishu.cn / open.feishu.cn is avoided by monkeypatching the
service-level fetch helper; no real network traffic should occur.
"""

from __future__ import annotations

import shutil
from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.models import Base


ARTIFACTS_ROOT = ROOT_DIR / ".test_artifacts" / "feishu_auth"

# 32+ character secret avoids jwt InsecureKeyLengthWarning (SHA-256 minimum).
# Also avoids UNSAFE_AUTH_SECRET_KEYS list (which includes bare "test-secret").
_TEST_AUTH_SECRET = "feishu-auth-smoke-test-secret-key-2026"


def build_test_client(test_name: str) -> tuple[TestClient, Settings]:
    """Build an isolated TestClient with fresh sqlite + settings for a single test."""
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / "feishu_auth.db"
    settings = Settings(
        app_name="feishu-auth-test",
        app_version="0.2.0",
        runtime_environment="production",
        database_url=f"sqlite:///{database_path.as_posix()}",
        upload_dir=str(artifacts_dir / "uploads"),
        samples_dir=str(artifacts_dir / "samples"),
        templates_dir=str(artifacts_dir / "templates"),
        outputs_dir=str(artifacts_dir / "outputs"),
        auth_secret_key=_TEST_AUTH_SECRET,
        admin_login_password="admin-pass-123",
        hr_login_password="hr-pass-123",
        feishu_sync_enabled=False,
        feishu_oauth_enabled=True,
        feishu_app_id="test-app-id",
        feishu_app_secret="test-app-secret",
        log_format="plain",
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
    return TestClient(app), settings


def test_authorize_url_returns_url_and_state_signed() -> None:
    """GET /api/v1/auth/feishu/authorize-url returns authorize URL + state_signed."""
    client, _settings = build_test_client("authorize_url")

    with client:
        response = client.get("/api/v1/auth/feishu/authorize-url")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    data = body["data"]
    url = data["url"]
    state_signed = data["state_signed"]

    assert url.startswith("https://accounts.feishu.cn/open-apis/authen/v1/authorize")
    assert "client_id=test-app-id" in url

    # state_signed envelope is `{state}.{HMAC}` -- must contain exactly one '.'
    assert state_signed
    assert "." in state_signed
    state_from_envelope, sig_part = state_signed.rsplit(".", 1)
    assert state_from_envelope
    assert sig_part
    # And the state query parameter in the URL must match the envelope's state half.
    query = parse_qs(urlparse(url).query)
    assert query.get("state") == [state_from_envelope]


def test_callback_success_matched_path(monkeypatch) -> None:
    """POST /api/v1/auth/feishu/callback with valid state_signed returns a JWT.

    Empty DB means 3-level matching falls through to `new_user` (layer 4).
    Real Feishu HTTP is bypassed via monkeypatched _fetch_feishu_user_info.
    """
    client, _settings = build_test_client("callback_success")

    async def mock_fetch_feishu_user_info(_code: str, _settings: Any) -> dict:
        return {
            "open_id": "ou_test_123",
            "union_id": "on_test_123",
            "name": "测试用户",
        }

    # Patch the service-level helper AND the symbol re-exported into the API module,
    # because feishu_auth.py does `from ... import _fetch_feishu_user_info`.
    monkeypatch.setattr(
        "backend.app.services.feishu_oauth_service._fetch_feishu_user_info",
        mock_fetch_feishu_user_info,
    )
    monkeypatch.setattr(
        "backend.app.api.v1.feishu_auth._fetch_feishu_user_info",
        mock_fetch_feishu_user_info,
    )

    with client:
        # 1. Obtain a real, signature-valid state_signed envelope from the authorize-url endpoint.
        authorize_resp = client.get("/api/v1/auth/feishu/authorize-url")
        assert authorize_resp.status_code == 200
        authorize_data = authorize_resp.json()["data"]
        state_signed = authorize_data["state_signed"]
        state_from_url = parse_qs(urlparse(authorize_data["url"]).query)["state"][0]

        # 2. Post the callback with a matching state + state_signed.
        callback_resp = client.post(
            "/api/v1/auth/feishu/callback",
            json={
                "code": "mock-code",
                "state": state_from_url,
                "state_signed": state_signed,
            },
        )

    assert callback_resp.status_code == 200
    callback_body = callback_resp.json()
    assert callback_body["success"] is True

    result = callback_body["data"]
    # Empty DB -> 3-level matching fallthrough -> new_user (layer 4).
    assert result["status"] in {"matched", "auto_bound", "new_user"}
    assert result["status"] == "new_user"
    # JWT envelope populated.
    assert result["access_token"]
    assert result["role"] == "employee"


def test_callback_rejects_invalid_state_signed() -> None:
    """POST /api/v1/auth/feishu/callback with bad HMAC -> 400 + INVALID_STATE."""
    client, _settings = build_test_client("callback_invalid_state")

    with client:
        response = client.post(
            "/api/v1/auth/feishu/callback",
            json={
                "code": "anything",
                "state": "tampered-state",
                "state_signed": "some-bad-signature.not-a-real-hmac",
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_STATE"
