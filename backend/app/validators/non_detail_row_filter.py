from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

NON_DETAIL_TOKENS = {
    "\u5408\u8ba1": "summary_total",
    "\u5c0f\u8ba1": "summary_subtotal",
    "\u5728\u804c\u4eba\u5458": "group_header",
    "\u9000\u4f11\u4eba\u5458": "group_header",
    "\u5bb6\u5c5e\u7edf\u7b79\u4eba\u5458": "group_header",
}
PLACEHOLDER_VALUES = {"", "-", "--", "\u2014\u2014", "none", "null", "\u7a7a\u767d", "(\u7a7a\u767d)", "\uff08\u7a7a\u767d\uff09"}
HEADER_ROW_TOKENS = {
    "\u59d3\u540d",
    "\u5458\u5de5\u59d3\u540d",
    "\u8eab\u4efd\u8bc1\u53f7",
    "\u8eab\u4efd\u8bc1\u53f7\u7801",
    "\u8bc1\u4ef6\u53f7",
    "\u8bc1\u4ef6\u53f7\u7801",
    "\u5de5\u53f7",
}


@dataclass
class RowFilterDecision:
    row_number: int
    keep: bool
    reason: str
    first_value: str
    normalized_values: list[str]


@dataclass
class FilteredRow:
    row_number: int
    values: list[object]


@dataclass
class FilteredRowsResult:
    kept_rows: list[FilteredRow]
    filtered_rows: list[RowFilterDecision]


def classify_row(values: Iterable[object], row_number: int) -> RowFilterDecision:
    normalized_values = [_normalize(value) for value in values]
    non_empty_values = [value for value in normalized_values if value and value.lower() not in PLACEHOLDER_VALUES]

    if not non_empty_values:
        return RowFilterDecision(
            row_number=row_number,
            keep=False,
            reason="blank_row",
            first_value="",
            normalized_values=normalized_values,
        )

    first_value = non_empty_values[0]
    exact_reason = _match_non_detail_token(first_value)
    if exact_reason:
        return RowFilterDecision(
            row_number=row_number,
            keep=False,
            reason=exact_reason,
            first_value=first_value,
            normalized_values=normalized_values,
        )

    if _looks_like_header_row(non_empty_values):
        return RowFilterDecision(
            row_number=row_number,
            keep=False,
            reason="header_row",
            first_value=first_value,
            normalized_values=normalized_values,
        )

    if _is_text_only_group_row(non_empty_values):
        return RowFilterDecision(
            row_number=row_number,
            keep=False,
            reason="group_header",
            first_value=first_value,
            normalized_values=normalized_values,
        )

    return RowFilterDecision(
        row_number=row_number,
        keep=True,
        reason="detail_row",
        first_value=first_value,
        normalized_values=normalized_values,
    )


def filter_candidate_rows(rows: Iterable[tuple[int, list[object]]]) -> FilteredRowsResult:
    kept_rows: list[FilteredRow] = []
    filtered_rows: list[RowFilterDecision] = []

    for row_number, values in rows:
        decision = classify_row(values, row_number=row_number)
        if decision.keep:
            kept_rows.append(FilteredRow(row_number=row_number, values=values))
        else:
            filtered_rows.append(decision)

    return FilteredRowsResult(kept_rows=kept_rows, filtered_rows=filtered_rows)


def _match_non_detail_token(value: str) -> Optional[str]:
    stripped = value.strip()
    if stripped in NON_DETAIL_TOKENS:
        return NON_DETAIL_TOKENS[stripped]
    if stripped.startswith("\u5408\u8ba1") or stripped.endswith("\u5408\u8ba1"):
        return "summary_total"
    if stripped.startswith("\u5c0f\u8ba1") or stripped.endswith("\u5c0f\u8ba1"):
        return "summary_subtotal"
    return None


def _is_text_only_group_row(non_empty_values: list[str]) -> bool:
    first_value = non_empty_values[0]
    if first_value in {
        "\u5728\u804c\u4eba\u5458",
        "\u9000\u4f11\u4eba\u5458",
        "\u5bb6\u5c5e\u7edf\u7b79\u4eba\u5458",
    }:
        return True
    if len(non_empty_values) > 3:
        return False
    if any(_looks_numeric(value) for value in non_empty_values[1:]):
        return False
    return first_value in NON_DETAIL_TOKENS or first_value.endswith("\u4eba\u5458")


def _looks_like_header_row(non_empty_values: list[str]) -> bool:
    header_like = [value for value in non_empty_values if value in HEADER_ROW_TOKENS]
    if not header_like:
        return False
    if len(header_like) == len(non_empty_values):
        return True
    if len(non_empty_values) <= 4 and len(header_like) >= 2 and not any(_looks_numeric(value) for value in non_empty_values):
        return True
    return False


def _normalize(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _looks_numeric(value: str) -> bool:
    candidate = value.replace(",", "").replace("%", "")
    if not candidate:
        return False
    try:
        float(candidate)
        return True
    except ValueError:
        return False
