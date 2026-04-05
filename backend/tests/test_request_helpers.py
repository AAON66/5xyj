from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.app.utils.request_helpers import get_client_ip


def _make_request(client_host: str | None, headers: dict[str, str] | None = None) -> Request:
    """Create a mock Request object."""
    request = MagicMock(spec=Request)
    if client_host is None:
        request.client = None
    else:
        client = MagicMock()
        client.host = client_host
        request.client = client
    request.headers = headers or {}
    return request


def _mock_settings(trusted_proxies: list[str]):
    """Create a mock settings object with trusted_proxies."""
    settings = MagicMock()
    settings.trusted_proxies = trusted_proxies
    return settings


def test_get_client_ip_no_proxy_header_returns_direct():
    """Test 1: 无代理头时返回 request.client.host"""
    request = _make_request("192.168.1.100")
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1"]),
    ):
        assert get_client_ip(request) == "192.168.1.100"


def test_get_client_ip_xff_trusted_proxy():
    """Test 2: 有 X-Forwarded-For 头且直连 IP 在 trusted_proxies 中时，返回 XFF 第一个 IP"""
    request = _make_request("127.0.0.1", {"x-forwarded-for": "1.2.3.4"})
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1", "::1"]),
    ):
        assert get_client_ip(request) == "1.2.3.4"


def test_get_client_ip_xff_untrusted_proxy_ignored():
    """Test 3: 有 X-Forwarded-For 头但直连 IP 不在 trusted_proxies 中时，忽略 header"""
    request = _make_request("8.8.8.8", {"x-forwarded-for": "1.2.3.4"})
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1", "::1"]),
    ):
        assert get_client_ip(request) == "8.8.8.8"


def test_get_client_ip_x_real_ip_trusted_proxy():
    """Test 4: 有 X-Real-IP 头且直连 IP 在 trusted_proxies 中时，返回 X-Real-IP"""
    request = _make_request("127.0.0.1", {"x-real-ip": "5.6.7.8"})
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1"]),
    ):
        assert get_client_ip(request) == "5.6.7.8"


def test_get_client_ip_xff_priority_over_x_real_ip():
    """Test 5: 同时有 X-Forwarded-For 和 X-Real-IP 时，X-Forwarded-For 优先"""
    request = _make_request(
        "127.0.0.1",
        {"x-forwarded-for": "1.2.3.4", "x-real-ip": "5.6.7.8"},
    )
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1"]),
    ):
        assert get_client_ip(request) == "1.2.3.4"


def test_get_client_ip_xff_multiple_ips_takes_first():
    """Test 6: X-Forwarded-For 含多个 IP 时取第一个"""
    request = _make_request("127.0.0.1", {"x-forwarded-for": "1.2.3.4, 5.6.7.8, 9.10.11.12"})
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1"]),
    ):
        assert get_client_ip(request) == "1.2.3.4"


def test_get_client_ip_no_client_returns_unknown():
    """Test 7: request.client 为 None 时返回 'unknown'"""
    request = _make_request(None, {"x-forwarded-for": "1.2.3.4"})
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1"]),
    ):
        assert get_client_ip(request) == "unknown"


def test_get_client_ip_integration_with_fastapi_testclient():
    """Test 8: 集成测试 — 通过 FastAPI TestClient 发送带 X-Forwarded-For 的请求"""
    app = FastAPI()

    @app.get("/ip")
    def read_ip(request: Request) -> dict:
        return {"ip": get_client_ip(request)}

    client = TestClient(app)

    # TestClient 的默认 client host 是 'testclient'，不会在 trusted_proxies 中
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["testclient"]),
    ):
        response = client.get("/ip", headers={"X-Forwarded-For": "203.0.113.42"})
        assert response.status_code == 200
        assert response.json() == {"ip": "203.0.113.42"}

    # 不信任 testclient 时，应返回 testclient 而非 header 值
    with patch(
        "backend.app.utils.request_helpers.get_settings",
        return_value=_mock_settings(["127.0.0.1"]),
    ):
        response = client.get("/ip", headers={"X-Forwarded-For": "203.0.113.42"})
        assert response.status_code == 200
        # direct_ip should be 'testclient' (not trusted) so header ignored
        assert response.json()["ip"] != "203.0.113.42"
