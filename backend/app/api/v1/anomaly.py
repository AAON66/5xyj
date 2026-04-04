from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import paginated_response, success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_role
from backend.app.schemas.anomaly import (
    AnomalyDetectRequest,
    AnomalyRecordRead,
    AnomalyStatusUpdateRequest,
)
from backend.app.services.anomaly_detection_service import (
    batch_update_anomaly_status,
    detect_anomalies,
    list_anomalies,
)
from backend.app.services.audit_service import log_audit

# Error code prefix: ANM_xxx
router = APIRouter(prefix='/anomalies', tags=['数据质量'])


def _serialize_anomaly(record) -> dict:
    """Convert AnomalyRecord to dict matching AnomalyRecordRead."""
    return AnomalyRecordRead(
        id=record.id,
        employee_identifier=record.employee_identifier,
        person_name=record.person_name,
        company_name=record.company_name,
        region=record.region,
        left_period=record.left_period,
        right_period=record.right_period,
        field_name=record.field_name,
        left_value=str(record.left_value) if record.left_value is not None else None,
        right_value=str(record.right_value) if record.right_value is not None else None,
        change_percent=record.change_percent,
        threshold_percent=record.threshold_percent,
        status=record.status,
        reviewed_by=record.reviewed_by,
        reviewed_at=record.reviewed_at,
        created_at=record.created_at,
    ).model_dump(mode='json')


@router.post(
    '/detect',
    summary="运行异常检测",
    description="对比两个账期的社保数据，检测缴费基数和金额异常变动。",
)
def detect_anomalies_endpoint(
    request_body: AnomalyDetectRequest,
    db: Session = Depends(get_db),
):
    anomalies = detect_anomalies(
        db,
        request_body.left_period,
        request_body.right_period,
        thresholds=request_body.thresholds or None,
    )
    data = [_serialize_anomaly(a) for a in anomalies]
    return success_response(data, message=f"检测完成，发现 {len(anomalies)} 条异常记录。")


@router.get(
    '',
    summary="查询异常记录",
    description="分页查询异常检测结果，支持按状态和险种筛选。",
)
def list_anomalies_endpoint(
    left_period: Optional[str] = Query(None, description="左侧账期"),
    right_period: Optional[str] = Query(None, description="右侧账期"),
    status: Optional[str] = Query(None, description="状态筛选"),
    field_name: Optional[str] = Query(None, description="险种字段筛选"),
    page: int = Query(0, ge=0, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
):
    items, total = list_anomalies(
        db,
        left_period=left_period,
        right_period=right_period,
        status=status,
        field_name=field_name,
        page=page,
        page_size=page_size,
    )
    data = [_serialize_anomaly(a) for a in items]
    return paginated_response(data, total, page, page_size)


@router.patch(
    '/status',
    summary="批量更新异常状态",
    description="批量将异常记录标记为已确认或已排除。",
)
def batch_update_status_endpoint(
    request_body: AnomalyStatusUpdateRequest,
    user: AuthUser = Depends(require_role("admin", "hr")),
    db: Session = Depends(get_db),
):
    count = batch_update_anomaly_status(
        db,
        request_body.anomaly_ids,
        request_body.status,
        user.username,
    )
    log_audit(
        db,
        "anomaly_status_update",
        user.username,
        user.role,
        detail={
            "anomaly_ids": request_body.anomaly_ids,
            "new_status": request_body.status,
            "updated_count": count,
        },
        resource_type="anomaly_record",
    )
    return success_response({"updated_count": count}, message=f"已更新 {count} 条异常记录状态。")
