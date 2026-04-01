"""Tests for API documentation access control and Markdown generation."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _get_admin_token(client: TestClient) -> str:
    """Login as admin and return the access token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


def _get_hr_token(client: TestClient) -> str:
    """Login as HR and return the access token."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "testhr",
        "password": "hrpass123",
    })
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


class TestDocsAccessControl:
    """GET /docs requires admin auth."""

    def test_docs_without_auth_returns_401(self, test_client):
        resp = test_client.get("/docs")
        assert resp.status_code == 401

    def test_docs_with_hr_token_returns_403(self, test_client, seed_test_admin, seed_test_hr):
        token = _get_hr_token(test_client)
        resp = test_client.get("/docs", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_docs_with_admin_token_returns_200(self, test_client, seed_test_admin):
        token = _get_admin_token(test_client)
        resp = test_client.get("/docs", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_redoc_with_admin_token_returns_200(self, test_client, seed_test_admin):
        token = _get_admin_token(test_client)
        resp = test_client.get("/redoc", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_openapi_json_with_admin_token_returns_200(self, test_client, seed_test_admin):
        token = _get_admin_token(test_client)
        resp = test_client.get("/api/v1/openapi.json", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "paths" in data
        assert "info" in data

    def test_openapi_json_without_auth_returns_401(self, test_client):
        resp = test_client.get("/api/v1/openapi.json")
        assert resp.status_code == 401


class TestMarkdownDocs:
    """GET /api/v1/docs/markdown returns Markdown documentation."""

    def test_markdown_docs_with_admin_returns_200(self, test_client, seed_test_admin):
        token = _get_admin_token(test_client)
        resp = test_client.get("/api/v1/docs/markdown", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "text/markdown" in content_type
        body = resp.text
        assert body.startswith("# ")

    def test_markdown_docs_without_auth_returns_401(self, test_client):
        resp = test_client.get("/api/v1/docs/markdown")
        assert resp.status_code == 401

    def test_markdown_docs_contains_endpoint_sections(self, test_client, seed_test_admin):
        token = _get_admin_token(test_client)
        resp = test_client.get("/api/v1/docs/markdown", headers={"Authorization": f"Bearer {token}"})
        body = resp.text
        # Should contain tag-based sections
        assert "##" in body


class TestOpenApiChineseDescriptions:
    """OpenAPI schema contains Chinese descriptions and correct tags."""

    def test_schema_has_chinese_tags(self, test_client, seed_test_admin):
        token = _get_admin_token(test_client)
        resp = test_client.get("/api/v1/openapi.json", headers={"Authorization": f"Bearer {token}"})
        schema = resp.json()
        paths = schema.get("paths", {})

        # Collect all tags used across all endpoints
        all_tags = set()
        for path_item in paths.values():
            for method_obj in path_item.values():
                if isinstance(method_obj, dict):
                    for tag in method_obj.get("tags", []):
                        all_tags.add(tag)

        expected_tags = {"认证", "社保查询", "员工管理", "导入导出", "系统管理"}
        for tag in expected_tags:
            assert tag in all_tags, f"Expected tag '{tag}' not found in schema tags: {all_tags}"

    def test_schema_has_chinese_summaries(self, test_client, seed_test_admin):
        token = _get_admin_token(test_client)
        resp = test_client.get("/api/v1/openapi.json", headers={"Authorization": f"Bearer {token}"})
        schema = resp.json()
        paths = schema.get("paths", {})

        # Check auth login endpoint has Chinese summary
        login_path = paths.get("/api/v1/auth/login", {})
        post_op = login_path.get("post", {})
        summary = post_op.get("summary", "")
        assert summary, "Login endpoint should have a summary"
        # Should contain Chinese characters
        assert any('\u4e00' <= c <= '\u9fff' for c in summary), f"Summary should be in Chinese: {summary}"


class TestPaginatedResponse:
    """paginated_response helper is available."""

    def test_paginated_response_function_exists(self):
        from backend.app.api.v1.responses import paginated_response
        assert callable(paginated_response)

    def test_paginated_response_returns_correct_structure(self):
        from backend.app.api.v1.responses import paginated_response
        resp = paginated_response(data=[{"id": 1}], total=10, page=1, page_size=5)
        import json
        body = json.loads(resp.body.decode())
        assert body["success"] is True
        assert body["pagination"]["total"] == 10
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["page_size"] == 5
        assert body["data"] == [{"id": 1}]
