from __future__ import annotations

import shutil

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.auth import issue_access_token
from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.models import Base


ARTIFACTS_ROOT = ROOT_DIR / ".test_artifacts" / "feishu_settings_api"


def build_test_client(test_name: str) -> tuple[TestClient, Settings]:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / "feishu_settings.db"
    settings = Settings(
        app_name="feishu-settings-test",
        app_version="0.2.0",
        runtime_environment="production",
        database_url=f"sqlite:///{database_path.as_posix()}",
        upload_dir=str(artifacts_dir / "uploads"),
        samples_dir=str(artifacts_dir / "samples"),
        templates_dir=str(artifacts_dir / "templates"),
        outputs_dir=str(artifacts_dir / "outputs"),
        auth_secret_key="feishu-settings-test-secret",
        admin_login_password="admin-pass-123",
        hr_login_password="hr-pass-123",
        feishu_sync_enabled=False,
        feishu_oauth_enabled=False,
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


def auth_headers(settings: Settings, *, username: str, role: str) -> dict[str, str]:
    token, _ = issue_access_token(settings.auth_secret_key, sub=username, role=role, expire_minutes=30)
    return {"Authorization": f"Bearer {token}"}


def _mock_credential_validation(monkeypatch) -> None:
    async def fake_validate(_app_id: str, _app_secret: str):
        return None

    monkeypatch.setattr(
        "backend.app.api.v1.feishu_settings._validate_feishu_credentials",
        fake_validate,
    )


def test_admin_can_read_and_update_feishu_runtime_settings(monkeypatch) -> None:
    client, settings = build_test_client("runtime_admin")
    _mock_credential_validation(monkeypatch)

    with client:
        initial_response = client.get(
            "/api/v1/feishu/settings/runtime",
            headers=auth_headers(settings, username="admin", role="admin"),
        )
        assert initial_response.status_code == 200
        assert initial_response.json()["data"]["feishu_sync_enabled"] is False
        assert initial_response.json()["data"]["feishu_credentials_configured"] is False
        assert initial_response.json()["data"]["masked_app_id"] is None

        runtime_update = client.put(
            "/api/v1/feishu/settings/runtime",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={"feishu_sync_enabled": True, "feishu_oauth_enabled": True},
        )
        assert runtime_update.status_code == 200
        assert runtime_update.json()["data"]["feishu_sync_enabled"] is True
        assert runtime_update.json()["data"]["feishu_oauth_enabled"] is True

        credentials_update = client.put(
            "/api/v1/feishu/settings/credentials",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={"app_id": "cli_a1b2c3d4", "app_secret": "secret-123"},
        )
        assert credentials_update.status_code == 200
        payload = credentials_update.json()["data"]
        assert payload["feishu_credentials_configured"] is True
        assert payload["secret_configured"] is True
        assert payload["masked_app_id"] is not None
        assert "secret-123" not in str(payload)
        assert "cli_a1b2c3d4" not in str(payload)

        status_response = client.get(
            "/api/v1/feishu/settings/credentials/status",
            headers=auth_headers(settings, username="admin", role="admin"),
        )
        assert status_response.status_code == 200
        assert status_response.json()["data"]["configured"] is True
        assert status_response.json()["data"]["secret_configured"] is True

        feature_response = client.get("/api/v1/system/features")
        assert feature_response.status_code == 200
        assert feature_response.json()["data"]["feishu_sync_enabled"] is True
        assert feature_response.json()["data"]["feishu_oauth_enabled"] is True
        assert feature_response.json()["data"]["feishu_credentials_configured"] is True


def test_non_admin_cannot_write_feishu_runtime_settings() -> None:
    client, settings = build_test_client("runtime_forbidden")

    with client:
        response = client.put(
            "/api/v1/feishu/settings/runtime",
            headers=auth_headers(settings, username="hr", role="hr"),
            json={"feishu_sync_enabled": True},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "http_error"


def test_effective_settings_drive_oauth_and_sync_feature_switches(monkeypatch) -> None:
    client, settings = build_test_client("effective_settings")
    _mock_credential_validation(monkeypatch)

    with client:
        disabled_oauth = client.get("/api/v1/auth/feishu/authorize-url")
        assert disabled_oauth.status_code == 404

        disabled_sync = client.get(
            "/api/v1/feishu/sync/history",
            headers=auth_headers(settings, username="admin", role="admin"),
        )
        assert disabled_sync.status_code == 404

        client.put(
            "/api/v1/feishu/settings/runtime",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={"feishu_sync_enabled": True, "feishu_oauth_enabled": True},
        )
        client.put(
            "/api/v1/feishu/settings/credentials",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={"app_id": "cli_runtime_x1", "app_secret": "secret-xyz"},
        )

        enabled_oauth = client.get("/api/v1/auth/feishu/authorize-url")
        assert enabled_oauth.status_code == 200
        oauth_url = enabled_oauth.json()["data"]["url"]
        assert "client_id=cli_runtime_x1" in oauth_url

        enabled_sync = client.get(
            "/api/v1/feishu/sync/history",
            headers=auth_headers(settings, username="admin", role="admin"),
        )
        assert enabled_sync.status_code == 200
        assert enabled_sync.json()["data"] == []
