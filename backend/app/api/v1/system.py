from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import success_response
from backend.app.core.config import Settings
from backend.app.dependencies import get_db
from backend.app.services.system_setting_service import get_effective_feishu_settings

router = APIRouter(prefix="/system", tags=["\u7cfb\u7edf\u7ba1\u7406"])


@router.get("/health", summary="\u7cfb\u7edf\u5065\u5eb7\u68c0\u67e5", description="\u8fd4\u56de\u7cfb\u7edf\u8fd0\u884c\u72b6\u6001\u3002", include_in_schema=False)
async def api_healthcheck(request: Request):
    settings: Settings = request.app.state.settings
    return success_response(
        {
            "status": "ok",
            "app_name": settings.app_name,
            "version": settings.app_version,
        }
    )


@router.get("/echo/{value}", summary="\u56de\u663e\u6d4b\u8bd5", description="\u56de\u663e\u4f20\u5165\u7684\u503c\uff0c\u7528\u4e8e\u8fde\u901a\u6027\u6d4b\u8bd5\u3002", include_in_schema=False)
async def echo_value(value: int):
    return success_response({"value": value})


@router.get("/features", summary="获取系统功能开关", description="返回系统功能开关状态，前端用于条件渲染。")
def get_feature_flags(request: Request, db: Session = Depends(get_db)):
    settings: Settings = request.app.state.settings
    effective_settings = get_effective_feishu_settings(db, settings)
    return success_response({
        "feishu_sync_enabled": effective_settings.feishu_sync_enabled,
        "feishu_oauth_enabled": effective_settings.feishu_oauth_enabled,
        "feishu_credentials_configured": effective_settings.credentials_configured,
    })
