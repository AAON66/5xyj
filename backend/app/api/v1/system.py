from __future__ import annotations

from fastapi import APIRouter, Request

from backend.app.api.v1.responses import success_response
from backend.app.core.config import Settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def api_healthcheck(request: Request):
    settings: Settings = request.app.state.settings
    return success_response(
        {
            "status": "ok",
            "app_name": settings.app_name,
            "version": settings.app_version,
        }
    )


@router.get("/echo/{value}")
async def echo_value(value: int):
    return success_response({"value": value})
