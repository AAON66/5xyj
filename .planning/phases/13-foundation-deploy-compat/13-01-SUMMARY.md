---
phase: 13-foundation-deploy-compat
plan: 01
status: complete
completed: 2026-04-05
tasks_completed: 2/2
---

# Plan 13-01: Python 3.9 全面兼容性修复 + 依赖清理 — SUMMARY

## Tasks Completed

### Task 1: 移除所有 @dataclass(slots=True) 并验证 PEP 604 union 兼容性
**Commit:** e71808c — fix(13-01): remove @dataclass(slots=True) for Python 3.9 compat

- Replaced 35 occurrences of `slots=True` across 17 files (parsers, exporters, services, validators)
- Preserved `frozen=True` where originally combined
- Verified no PEP 604 union in `isinstance()` runtime calls
- All PEP 604 type annotations protected by `from __future__ import annotations`

### Task 2: 依赖版本锁定 + 未使用依赖清理 + requirements 合并
**Commit:** b008dae — chore(13-01): lock deps with upper bounds for Python 3.9 compat

- Added version upper bounds: fastapi<0.130, pydantic<2.13, pydantic-settings<2.12, pandas<3.0, sqlalchemy<2.1
- Added `xlrd>=2.0.0` (D-09: .xls support, was undeclared)
- Merged `PyJWT` and `pwdlib[bcrypt]` from requirements.server.txt
- Removed unused deps: `psycopg2-binary`, `asyncpg`, `loguru`
- Deleted `backend/requirements.server.txt` (merged into main file)

## Key Files

### Modified
- `backend/app/parsers/header_extraction.py`, `workbook_discovery.py`
- `backend/app/exporters/export_utils.py`
- `backend/app/mappings/manual_field_aliases.py`
- `backend/app/validators/non_detail_row_filter.py`
- `backend/app/services/` — 12 service files
- `backend/requirements.txt`

### Deleted
- `backend/requirements.server.txt`

## Verification

- `grep -rn "slots=True" backend/app/ --include="*.py"` returns 0 lines ✓
- `backend/requirements.txt` contains `fastapi>=0.115.0,<0.130.0` ✓
- `backend/requirements.txt` contains `xlrd>=2.0.0` ✓
- `backend/requirements.server.txt` deleted ✓

## Requirements Addressed

- INFRA-01: Python 3.9 运行环境适配

## Self-Check: PASSED

All acceptance criteria from plan met. Python 3.9 syntax compatibility achieved through slots removal + `from __future__ import annotations` protection of PEP 604 unions.
