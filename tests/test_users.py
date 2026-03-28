"""Tests for user management CRUD endpoints (admin-only)."""
from __future__ import annotations

import pytest

from backend.app.api.v1.auth import _employee_rate_limiter
from backend.app.services.user_service import hash_password
from tests.conftest import TEST_SECRET_KEY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, username: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


def _get_token(resp) -> str:
    return resp.json()["data"]["access_token"]


def _admin_headers(client, seed_test_admin) -> dict:
    resp = _login(client, "testadmin", "testpass123")
    return {"Authorization": f"Bearer {_get_token(resp)}"}


def _hr_headers(client, seed_test_hr) -> dict:
    resp = _login(client, "testhr", "hrpass123")
    return {"Authorization": f"Bearer {_get_token(resp)}"}


def _employee_headers(client, seed_test_employee) -> dict:
    _employee_rate_limiter._records.clear()
    resp = client.post(
        "/api/v1/auth/employee-verify",
        json={"employee_id": "EMP001", "id_number": "110101199001011234", "person_name": "Zhang San"},
    )
    return {"Authorization": f"Bearer {_get_token(resp)}"}


# ---------------------------------------------------------------------------
# POST /users - Create user
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_create_user_as_admin(self, test_client, seed_test_admin):
        headers = _admin_headers(test_client, seed_test_admin)
        resp = test_client.post("/api/v1/users/", json={
            "username": "newhr",
            "password": "securepass123",
            "role": "hr",
            "display_name": "New HR User",
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["username"] == "newhr"
        assert data["role"] == "hr"
        assert data["display_name"] == "New HR User"
        assert data["is_active"] is True
        # Must not contain password
        assert "password" not in data
        assert "hashed_password" not in data

    def test_create_user_duplicate_username(self, test_client, seed_test_admin):
        headers = _admin_headers(test_client, seed_test_admin)
        # First create
        test_client.post("/api/v1/users/", json={
            "username": "dupuser",
            "password": "securepass123",
            "role": "hr",
        }, headers=headers)
        # Duplicate
        resp = test_client.post("/api/v1/users/", json={
            "username": "dupuser",
            "password": "securepass123",
            "role": "hr",
        }, headers=headers)
        assert resp.status_code == 409

    def test_create_user_as_hr_returns_403(self, test_client, seed_test_admin, seed_test_hr):
        headers = _hr_headers(test_client, seed_test_hr)
        resp = test_client.post("/api/v1/users/", json={
            "username": "newuser",
            "password": "securepass123",
            "role": "hr",
        }, headers=headers)
        assert resp.status_code == 403

    def test_create_user_as_employee_returns_403(self, test_client, seed_test_admin, seed_test_employee):
        headers = _employee_headers(test_client, seed_test_employee)
        resp = test_client.post("/api/v1/users/", json={
            "username": "newuser",
            "password": "securepass123",
            "role": "hr",
        }, headers=headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /users - List users
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_list_users_as_admin(self, test_client, seed_test_admin, seed_test_hr):
        headers = _admin_headers(test_client, seed_test_admin)
        resp = test_client.get("/api/v1/users/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 2  # admin + hr at minimum

    def test_list_users_as_hr_returns_403(self, test_client, seed_test_admin, seed_test_hr):
        headers = _hr_headers(test_client, seed_test_hr)
        resp = test_client.get("/api/v1/users/", headers=headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /users/{id} - Get single user
# ---------------------------------------------------------------------------

class TestGetUser:
    def test_get_user_by_id(self, test_client, seed_test_admin, seed_test_hr):
        headers = _admin_headers(test_client, seed_test_admin)
        user_id = str(seed_test_hr.id)
        resp = test_client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["username"] == "testhr"

    def test_get_user_not_found(self, test_client, seed_test_admin):
        headers = _admin_headers(test_client, seed_test_admin)
        resp = test_client.get("/api/v1/users/00000000-0000-0000-0000-000000000000", headers=headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /users/{id} - Update user
# ---------------------------------------------------------------------------

class TestUpdateUser:
    def test_update_display_name(self, test_client, seed_test_admin, seed_test_hr):
        headers = _admin_headers(test_client, seed_test_admin)
        user_id = str(seed_test_hr.id)
        resp = test_client.put(f"/api/v1/users/{user_id}", json={
            "display_name": "Updated HR Name",
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["display_name"] == "Updated HR Name"

    def test_disable_user(self, test_client, seed_test_admin, seed_test_hr):
        headers = _admin_headers(test_client, seed_test_admin)
        user_id = str(seed_test_hr.id)
        resp = test_client.put(f"/api/v1/users/{user_id}", json={
            "is_active": False,
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["is_active"] is False

    def test_disabled_user_cannot_login(self, test_client, seed_test_admin, seed_test_hr):
        headers = _admin_headers(test_client, seed_test_admin)
        user_id = str(seed_test_hr.id)
        # Disable
        test_client.put(f"/api/v1/users/{user_id}", json={"is_active": False}, headers=headers)
        # Try login
        resp = _login(test_client, "testhr", "hrpass123")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /users/{id}/password - Reset password
# ---------------------------------------------------------------------------

class TestResetPassword:
    def test_reset_password(self, test_client, seed_test_admin, seed_test_hr):
        headers = _admin_headers(test_client, seed_test_admin)
        user_id = str(seed_test_hr.id)
        resp = test_client.put(f"/api/v1/users/{user_id}/password", json={
            "new_password": "brandnewpass123",
        }, headers=headers)
        assert resp.status_code == 200
        # Verify new password works
        resp2 = _login(test_client, "testhr", "brandnewpass123")
        assert resp2.status_code == 200

    def test_reset_password_not_found(self, test_client, seed_test_admin):
        headers = _admin_headers(test_client, seed_test_admin)
        resp = test_client.put(
            "/api/v1/users/00000000-0000-0000-0000-000000000000/password",
            json={"new_password": "brandnewpass123"},
            headers=headers,
        )
        assert resp.status_code == 404
