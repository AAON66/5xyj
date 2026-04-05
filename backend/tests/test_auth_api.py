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


ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'auth_api'


def build_test_client(test_name: str) -> TestClient:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / 'auth.db'
    settings = Settings(
        app_name='auth-test',
        app_version='0.2.0',
        runtime_environment='production',
        database_url=f'sqlite:///{database_path.as_posix()}',
        upload_dir=str(artifacts_dir / 'uploads'),
        samples_dir=str(artifacts_dir / 'samples'),
        templates_dir=str(artifacts_dir / 'templates'),
        outputs_dir=str(artifacts_dir / 'outputs'),
        auth_secret_key='auth-test-secret',
        admin_login_username='admin',
        admin_login_password='admin-pass',
        hr_login_username='hr',
        hr_login_password='hr-pass',
        log_format='plain',
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
    return TestClient(app)


def test_login_endpoint_returns_bearer_token_for_admin() -> None:
    client = build_test_client('login_admin')

    with client:
        response = client.post(
            '/api/v1/auth/login',
            json={'username': 'admin', 'password': 'admin-pass', 'role': 'admin'},
        )

    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['token_type'] == 'bearer'
    assert payload['access_token']
    assert payload['user']['username'] == 'admin'
    assert payload['user']['role'] == 'admin'


def test_login_endpoint_rejects_invalid_credentials() -> None:
    client = build_test_client('login_invalid')

    with client:
        response = client.post(
            '/api/v1/auth/login',
            json={'username': 'admin', 'password': 'wrong-pass', 'role': 'admin'},
        )

    assert response.status_code == 401
    assert response.json()['error']['code'] == 'http_error'


def test_protected_endpoint_requires_bearer_token() -> None:
    client = build_test_client('protected_requires_token')

    with client:
        response = client.get('/api/v1/employees')

    assert response.status_code == 401
    assert response.json()['error']['code'] == 'http_error'


def test_me_endpoint_returns_authenticated_user_profile() -> None:
    client = build_test_client('me_profile')

    with client:
        login_response = client.post(
            '/api/v1/auth/login',
            json={'username': 'hr', 'password': 'hr-pass', 'role': 'hr'},
        )
        token = login_response.json()['data']['access_token']
        response = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['username'] == 'hr'
    assert payload['role'] == 'hr'
    assert payload['display_name'] == 'HR'


def test_employee_self_service_query_requires_auth() -> None:
    client = build_test_client('self_service_requires_auth')

    with client:
        # Unauthenticated request should be rejected
        response = client.post(
            '/api/v1/employees/self-service/query',
            json={'person_name': 'missing-employee', 'id_number': '440101199001019999'},
        )
        assert response.status_code == 401
        assert response.json()['error']['code'] == 'http_error'

        # Authenticated request returns 404 when employee not found
        token, _exp = issue_access_token('auth-test-secret', sub='admin', role='admin', expire_minutes=30)
        auth_response = client.post(
            '/api/v1/employees/self-service/query',
            json={'person_name': 'missing-employee', 'id_number': '440101199001019999'},
            headers={'Authorization': f'Bearer {token}'},
        )

    assert auth_response.status_code == 404
    assert auth_response.json()['error']['code'] == 'not_found'