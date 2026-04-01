from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.audit_log import AuditLogListResponse, AuditLogRead
from backend.app.api.v1.responses import success_response

# Error code prefix: AUDIT_xxx
router = APIRouter(prefix="/audit-logs", tags=["\u7cfb\u7edf\u7ba1\u7406"])


@router.get("", summary="\u67e5\u8be2\u5ba1\u8ba1\u65e5\u5fd7", description="\u5206\u9875\u67e5\u8be2\u7cfb\u7edf\u5ba1\u8ba1\u65e5\u5fd7\uff0c\u652f\u6301\u6309\u52a8\u4f5c\u7c7b\u578b\u548c\u65f6\u95f4\u8303\u56f4\u7b5b\u9009\u3002\u4ec5\u7ba1\u7406\u5458\u53ef\u8bbf\u95ee\u3002")
def list_audit_logs(
    db: Session = Depends(get_db),
    action: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List audit logs (read-only, admin only).

    Per D-08: No PUT/PATCH/DELETE endpoints. Audit logs are append-only.
    """
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter(AuditLog.action == action)
    if start_time:
        query = query.filter(AuditLog.created_at >= datetime.fromisoformat(start_time))
    if end_time:
        query = query.filter(AuditLog.created_at <= datetime.fromisoformat(end_time))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return success_response(
        AuditLogListResponse(
            items=[AuditLogRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        ).model_dump(mode="json")
    )
