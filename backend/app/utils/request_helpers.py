from __future__ import annotations

from fastapi import Request

from backend.app.core.config import get_settings


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting reverse proxy headers.

    Priority: X-Forwarded-For (first IP) > X-Real-IP > direct connection.
    Only trusts proxy headers if the direct connection is from a trusted proxy.
    """
    direct_ip = request.client.host if request.client else "unknown"

    if direct_ip == "unknown":
        return direct_ip

    settings = get_settings()
    trust_headers = direct_ip in settings.trusted_proxies

    if trust_headers:
        # X-Forwarded-For: client, proxy1, proxy2
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # X-Real-IP: single IP set by nginx
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

    return direct_ip
