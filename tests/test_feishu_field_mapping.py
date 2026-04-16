"""Tests for FeishuFieldInfo ui_type extension and suggest-mapping logic."""

from __future__ import annotations

import pytest

from backend.app.schemas.feishu import FeishuFieldInfo


# --- FeishuFieldInfo schema tests ---


def test_feishu_field_info_has_ui_type():
    """FeishuFieldInfo should accept ui_type parameter."""
    info = FeishuFieldInfo(
        field_id="fld1",
        field_name="姓名",
        field_type=1,
        ui_type="Text",
    )
    assert info.ui_type == "Text"


def test_feishu_field_info_ui_type_default_none():
    """FeishuFieldInfo ui_type should default to None when not provided."""
    info = FeishuFieldInfo(
        field_id="fld1",
        field_name="姓名",
        field_type=1,
    )
    assert info.ui_type is None


# --- suggest_field_mapping function tests ---


def test_suggest_mapping_chinese_name():
    """Chinese field name '姓名' should map to person_name with high confidence."""
    from backend.app.api.v1.feishu_settings import suggest_field_mapping

    result = suggest_field_mapping([{"field_name": "姓名", "field_id": "fld1"}])
    assert len(result["suggestions"]) == 1
    suggestion = result["suggestions"][0]
    assert suggestion["canonical_field"] == "person_name"
    assert suggestion["confidence"] >= 0.9
    assert "fld1" not in result["unmatched"]


def test_suggest_mapping_english_key():
    """English key 'person_name' should match via exact key fallback."""
    from backend.app.api.v1.feishu_settings import suggest_field_mapping
    from backend.app.mappings.manual_field_aliases import CANONICAL_FIELDS

    system_fields = list(CANONICAL_FIELDS)
    result = suggest_field_mapping(
        [{"field_name": "person_name", "field_id": "fld2"}],
        system_fields=system_fields,
    )
    assert len(result["suggestions"]) == 1
    suggestion = result["suggestions"][0]
    assert suggestion["canonical_field"] == "person_name"
    assert "fld2" not in result["unmatched"]


def test_suggest_mapping_unmatched():
    """Unrecognized field should appear in unmatched list."""
    from backend.app.api.v1.feishu_settings import suggest_field_mapping

    result = suggest_field_mapping([{"field_name": "无关字段ABC", "field_id": "fld3"}])
    assert len(result["suggestions"]) == 0
    assert "fld3" in result["unmatched"]


def test_suggest_mapping_pension_company():
    """Insurance field '养老保险(单位)' should map to pension_company."""
    from backend.app.api.v1.feishu_settings import suggest_field_mapping

    result = suggest_field_mapping([{"field_name": "养老保险(单位)", "field_id": "fld4"}])
    assert len(result["suggestions"]) == 1
    suggestion = result["suggestions"][0]
    assert suggestion["canonical_field"] == "pension_company"
