from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For header."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
