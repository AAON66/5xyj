"""Feishu settings: SyncConfig CRUD, credential status, feature flags, and field discovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import httpx

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.config import Settings
from backend.app.dependencies import get_db
from backend.app.models.sync_config import SyncConfig
from backend.app.models.sync_job import SyncJob
from backend.app.schemas.feishu import (
    FeatureFlags,
    FeishuCredentials,
    FeishuCredentialsStatus,
    FeishuFieldInfo,
    FeishuRuntimeSettingsRead,
    FeishuRuntimeSettingsUpdate,
    SyncConfigCreate,
    SyncConfigRead,
    SyncConfigUpdate,
)
from backend.app.mappings.manual_field_aliases import (
    CANONICAL_FIELDS,
    MANUAL_ALIAS_RULES,
    normalize_signature,
)
from backend.app.services.feishu_client import FeishuClient, get_feishu_client
from backend.app.services.system_setting_service import (
    FEISHU_APP_ID_KEY,
    FEISHU_APP_SECRET_KEY,
    FEISHU_OAUTH_ENABLED_KEY,
    FEISHU_SYNC_ENABLED_KEY,
    EffectiveFeishuSettings,
    get_effective_feishu_settings,
    mask_app_id,
    set_setting,
)

from pydantic import BaseModel as PydanticBaseModel
from typing import List, Optional


async def _get_client_safe(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[FeishuClient]:
    """Get FeishuClient or None if not configured."""
    try:
        effective_settings = _get_effective_settings(request, db)
        return await get_feishu_client(effective_settings.feishu_app_id, effective_settings.feishu_app_secret)
    except ValueError:
        return None

router = APIRouter(prefix="/feishu/settings", tags=["飞书设置"])


def _get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _get_effective_settings(request: Request, db: Session) -> EffectiveFeishuSettings:
    return get_effective_feishu_settings(db, _get_settings(request))


def _build_runtime_settings_read(effective_settings: EffectiveFeishuSettings) -> FeishuRuntimeSettingsRead:
    return FeishuRuntimeSettingsRead(
        feishu_sync_enabled=effective_settings.feishu_sync_enabled,
        feishu_oauth_enabled=effective_settings.feishu_oauth_enabled,
        feishu_credentials_configured=effective_settings.credentials_configured,
        masked_app_id=mask_app_id(effective_settings.feishu_app_id),
        secret_configured=bool(effective_settings.feishu_app_secret),
    )


async def _validate_feishu_credentials(app_id: str, app_secret: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": app_id, "app_secret": app_secret},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                return {
                    "code": "INVALID_CREDENTIALS",
                    "message": f"飞书凭证验证失败: {data.get('msg', '未知错误')}",
                    "status_code": 400,
                }
    except Exception as exc:
        return {
            "code": "VALIDATION_ERROR",
            "message": f"凭证验证请求失败: {exc}",
            "status_code": 502,
        }
    return None


def suggest_field_mapping(
    feishu_fields: list,
    system_fields: Optional[list] = None,
) -> dict:
    """Match feishu fields to canonical system fields using alias rules + exact key fallback."""
    suggestions = []
    matched_field_ids = set()
    for ff in feishu_fields:
        field_name = ff["field_name"]
        field_id = ff.get("field_id", "")
        best_match = None
        best_confidence = 0.0
        best_rule = ""
        for rule in MANUAL_ALIAS_RULES:
            if system_fields and rule.canonical_field not in system_fields:
                continue
            if rule.matches(field_name, region=None):
                if rule.confidence > best_confidence:
                    best_match = rule.canonical_field
                    best_confidence = rule.confidence
                    best_rule = " + ".join(rule.patterns)
        # English exact key fallback
        if best_match is None:
            normalized = normalize_signature(field_name)
            candidates = system_fields if system_fields else list(CANONICAL_FIELDS)
            for sf in candidates:
                if normalized == normalize_signature(sf):
                    best_match = sf
                    best_confidence = 1.0
                    best_rule = "exact_key_match"
                    break
        if best_match:
            suggestions.append({
                "feishu_field_id": field_id,
                "feishu_field_name": field_name,
                "canonical_field": best_match,
                "confidence": best_confidence,
                "matched_rule": best_rule,
            })
            matched_field_ids.add(field_id)
    unmatched = [
        ff.get("field_id", "")
        for ff in feishu_fields
        if ff.get("field_id", "") not in matched_field_ids
    ]
    return {"suggestions": suggestions, "unmatched": unmatched}


class SuggestMappingRequest(PydanticBaseModel):
    feishu_fields: list
    system_fields: Optional[list] = None


@router.get("/configs", summary="获取所有同步配置", description="返回所有激活的同步配置列表。")
async def list_configs(
    request: Request,
    db: Session = Depends(get_db),
):
    configs = db.query(SyncConfig).filter(SyncConfig.is_active.is_(True)).all()
    return success_response([SyncConfigRead.model_validate(c).model_dump() for c in configs])


@router.post("/configs", summary="创建同步配置", description="创建新的飞书同步配置。")
async def create_config(
    body: SyncConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
):
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
    config = db.get(SyncConfig, config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    field_mapping = body.get("field_mapping", {})
    config.field_mapping = field_mapping
    db.commit()
    db.refresh(config)
    return success_response(SyncConfigRead.model_validate(config).model_dump())


@router.post(
    "/configs/{config_id}/suggest-mapping",
    summary="获取字段映射建议",
    description="基于同义词规则库，为飞书字段推荐系统字段映射。",
)
async def suggest_mapping_endpoint(
    config_id: str,
    body: SuggestMappingRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    config = db.get(SyncConfig, config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)
    result = suggest_field_mapping(body.feishu_fields, body.system_fields)
    return success_response(result)


@router.get("/configs/{config_id}/feishu-fields", summary="获取飞书表格字段列表", description="从飞书多维表格获取字段定义。")
async def get_feishu_fields(
    config_id: str,
    request: Request,
    db: Session = Depends(get_db),
    client: Optional[FeishuClient] = Depends(_get_client_safe),
):
    if client is None:
        return error_response("CREDENTIALS_MISSING", "飞书凭证未配置", 400)

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
            ui_type=f.get("ui_type", None),
            description=f.get("description", None),
        ).model_dump()
        for f in fields
    ]
    return success_response(field_infos)


@router.get("/runtime", summary="获取飞书运行时设置", description="返回当前飞书功能开关与脱敏后的凭证状态。")
async def get_runtime_settings(request: Request, db: Session = Depends(get_db)):
    effective_settings = _get_effective_settings(request, db)
    return success_response(_build_runtime_settings_read(effective_settings).model_dump())


@router.put("/runtime", summary="更新飞书运行时开关", description="更新飞书同步与 OAuth 的运行时开关。")
async def update_runtime_settings(
    body: FeishuRuntimeSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    if body.feishu_sync_enabled is not None:
        set_setting(db, FEISHU_SYNC_ENABLED_KEY, body.feishu_sync_enabled)
    if body.feishu_oauth_enabled is not None:
        set_setting(db, FEISHU_OAUTH_ENABLED_KEY, body.feishu_oauth_enabled)
    db.commit()
    effective_settings = _get_effective_settings(request, db)
    return success_response(_build_runtime_settings_read(effective_settings).model_dump())


@router.get("/credentials/status", summary="获取飞书凭证配置状态", description="检查飞书应用凭证是否已配置。")
async def credentials_status(request: Request, db: Session = Depends(get_db)):
    effective_settings = _get_effective_settings(request, db)
    payload = FeishuCredentialsStatus(
        configured=effective_settings.credentials_configured,
        masked_app_id=mask_app_id(effective_settings.feishu_app_id),
        secret_configured=bool(effective_settings.feishu_app_secret),
    )
    return success_response(payload.model_dump())


@router.put("/credentials", summary="验证并保存飞书凭证", description="验证飞书应用凭证是否有效，并持久化到运行时设置。")
async def validate_credentials(
    body: FeishuCredentials,
    request: Request,
    db: Session = Depends(get_db),
):
    validation_error = await _validate_feishu_credentials(body.app_id, body.app_secret)
    if validation_error is not None:
        return error_response(
            validation_error["code"],
            validation_error["message"],
            validation_error["status_code"],
        )

    set_setting(db, FEISHU_APP_ID_KEY, body.app_id)
    set_setting(db, FEISHU_APP_SECRET_KEY, body.app_secret)
    db.commit()
    effective_settings = _get_effective_settings(request, db)
    return success_response(_build_runtime_settings_read(effective_settings).model_dump())


@router.get("/features", summary="获取飞书功能开关状态", description="返回飞书相关功能的开关状态，前端用于条件渲染。")
async def get_feature_flags(request: Request, db: Session = Depends(get_db)):
    effective_settings = _get_effective_settings(request, db)
    flags = FeatureFlags(
        feishu_sync_enabled=effective_settings.feishu_sync_enabled,
        feishu_oauth_enabled=effective_settings.feishu_oauth_enabled,
        feishu_credentials_configured=effective_settings.credentials_configured,
    )
    return success_response(flags.model_dump())
