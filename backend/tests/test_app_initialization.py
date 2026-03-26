from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.bootstrap import UnsafeAuthConfigurationError
from backend.app.core.config import Settings
from backend.app.main import create_app


def build_test_client(**overrides: object) -> TestClient:
    settings = Settings(
        app_name='测试社保工具',
        app_version='9.9.9',
        backend_cors_origins=['http://localhost:3000'],
        max_upload_size_mb=1,
        upload_dir='./.test_artifacts/app_init/uploads',
        samples_dir='./.test_artifacts/app_init/samples',
        templates_dir='./.test_artifacts/app_init/templates',
        outputs_dir='./.test_artifacts/app_init/outputs',
        log_format='plain',
        **overrides,
    )
    return TestClient(create_app(settings))


def test_root_healthcheck_returns_wrapped_success_payload() -> None:
    with build_test_client() as client:
        response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {
        'success': True,
        'message': 'ok',
        'data': {
            'status': 'ok',
            'app_name': '测试社保工具',
            'version': '9.9.9',
        },
    }


def test_api_healthcheck_uses_app_settings() -> None:
    with build_test_client() as client:
        response = client.get('/api/v1/system/health')

    assert response.status_code == 200
    assert response.json()['data'] == {
        'status': 'ok',
        'app_name': '测试社保工具',
        'version': '9.9.9',
    }


def test_cors_preflight_returns_allowed_origin_headers() -> None:
    with build_test_client() as client:
        response = client.options(
            '/api/v1/system/health',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
            },
        )

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:3000'
    assert 'GET' in response.headers['access-control-allow-methods']


def test_validation_error_is_wrapped() -> None:
    with build_test_client() as client:
        response = client.get('/api/v1/system/echo/not-an-int')

    assert response.status_code == 422
    payload = response.json()
    assert payload['success'] is False
    assert payload['error']['code'] == 'validation_error'
    assert payload['error']['message'] == 'Request validation failed.'
    assert payload['error']['details']


def test_not_found_is_wrapped() -> None:
    with build_test_client() as client:
        response = client.get('/api/v1/missing')

    assert response.status_code == 404
    assert response.json() == {
        'success': False,
        'error': {
            'code': 'not_found',
            'message': 'Not Found',
        },
    }


def test_upload_guard_rejects_oversized_multipart_payload() -> None:
    with build_test_client() as client:
        response = client.post(
            '/api/v1/system/health',
            content=b'x',
            headers={
                'content-type': 'multipart/form-data; boundary=test-boundary',
                'content-length': str((1024 * 1024) + 1),
            },
        )

    assert response.status_code == 413
    assert response.json() == {
        'success': False,
        'error': {
            'code': 'payload_too_large',
            'message': 'Upload exceeds the configured 1048576 byte limit.',
        },
    }


def test_local_runtime_allows_startup_with_default_auth_settings() -> None:
    with build_test_client(runtime_environment='local') as client:
        response = client.get('/health')

    assert response.status_code == 200


def test_default_admin_password_non_local_startup_is_rejected() -> None:
    client = build_test_client(
        runtime_environment='production',
        auth_secret_key='safe-signing-secret',
        admin_login_password='admin123',
        hr_login_password='hr-pass',
    )

    with pytest.raises(UnsafeAuthConfigurationError, match='admin_login_password'):
        with client:
            pass


def test_default_hr_password_non_local_startup_is_rejected() -> None:
    client = build_test_client(
        runtime_environment='production',
        auth_secret_key='safe-signing-secret',
        admin_login_password='admin-pass',
        hr_login_password='hr123',
    )

    with pytest.raises(UnsafeAuthConfigurationError, match='hr_login_password'):
        with client:
            pass


def test_default_secret_non_local_startup_is_rejected() -> None:
    client = build_test_client(
        runtime_environment='production',
        auth_secret_key='change-this-auth-secret',
        admin_login_password='admin-pass',
        hr_login_password='hr-pass',
    )

    with pytest.raises(UnsafeAuthConfigurationError, match='auth_secret_key'):
        with client:
            pass