"""Feishu sync trigger and history endpoints with NDJSON streaming."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.config import Settings
from backend.app.dependencies import get_db
from backend.app.schemas.feishu import (
    ConflictResolution,
    PullRequest,
    PushConflictAction,
    PushRequest,
    SyncJobRead,
)
from backend.app.services.feishu_client import FeishuClient, get_feishu_client
from backend.app.services.system_setting_service import EffectiveFeishuSettings, get_effective_feishu_settings
from backend.app.services.feishu_sync_service import (
    check_push_conflicts,
    detect_pull_conflicts,
    get_sync_history,
    pull_records_from_feishu,
    push_records_to_feishu,
    retry_sync_job,
)

router = APIRouter(prefix="/feishu/sync", tags=["飞书同步"])


def _get_effective_settings(request: Request, db: Session) -> EffectiveFeishuSettings:
    return get_effective_feishu_settings(db, request.app.state.settings)


def _check_sync_enabled(settings: EffectiveFeishuSettings):
    if not settings.feishu_sync_enabled:
        return error_response("FEATURE_DISABLED", "飞书同步功能未启用", 404)
    return None


async def _get_client_safe(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[FeishuClient]:
    """Get FeishuClient or None if not configured (avoids DI failure when feature disabled)."""
    try:
        effective_settings = _get_effective_settings(request, db)
        return await get_feishu_client(effective_settings.feishu_app_id, effective_settings.feishu_app_secret)
    except ValueError:
        return None


@router.post("/push", summary="推送数据到飞书", description="将系统中的社保记录推送到飞书多维表格。")
async def push_to_feishu(
    body: PushRequest,
    request: Request,
    db: Session = Depends(get_db),
    client: Optional[FeishuClient] = Depends(_get_client_safe),
):
    effective_settings = _get_effective_settings(request, db)
    disabled = _check_sync_enabled(effective_settings)
    if disabled:
        return disabled

    if client is None:
        return error_response("CREDENTIALS_MISSING", "飞书凭证未配置", 400)

    from backend.app.models.sync_config import SyncConfig

    config = db.get(SyncConfig, body.config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    # Check for conflicts first
    conflicts = await check_push_conflicts(db, client, config, body.filters)
    if conflicts and conflicts.total_conflicts > 0:
        return success_response(conflicts.model_dump(), message="conflict_preview")

    # Stream push progress via NDJSON
    async def push_event_stream():
        job = await push_records_to_feishu(
            db, client, config, body.filters, triggered_by="api_push"
        )
        yield json.dumps({"type": "start", "total": job.total_records}) + "\n"
        yield json.dumps({
            "type": "complete",
            "job_id": str(job.id),
            "success_records": job.success_records,
            "failed_records": job.failed_records,
            "status": job.status,
        }) + "\n"

    return StreamingResponse(push_event_stream(), media_type="application/x-ndjson")


@router.post("/push/confirm", summary="确认推送（处理冲突后）", description="处理冲突后确认推送数据到飞书。")
async def push_confirm(
    body: PushConflictAction,
    request: Request,
    db: Session = Depends(get_db),
    client: Optional[FeishuClient] = Depends(_get_client_safe),
):
    effective_settings = _get_effective_settings(request, db)
    disabled = _check_sync_enabled(effective_settings)
    if disabled:
        return disabled

    if client is None:
        return error_response("CREDENTIALS_MISSING", "飞书凭证未配置", 400)

    from backend.app.models.sync_config import SyncConfig

    config = db.get(SyncConfig, body.config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    if body.action == "cancel":
        return success_response({"cancelled": True})

    # Execute push (overwrite or skip based on action)
    job = await push_records_to_feishu(
        db, client, config, None, triggered_by="api_push_confirm"
    )
    return success_response(SyncJobRead.model_validate(job).model_dump())


@router.post("/pull/preview", summary="预览拉取冲突", description="预览从飞书拉取数据时可能的冲突。")
async def pull_preview(
    body: PullRequest,
    request: Request,
    db: Session = Depends(get_db),
    client: Optional[FeishuClient] = Depends(_get_client_safe),
):
    effective_settings = _get_effective_settings(request, db)
    disabled = _check_sync_enabled(effective_settings)
    if disabled:
        return disabled

    if client is None:
        return error_response("CREDENTIALS_MISSING", "飞书凭证未配置", 400)

    from backend.app.models.sync_config import SyncConfig

    config = db.get(SyncConfig, body.config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    conflicts = await detect_pull_conflicts(db, client, config)
    if conflicts:
        return success_response(conflicts.model_dump())
    return success_response({"total_conflicts": 0, "conflicts": []})


@router.post("/pull/execute", summary="执行拉取", description="从飞书多维表格拉取数据到系统。")
async def pull_execute(
    body: ConflictResolution,
    request: Request,
    db: Session = Depends(get_db),
    client: Optional[FeishuClient] = Depends(_get_client_safe),
):
    effective_settings = _get_effective_settings(request, db)
    disabled = _check_sync_enabled(effective_settings)
    if disabled:
        return disabled

    if client is None:
        return error_response("CREDENTIALS_MISSING", "飞书凭证未配置", 400)

    from backend.app.models.sync_config import SyncConfig

    config = db.get(SyncConfig, body.config_id)
    if not config:
        return error_response("NOT_FOUND", "同步配置不存在", 404)

    async def pull_event_stream():
        job = await pull_records_from_feishu(
            db, client, config, body.strategy,
            body.per_record_choices, triggered_by="api_pull"
        )
        yield json.dumps({"type": "start", "total": job.total_records}) + "\n"
        yield json.dumps({
            "type": "complete",
            "job_id": str(job.id),
            "success_records": job.success_records,
            "failed_records": job.failed_records,
            "status": job.status,
        }) + "\n"

    return StreamingResponse(pull_event_stream(), media_type="application/x-ndjson")


@router.get("/history", summary="同步历史", description="查询同步任务历史记录，支持分页。")
async def sync_history(
    request: Request,
    config_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    effective_settings = _get_effective_settings(request, db)
    disabled = _check_sync_enabled(effective_settings)
    if disabled:
        return disabled

    jobs = get_sync_history(db, config_id=config_id, limit=limit, offset=offset)
    return success_response([SyncJobRead.model_validate(j).model_dump() for j in jobs])


@router.post("/{job_id}/retry", summary="重试失败的同步任务", description="重试一个失败的同步任务。")
async def retry_job(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    client: Optional[FeishuClient] = Depends(_get_client_safe),
):
    effective_settings = _get_effective_settings(request, db)
    disabled = _check_sync_enabled(effective_settings)
    if disabled:
        return disabled

    if client is None:
        return error_response("CREDENTIALS_MISSING", "飞书凭证未配置", 400)

    try:
        job = await retry_sync_job(db, client, job_id, triggered_by="api_retry")
    except ValueError as e:
        return error_response("RETRY_FAILED", str(e), 400)
    return success_response(SyncJobRead.model_validate(job).model_dump())
