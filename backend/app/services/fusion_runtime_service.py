from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from backend.app.models.fusion_rule import FusionRule
from backend.app.models.normalized_record import NormalizedRecord
from backend.app.schemas.fusion_inputs import FusionBurdenDiagnostics, FusionBurdenRow
from backend.app.services.fusion_rule_service import get_active_fusion_rules

FUSION_OVERRIDE_PAYLOAD_KEY = 'fusion_overrides'
FUSION_OVERRIDE_SOURCES_PAYLOAD_KEY = 'fusion_override_sources'
FUSION_OVERRIDE_MATCH_KEY_PAYLOAD_KEY = 'fusion_override_match_key'
FUSION_FIELD_NAMES = ('personal_social_burden', 'personal_housing_burden')


@dataclass
class FusionRuntimeOverlay:
    overrides: dict[str, dict[str, Decimal]]
    sources: dict[str, list[dict[str, object]]]
    messages: list[str]


def build_fusion_runtime_overlay(
    db: Session,
    records: Iterable[NormalizedRecord],
    *,
    burden_rows: Optional[Iterable[FusionBurdenRow]] = None,
    burden_diagnostics: Optional[FusionBurdenDiagnostics] = None,
    fusion_rule_ids: Optional[list[str]] = None,
) -> FusionRuntimeOverlay:
    normalized_records = list(records)
    overrides: dict[str, dict[str, Decimal]] = {}
    sources: dict[str, list[dict[str, object]]] = {}
    messages = list((burden_diagnostics or FusionBurdenDiagnostics()).messages)
    record_keys = _collect_record_keys(normalized_records)

    unmatched_burden_rows = 0
    for row in burden_rows or []:
        key = _burden_override_key(row)
        if key is None:
            continue
        values = {
            field_name: Decimal(str(value))
            for field_name in FUSION_FIELD_NAMES
            if (value := getattr(row, field_name)) is not None
        }
        if not values:
            continue
        if key not in record_keys:
            unmatched_burden_rows += 1
            continue
        target = overrides.setdefault(key, {})
        target.update(values)
        key_sources = sources.setdefault(key, [])
        key_sources.extend(
            {
                'source_kind': row.source_kind,
                'source_ref': row.source_ref,
                'field_name': field_name,
                'value': str(value),
            }
            for field_name, value in values.items()
        )

    if unmatched_burden_rows:
        messages.append(f'承担额来源中有 {unmatched_burden_rows} 条记录未命中当前聚合员工。')

    selected_rules = _resolve_selected_rules(db, fusion_rule_ids)
    unmatched_rules = 0
    for rule in selected_rules:
        key = _rule_override_key(rule)
        if key is None:
            continue
        if key not in record_keys:
            unmatched_rules += 1
            continue
        overrides.setdefault(key, {})[rule.field_name] = Decimal(str(rule.override_value))
        sources.setdefault(key, []).append(
            {
                'source_kind': 'rule',
                'rule_id': rule.id,
                'scope_type': rule.scope_type,
                'scope_value': rule.scope_value,
                'field_name': rule.field_name,
                'value': str(rule.override_value),
            }
        )

    if unmatched_rules:
        messages.append(f'已跳过 {unmatched_rules} 条未命中当前聚合员工的特殊规则。')

    return FusionRuntimeOverlay(overrides=overrides, sources=sources, messages=messages)


def build_fusion_overrides(
    db: Session,
    records: Iterable[NormalizedRecord],
    *,
    burden_rows: Optional[Iterable[FusionBurdenRow]] = None,
    burden_diagnostics: Optional[FusionBurdenDiagnostics] = None,
    fusion_rule_ids: Optional[list[str]] = None,
) -> dict[str, dict[str, Decimal]]:
    return build_fusion_runtime_overlay(
        db,
        records,
        burden_rows=burden_rows,
        burden_diagnostics=burden_diagnostics,
        fusion_rule_ids=fusion_rule_ids,
    ).overrides


