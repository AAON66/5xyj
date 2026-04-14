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


ARTIFACTS_ROOT = ROOT_DIR / ".test_artifacts" / "fusion_rules_api"


def build_test_client(test_name: str) -> tuple[TestClient, Settings, Session]:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / "fusion_rules.db"
    settings = Settings(
        app_name="fusion-rules-test",
        app_version="0.2.0",
        runtime_environment="production",
        database_url=f"sqlite:///{database_path.as_posix()}",
        upload_dir=str(artifacts_dir / "uploads"),
        samples_dir=str(artifacts_dir / "samples"),
        templates_dir=str(artifacts_dir / "templates"),
        outputs_dir=str(artifacts_dir / "outputs"),
        auth_secret_key="fusion-rules-test-secret",
        admin_login_username="admin",
        admin_login_password="admin-pass",
        hr_login_username="hr",
        hr_login_password="hr-pass",
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
    return TestClient(app), settings, session_factory()


def auth_headers(settings: Settings, *, username: str, role: str) -> dict[str, str]:
    token, _ = issue_access_token(settings.auth_secret_key, sub=username, role=role, expire_minutes=30)
    return {"Authorization": f"Bearer {token}"}


def test_fusion_rule_crud_flow_for_admin() -> None:
    client, settings, _db = build_test_client("crud_admin")

    with client:
        create_response = client.post(
            "/api/v1/fusion-rules",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={
                "scope_type": "employee_id",
                "scope_value": "E9001",
                "field_name": "personal_social_burden",
                "override_value": "123.45",
                "note": "manual override",
            },
        )
        assert create_response.status_code == 201
        rule_id = create_response.json()["data"]["id"]
        assert create_response.json()["data"]["created_by"] == "admin"

        list_response = client.get(
            "/api/v1/fusion-rules",
            headers=auth_headers(settings, username="admin", role="admin"),
            params={"is_active": "true"},
        )
        assert list_response.status_code == 200
        assert len(list_response.json()["data"]) == 1

        update_response = client.put(
            f"/api/v1/fusion-rules/{rule_id}",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={"is_active": False, "override_value": "200.00"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["is_active"] is False

        filtered_response = client.get(
            "/api/v1/fusion-rules",
            headers=auth_headers(settings, username="admin", role="admin"),
            params={"is_active": "true"},
        )
        assert filtered_response.status_code == 200
        assert filtered_response.json()["data"] == []

        delete_response = client.delete(
            f"/api/v1/fusion-rules/{rule_id}",
            headers=auth_headers(settings, username="admin", role="admin"),
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["data"]["deleted"] is True


def test_fusion_rule_crud_flow_for_hr() -> None:
    client, settings, _db = build_test_client("crud_hr")

    with client:
        response = client.post(
            "/api/v1/fusion-rules",
            headers=auth_headers(settings, username="hr", role="hr"),
            json={
                "scope_type": "id_number",
                "scope_value": "440101199001010011",
                "field_name": "personal_housing_burden",
                "override_value": "88.00",
            },
        )

    assert response.status_code == 201
    assert response.json()["data"]["created_by"] == "hr"


def test_employee_cannot_access_fusion_rules_api() -> None:
    client, settings, _db = build_test_client("employee_forbidden")

    with client:
        response = client.get(
            "/api/v1/fusion-rules",
            headers=auth_headers(settings, username="E1001", role="employee"),
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "http_error"


def test_invalid_fusion_rule_field_name_is_rejected() -> None:
    client, settings, _db = build_test_client("invalid_field_name")

    with client:
        response = client.post(
            "/api/v1/fusion-rules",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={
                "scope_type": "employee_id",
                "scope_value": "E9001",
                "field_name": "company_total_amount",
                "override_value": "1.00",
            },
        )

    assert response.status_code == 422


def test_invalid_fusion_rule_scope_type_is_rejected() -> None:
    client, settings, _db = build_test_client("invalid_scope_type")

    with client:
        response = client.post(
            "/api/v1/fusion-rules",
            headers=auth_headers(settings, username="admin", role="admin"),
            json={
                "scope_type": "person_name",
                "scope_value": "张三",
                "field_name": "personal_social_burden",
                "override_value": "1.00",
            },
        )

    assert response.status_code == 422
