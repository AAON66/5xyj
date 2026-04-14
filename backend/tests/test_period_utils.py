from __future__ import annotations

from datetime import date, datetime

from backend.app.utils.period_utils import (
    coalesce_billing_period,
    infer_billing_period_from_filename,
    normalize_billing_period,
    normalize_period_boundary,
)


def test_normalize_billing_period_accepts_common_formats() -> None:
    assert normalize_billing_period("202603") == "2026-03"
    assert normalize_billing_period("2026-03") == "2026-03"
    assert normalize_billing_period("2026年03月") == "2026-03"
    assert normalize_billing_period("2026年-03月") == "2026-03"
    assert normalize_billing_period("2026-03-01T00:00:00") == "2026-03"
    assert normalize_billing_period(date(2026, 3, 1)) == "2026-03"
    assert normalize_billing_period(datetime(2026, 3, 1, 9, 30, 0)) == "2026-03"


def test_normalize_billing_period_rejects_invalid_values() -> None:
    assert normalize_billing_period("175.00") is None
    assert normalize_billing_period("备注") is None
    assert normalize_billing_period("离职原因") is None


def test_normalize_period_boundary_accepts_common_formats() -> None:
    assert normalize_period_boundary("20260301") == "2026-03-01"
    assert normalize_period_boundary("2026-03-01T00:00:00") == "2026-03-01"
    assert normalize_period_boundary("2026年03月01日") == "2026-03-01"


def test_period_helpers_can_fall_back_to_filename() -> None:
    assert infer_billing_period_from_filename("杭州聚变202603公积金账单.xlsx") == "2026-03"
    assert coalesce_billing_period("175.00", "杭州聚变202603公积金账单.xlsx") == "2026-03"
