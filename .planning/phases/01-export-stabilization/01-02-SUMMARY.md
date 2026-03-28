---
plan: 01-02
phase: 01-export-stabilization
status: completed
started: 2026-03-27T16:30:00Z
completed: 2026-03-27T17:15:00Z
---

# Summary: Fix Tool Template Alignment + Dual Export Verification

## What Was Built

Decoupled `_tool_row_values` from `_salary_row_values` and rewrote it as an independent 42-position explicit mapping with runtime length guard. Added comprehensive alignment tests including real workbook verification.

## Key Files

### Created
- `backend/tests/test_tool_export_alignment.py` — 7 alignment tests

### Modified
- `backend/app/exporters/tool_exporter.py` — Independent `_tool_row_values` with runtime assert

## Task Results

| Task | Description | Status | Tests |
|------|-------------|--------|-------|
| 1 | Decouple and fix _tool_row_values + alignment tests | Completed | 7/7 passed |

## Test Results

- **Tool Alignment**: 7/7 passed (length, field position, real workbook, dual export, housing edge case, multi-region, Salary regression)
- **Salary Regression**: 6/6 passed (no regression from Tool changes)
- **API Compatibility**: 5/5 passed
- **Total**: 18/18 all green

## Key Changes

1. `_tool_row_values` no longer calls `_salary_row_values` — fully independent
2. Each of the 42 values is computed and placed at an explicit position matching `TOOL_HEADERS`
3. Runtime `assert len(values) == len(TOOL_HEADERS)` prevents future misalignment
4. Test 3 validates against the real template workbook layout, not just the constant

## Deviations

The original `_tool_row_values` already produced 42 values (length was coincidentally correct), but the internal structure was fragile due to `*salary_values[2:]` splice. The rewrite makes each position explicit and auditable.

## Self-Check: PASSED