def apply_fusion_overrides(
    record: NormalizedRecord,
    overrides: dict[str, dict[str, Decimal]],
    *,
    sources: Optional[dict[str, list[dict[str, object]]]] = None,
) -> dict[str, Decimal]:
    payload = dict(record.raw_payload or {})
    resolved_key = next((candidate for candidate in _record_override_keys(record) if candidate in overrides), None)
    if resolved_key is None:
        payload.pop(FUSION_OVERRIDE_PAYLOAD_KEY, None)
        payload.pop(FUSION_OVERRIDE_SOURCES_PAYLOAD_KEY, None)
        payload.pop(FUSION_OVERRIDE_MATCH_KEY_PAYLOAD_KEY, None)
        record.raw_payload = payload or None
        return {}

    values = overrides[resolved_key]
    payload[FUSION_OVERRIDE_PAYLOAD_KEY] = {field_name: str(value) for field_name, value in values.items()}
    payload[FUSION_OVERRIDE_MATCH_KEY_PAYLOAD_KEY] = _deserialize_override_key(resolved_key)
    if sources and resolved_key in sources:
        payload[FUSION_OVERRIDE_SOURCES_PAYLOAD_KEY] = deepcopy(sources[resolved_key])
    else:
        payload.pop(FUSION_OVERRIDE_SOURCES_PAYLOAD_KEY, None)
    record.raw_payload = payload
    return values


def has_active_or_selected_fusion_rules(db: Session, fusion_rule_ids: Optional[list[str]]) -> bool:
    if fusion_rule_ids is not None:
        return bool(fusion_rule_ids)
    return bool(get_active_fusion_rules(db))


def _resolve_selected_rules(db: Session, fusion_rule_ids: Optional[list[str]]) -> list[FusionRule]:
    if fusion_rule_ids is None:
        return get_active_fusion_rules(db)

    normalized_ids = [rule_id.strip() for rule_id in fusion_rule_ids if rule_id and rule_id.strip()]
    if not normalized_ids:
        return []

    return (
        db.query(FusionRule)
        .filter(FusionRule.id.in_(normalized_ids), FusionRule.is_active.is_(True))
        .order_by(FusionRule.created_at.desc())
        .all()
    )


def _collect_record_keys(records: list[NormalizedRecord]) -> set[str]:
    keys: set[str] = set()
    for record in records:
        keys.update(_record_override_keys(record))
    return keys


def _record_override_keys(record: NormalizedRecord) -> list[str]:
    keys: list[str] = []
    employee_id = _normalize_employee_id(record.employee_id)
    if employee_id is not None:
        keys.append(_make_override_key('employee_id', employee_id))
    id_number = _normalize_id_number(record.id_number)
    if id_number is not None:
        keys.append(_make_override_key('id_number', id_number))
    return keys


def _burden_override_key(row: FusionBurdenRow) -> Optional[str]:
    employee_id = _normalize_employee_id(row.employee_id)
    if employee_id is not None:
        return _make_override_key('employee_id', employee_id)
    id_number = _normalize_id_number(row.id_number)
    if id_number is not None:
        return _make_override_key('id_number', id_number)
    return None


def _rule_override_key(rule: FusionRule) -> Optional[str]:
    if rule.scope_type == 'employee_id':
        normalized_value = _normalize_employee_id(rule.scope_value)
    else:
        normalized_value = _normalize_id_number(rule.scope_value)
    if normalized_value is None:
        return None
    return _make_override_key(rule.scope_type, normalized_value)


def _normalize_employee_id(value: object) -> str | None:
    text = _normalize_text(value)
    if text is None:
        return None
    return text.upper()


def _normalize_id_number(value: object) -> str | None:
    text = _normalize_text(value)
    if text is None:
        return None
    compact = text.replace(' ', '').upper()
    return compact or None


def _normalize_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _make_override_key(scope_type: str, scope_value: str) -> str:
    return f'{scope_type}|{scope_value}'


def _deserialize_override_key(key: str) -> dict[str, str]:
    scope_type, _, scope_value = key.partition('|')
    return {'scope_type': scope_type, 'scope_value': scope_value}
