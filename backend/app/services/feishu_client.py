from __future__ import annotations

import asyncio
import time
from typing import Optional

import httpx

FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"

# Rate limiter: max 15 concurrent requests (conservative; Feishu limit is 20 req/s for some endpoints)
_DEFAULT_MAX_CONCURRENT = 15


class FeishuApiError(Exception):
    """Error raised when Feishu API returns a non-zero error code."""

    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


class FeishuClient:
    """Async Feishu API client with automatic tenant_access_token management and rate limiting.

    IMPORTANT: This client uses httpx.AsyncClient. All public methods are async.
    This is required because FastAPI endpoints use StreamingResponse which runs
    in the async event loop. Using sync httpx.Client would block the event loop. (H1)
    """

    def __init__(self, app_id: str, app_secret: str, max_concurrent: int = _DEFAULT_MAX_CONCURRENT):
        self._app_id = app_id
        self._app_secret = app_secret
        self._token: Optional[str] = None
        self._token_expires_at: float = 0
        self._http = httpx.AsyncClient(base_url=FEISHU_BASE_URL, timeout=30)
        # Rate limiting via semaphore (addresses review M2)
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _ensure_token(self) -> str:
        """Get valid tenant_access_token, refreshing if expired (300s buffer)."""
        if self._token and time.time() < self._token_expires_at - 300:
            return self._token
        async with self._semaphore:
            # Double-check after acquiring semaphore (another coroutine may have refreshed)
            if self._token and time.time() < self._token_expires_at - 300:
                return self._token
            resp = await self._http.post("/auth/v3/tenant_access_token/internal", json={
                "app_id": self._app_id,
                "app_secret": self._app_secret,
            })
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise FeishuApiError(data.get("msg", "Failed to get tenant_access_token"), data.get("code"))
            self._token = data["tenant_access_token"]
            self._token_expires_at = time.time() + data["expire"]
            return self._token

    async def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {await self._ensure_token()}"}

    async def list_fields(self, app_token: str, table_id: str) -> list[dict]:
        """Fetch all field definitions from a Bitable table."""
        items: list[dict] = []
        page_token: Optional[str] = None
        while True:
            params: dict = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token
            async with self._semaphore:
                resp = await self._http.get(
                    f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                    headers=await self._headers(), params=params,
                )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise FeishuApiError(data.get("msg", "list_fields failed"), data.get("code"))
            items.extend(data["data"]["items"])
            if not data["data"].get("has_more"):
                break
            page_token = data["data"].get("page_token")
        return items

    async def batch_create_records(self, app_token: str, table_id: str, records: list[dict]) -> dict:
        """Create records in batch. Max 500 per call (conservative, API limit 1000)."""
        async with self._semaphore:
            resp = await self._http.post(
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                headers=await self._headers(),
                json={"records": [{"fields": r} for r in records]},
            )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise FeishuApiError(data.get("msg", "batch_create failed"), data.get("code"))
        return data

    async def batch_update_records(self, app_token: str, table_id: str, records: list[dict]) -> dict:
        """Update records in batch. Each record must have 'record_id' and 'fields'."""
        async with self._semaphore:
            resp = await self._http.post(
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
                headers=await self._headers(),
                json={"records": records},
            )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise FeishuApiError(data.get("msg", "batch_update failed"), data.get("code"))
        return data

    async def search_records(
        self,
        app_token: str,
        table_id: str,
        filter_expr: Optional[str] = None,
        page_token: Optional[str] = None,
        page_size: int = 500,
    ) -> dict:
        """Search records with optional filter. Max 500 per page."""
        body: dict = {"page_size": page_size}
        if filter_expr:
            body["filter"] = filter_expr
        if page_token:
            body["page_token"] = page_token
        async with self._semaphore:
            resp = await self._http.post(
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
                headers=await self._headers(), json=body,
            )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise FeishuApiError(data.get("msg", "search_records failed"), data.get("code"))
        return data

    async def close(self) -> None:
        await self._http.aclose()


# --- FastAPI Dependency Injection (addresses review M1) ---
# Use Depends(get_feishu_client) in endpoints instead of module-level singleton.

_client_cache: Optional[FeishuClient] = None


async def get_feishu_client() -> FeishuClient:
    """FastAPI dependency that provides a shared FeishuClient instance.

    Usage in endpoints: client: FeishuClient = Depends(get_feishu_client)

    Raises ValueError if Feishu credentials not configured.
    """
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    from backend.app.core.config import get_settings

    settings = get_settings()
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        raise ValueError("Feishu credentials not configured (FEISHU_APP_ID / FEISHU_APP_SECRET)")
    _client_cache = FeishuClient(settings.feishu_app_id, settings.feishu_app_secret)
    return _client_cache


async def reset_feishu_client() -> None:
    """Reset the cached client (for testing or credential update)."""
    global _client_cache
    if _client_cache is not None:
        await _client_cache.close()
    _client_cache = None
