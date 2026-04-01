"""Feishu settings: SyncConfig CRUD, credential status, feature flags, and field discovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.config import Settings, get_settings
from backend.app.dependencies import get_db
from backend.app.models.sync_config import SyncConfig
from backend.app.models.sync_job import SyncJob
from backend.app.schemas.feishu import (
    FeatureFlags,
    FeishuCredentials,
    FeishuFieldInfo,
    SyncConfigCreate,
    SyncConfigRead,
    SyncConfigUpdate,
)
from backend.app.services.feishu_client import FeishuClient, get_feishu_client

router = APIRouter(prefix="/feishu/settings", tags=["飞书设置"])


def _get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _check_sync_enabled(settings: Settings):
    if not settings.feishu_sync_enabled:
        return error_response("FEATURE_DISABLED", "飞书同步功能未启用", 404)
    return None


@router.get("/configs", summary="获取所有同步配置", description="返回所有激活的同步配置列表。")
async def list_configs(
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    configs = db.query(SyncConfig).filter(SyncConfig.is_active.is_(True)).all()
    return success_response([SyncConfigRead.model_validate(c).model_dump() for c in configs])


@router.post("/configs", summary="创建同步配置", description="创建新的飞书同步配置。")
async def create_config(
    body: SyncConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    config = SyncConfig(
        name=body.name,
        app_token=body.app_token,
        table_id=body.table_id,
        granularity=body.granularity,
        field_mapping=body.field_mapping,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return success_response(SyncConfigRead.model_validate(config).model_dump(), status_code=201)


@router.put("/configs/{config_id}", summary="更新同步配置", description="更新指定的同步配置。")
async def update_config(
    config_id: str,
    body: SyncConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    config = db.get(SyncConfig, config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return success_response(SyncConfigRead.model_validate(config).model_dump())


@router.delete("/configs/{config_id}", summary="删除同步配置", description="删除指定的同步配置及其关联的同步任务。")
async def delete_config(
    config_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    config = db.get(SyncConfig, config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    # Delete associated sync jobs first
    db.query(SyncJob).filter(SyncJob.config_id == config_id).delete()
    db.delete(config)
    db.commit()
    return success_response(None, status_code=204)


@router.post("/configs/{config_id}/mapping", summary="保存字段映射", description="更新指定配置的字段映射关系。")
async def save_field_mapping(
    config_id: str,
    body: dict,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    config = db.get(SyncConfig, config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    field_mapping = body.get("field_mapping", {})
    config.field_mapping = field_mapping
    db.commit()
    db.refresh(config)
    return success_response(SyncConfigRead.model_validate(config).model_dump())


@router.get("/configs/{config_id}/feishu-fields", summary="获取飞书表格字段列表", description="从飞书多维表格获取字段定义。")
async def get_feishu_fields(
    config_id: str,
    request: Request,
    db: Session = Depends(get_db),
    client: FeishuClient = Depends(get_feishu_client),
):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    config = db.get(SyncConfig, config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    try:
        fields = await client.list_fields(config.app_token, config.table_id)
    except Exception as e:
        return error_response("FEISHU_API_ERROR", f"获取飞书字段失败: {e}", 502)

    field_infos = [
        FeishuFieldInfo(
            field_id=f.get("field_id", ""),
            field_name=f.get("field_name", ""),
            field_type=f.get("type", 0),
            description=f.get("description", None),
        ).model_dump()
        for f in fields
    ]
    return success_response(field_infos)


@router.get("/credentials/status", summary="获取飞书凭证配置状态", description="检查飞书应用凭证是否已配置。")
async def credentials_status(request: Request):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    configured = bool(settings.feishu_app_id and settings.feishu_app_secret)
    return success_response({"configured": configured})


@router.put("/credentials", summary="验证飞书凭证", description="验证飞书应用凭证是否有效（不会存储到数据库）。")
async def validate_credentials(
    body: FeishuCredentials,
    request: Request,
):
    settings = _get_settings(request)
    disabled = _check_sync_enabled(settings)
    if disabled:
        return disabled

    # Validate credentials by attempting a token fetch -- DO NOT store to DB
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": body.app_id, "app_secret": body.app_secret},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                return error_response(
                    "INVALID_CREDENTIALS",
                    f"飞书凭证验证失败: {data.get('msg', '未知错误')}",
                    400,
                )
    except Exception as e:
        return error_response("VALIDATION_ERROR", f"凭证验证请求失败: {e}", 502)

    return success_response({"valid": True})


@router.get("/features", summary="获取飞书功能开关状态", description="返回飞书相关功能的开关状态，前端用于条件渲染。")
async def get_feature_flags(
    settings: Settings = Depends(get_settings),
):
    flags = FeatureFlags(
        feishu_sync_enabled=settings.feishu_sync_enabled,
        feishu_oauth_enabled=settings.feishu_oauth_enabled,
        feishu_credentials_configured=bool(settings.feishu_app_id and settings.feishu_app_secret),
    )
    return success_response(flags.model_dump())
