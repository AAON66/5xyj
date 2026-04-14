from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.v1.responses import error_response, success_response
from backend.app.core.auth import AuthUser
from backend.app.dependencies import get_db, require_authenticated_user
from backend.app.schemas.fusion_rules import FusionRuleCreate, FusionRuleFieldName, FusionRuleRead, FusionRuleUpdate
from backend.app.services.fusion_rule_service import (
    create_fusion_rule,
    delete_fusion_rule,
    get_fusion_rule,
    list_fusion_rules,
    update_fusion_rule,
)


router = APIRouter(prefix="/fusion-rules", tags=["融合规则"])


@router.get("", summary="获取融合规则列表", description="返回可复用的特殊规则列表。")
def list_fusion_rules_endpoint(
    is_active: bool | None = Query(default=None),
    field_name: FusionRuleFieldName | None = Query(default=None),
    db: Session = Depends(get_db),
):
    payload = [FusionRuleRead.model_validate(item).model_dump(mode="json") for item in list_fusion_rules(
        db,
        is_active=is_active,
        field_name=field_name,
    )]
    return success_response(payload)


@router.post("", summary="创建融合规则", description="创建新的特殊覆盖规则。")
def create_fusion_rule_endpoint(
    body: FusionRuleCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_authenticated_user),
):
    rule = create_fusion_rule(
        db,
        scope_type=body.scope_type,
        scope_value=body.scope_value,
        field_name=body.field_name,
        override_value=body.override_value,
        note=body.note,
        created_by=current_user.username,
    )
    return success_response(FusionRuleRead.model_validate(rule).model_dump(mode="json"), status_code=201)


@router.put("/{rule_id}", summary="更新融合规则", description="更新指定的特殊覆盖规则。")
def update_fusion_rule_endpoint(
    rule_id: str,
    body: FusionRuleUpdate,
    db: Session = Depends(get_db),
):
    updated = update_fusion_rule(db, rule_id, **body.model_dump(exclude_unset=True))
    if updated is None:
        return error_response("NOT_FOUND", "融合规则不存在", 404)
    return success_response(FusionRuleRead.model_validate(updated).model_dump(mode="json"))


@router.delete("/{rule_id}", summary="删除融合规则", description="删除指定的特殊覆盖规则。")
def delete_fusion_rule_endpoint(
    rule_id: str,
    db: Session = Depends(get_db),
):
    deleted = delete_fusion_rule(db, rule_id)
    if not deleted:
        return error_response("NOT_FOUND", "融合规则不存在", 404)
    return success_response({"deleted": True})
