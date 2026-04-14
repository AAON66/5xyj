from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.fusion_rule import FusionRule


ALLOWED_SCOPE_TYPES = {"employee_id", "id_number"}
ALLOWED_FIELD_NAMES = {"personal_social_burden", "personal_housing_burden"}


def _validate_scope_type(value: str) -> str:
    normalized = value.strip()
    if normalized not in ALLOWED_SCOPE_TYPES:
        raise ValueError(f"Unsupported fusion rule scope_type: {value}")
    return normalized


def _validate_field_name(value: str) -> str:
    normalized = value.strip()
    if normalized not in ALLOWED_FIELD_NAMES:
        raise ValueError(f"Unsupported fusion rule field_name: {value}")
    return normalized


def _validate_scope_value(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Fusion rule scope_value cannot be empty.")
    return normalized


def list_fusion_rules(
    db: Session,
    *,
    is_active: bool | None = None,
    field_name: str | None = None,
) -> list[FusionRule]:
    query = db.query(FusionRule)
    if is_active is not None:
        query = query.filter(FusionRule.is_active.is_(is_active))
    if field_name is not None:
        query = query.filter(FusionRule.field_name == _validate_field_name(field_name))
    return query.order_by(FusionRule.created_at.desc()).all()


def get_fusion_rule(db: Session, rule_id: str) -> Optional[FusionRule]:
    return db.query(FusionRule).filter(FusionRule.id == rule_id).first()


def create_fusion_rule(
    db: Session,
    *,
    scope_type: str,
    scope_value: str,
    field_name: str,
    override_value: Decimal,
    note: str | None,
    created_by: str | None,
) -> FusionRule:
    rule = FusionRule(
        scope_type=_validate_scope_type(scope_type),
        scope_value=_validate_scope_value(scope_value),
        field_name=_validate_field_name(field_name),
        override_value=Decimal(str(override_value)),
        note=note.strip() if isinstance(note, str) and note.strip() else None,
        is_active=True,
        created_by=created_by.strip() if isinstance(created_by, str) and created_by.strip() else None,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_fusion_rule(db: Session, rule_id: str, **changes) -> Optional[FusionRule]:
    rule = get_fusion_rule(db, rule_id)
    if rule is None:
        return None

    if "scope_type" in changes and changes["scope_type"] is not None:
        rule.scope_type = _validate_scope_type(changes["scope_type"])
    if "scope_value" in changes and changes["scope_value"] is not None:
        rule.scope_value = _validate_scope_value(changes["scope_value"])
    if "field_name" in changes and changes["field_name"] is not None:
        rule.field_name = _validate_field_name(changes["field_name"])
    if "override_value" in changes and changes["override_value"] is not None:
        rule.override_value = Decimal(str(changes["override_value"]))
    if "note" in changes:
        note = changes["note"]
        rule.note = note.strip() if isinstance(note, str) and note.strip() else None
    if "is_active" in changes and changes["is_active"] is not None:
        rule.is_active = bool(changes["is_active"])

    db.commit()
    db.refresh(rule)
    return rule


def delete_fusion_rule(db: Session, rule_id: str) -> bool:
    rule = get_fusion_rule(db, rule_id)
    if rule is None:
        return False
    db.delete(rule)
    db.commit()
    return True


def get_active_fusion_rules(db: Session) -> list[FusionRule]:
    return list_fusion_rules(db, is_active=True)
