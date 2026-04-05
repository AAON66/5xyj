---
phase: 13-foundation-deploy-compat
plan: 03
subsystem: backend-shared-modules
tags: [refactor, tech-debt, auth, consolidation]
requires: [13-01]
provides:
  - backend/app/mappings/regions.py::REGION_LABELS (single source of truth)
  - backend/app/utils/filename_utils.py::{FILENAME_NOISE, DATE_PATTERN, infer_company_name_from_filename}
  - backend/app/validators/constants.py::{ID_NUMBER_PATTERN, NON_MAINLAND_ID_NUMBER_PATTERN}
  - Explicit auth dependency on /employees/self-service/query
affects:
  - backend/app/services/region_detection_service.py
  - backend/app/services/import_service.py
  - backend/app/services/aggregate_service.py
  - backend/app/services/matching_service.py
  - backend/app/exporters/export_utils.py
  - backend/app/api/v1/employees.py
  - backend/tests/test_auth_api.py
  - backend/tests/test_employee_portal_api.py
tech-stack:
  added: []
  patterns: ["Single-definition constant modules imported by all consumers"]
key-files:
  created:
    - backend/app/mappings/regions.py
    - backend/app/utils/filename_utils.py
    - backend/app/validators/constants.py
  modified:
    - backend/app/services/region_detection_service.py
    - backend/app/services/import_service.py
    - backend/app/services/aggregate_service.py
    - backend/app/services/matching_service.py
    - backend/app/exporters/export_utils.py
    - backend/app/api/v1/employees.py
    - backend/tests/test_auth_api.py
    - backend/tests/test_employee_portal_api.py
decisions:
  - D-12: REGION_LABELS lives in mappings/regions.py (leaf module, avoids circular imports)
  - D-13: filename_utils.py owns FILENAME_NOISE, DATE_PATTERN and infer_company_name_from_filename (function hoisted from private _infer_... to public API)
  - D-14: ID number regex lives in validators/constants.py
  - D-16: self-service query endpoint carries explicit require_authenticated_user dependency for consistency
metrics:
  duration: "~15m coding + test runs"
  completed: 2026-04-05
requirements: [INFRA-02]
---

# Phase 13 Plan 03: 常量合并 + 自助查询端点认证修复 Summary

Consolidated three groups of duplicated constants (REGION_LABELS, FILENAME_NOISE/DATE_PATTERN/infer_company_name_from_filename, ID_NUMBER_PATTERN/NON_MAINLAND_ID_NUMBER_PATTERN) into shared leaf modules and added explicit authentication dependency on the employee self-service query endpoint with matching test updates.

## What Changed

### Task 1: Constant consolidation
Created three new shared leaf modules under `backend/app/`:
- `mappings/regions.py` — single `REGION_LABELS` dict (was duplicated in 4 files)
- `utils/filename_utils.py` — `FILENAME_NOISE`, `DATE_PATTERN`, and the renamed public
  `infer_company_name_from_filename` function (previously duplicated in
  `import_service.py` + `aggregate_service.py`)
- `validators/constants.py` — `ID_NUMBER_PATTERN`, `NON_MAINLAND_ID_NUMBER_PATTERN`
  (previously duplicated in `matching_service.py` + `export_utils.py`)

All existing call sites now import from these shared modules. The helper
`_infer_company_name_from_filename` was promoted to public API (no leading underscore)
and its business logic — including the `补缴1月入职2人` noise token — is implemented
exactly once. `import_service.py`'s previous copy contained mojibake (`??1???2?`)
because the file lacked proper encoding of that string; the consolidated copy uses
the canonical escape `\u8865\u7f341\u6708\u5165\u804c2\u4eba` from `aggregate_service.py`.

### Task 2: Explicit auth on self-service query
Added `_user=Depends(require_authenticated_user)` to the
`employee_self_service_query_endpoint` signature in `backend/app/api/v1/employees.py`.
The router already enforced `require_role("admin", "hr")`, but the endpoint now
declares the authentication dependency explicitly, eliminating the inconsistency
reviewer D-16 flagged.

Updated tests:
- `test_employee_self_service_query_remains_public` →
  `test_employee_self_service_query_requires_auth` (asserts 401 without token,
  404 with an admin bearer token).
- `test_old_query_endpoint_still_works` now builds the test context with
  `auth_enabled=True` and supplies an admin bearer token.
- `test_employee_master_api.py` uses `auth_enabled=False` globally, so
  `require_authenticated_user` returns the default user and no test changes
  were needed there.

Frontend already sends auth headers via `apiClient`, so no frontend change was
required.

## Deviations from Plan

### Rule 3 — Blocking: plan referenced `template_exporter.py`
- **Found during:** Task 1
- **Issue:** Plan listed `backend/app/exporters/template_exporter.py` as carrying the
  duplicate `REGION_LABELS`/`ID_NUMBER_PATTERN`. Actual duplicates live in
  `backend/app/exporters/export_utils.py`. `template_exporter.py` contains no such
  constants.
- **Fix:** Applied consolidation to `export_utils.py` instead. Net effect identical.
- **Files modified:** backend/app/exporters/export_utils.py
- **Commit:** 34e4e96

### Rule 1 — Bug: mojibake in import_service canonical string
- **Found during:** Task 1
- **Issue:** `import_service.py` had `cleaned.replace('??1???2?', '')` (corrupted).
  `aggregate_service.py` had the correct `\u8865\u7f341\u6708\u5165\u804c2\u4eba`
  (补缴1月入职2人).
- **Fix:** Shared `infer_company_name_from_filename` uses the correct string, so
  `import_service` now has working noise-stripping.
- **Commit:** 34e4e96

### Rule 3 — Blocking: test login helper pre-existing failure
- **Found during:** Task 2 testing
- **Issue:** The pre-existing `test_login_endpoint_returns_bearer_token_for_admin`
  test fails (401 instead of 200). The shared admin-seed DB persists across runs
  and login credentials mismatch — unrelated to this plan.
- **Fix:** Issued JWT tokens directly via `issue_access_token(...)` in the new/updated
  tests rather than routing through `POST /api/v1/auth/login`. This is the same
  technique already used in `test_employee_portal_api.py`.
- **Logged in:** `.planning/phases/13-foundation-deploy-compat/deferred-items.md`

## Authentication Gates
None — all changes were code-only refactoring and test updates.

## Testing
- `python3 -m pytest backend/tests/test_matching_service.py backend/tests/test_aggregate_api.py -q` → 28 passed
- `python3 -m pytest backend/tests/test_auth_api.py backend/tests/test_employee_portal_api.py -v` (excluding 3 pre-existing login-related failures) → 8 passed
- Targeted imports verified: `from backend.app.mappings.regions import REGION_LABELS`,
  `from backend.app.utils.filename_utils import ...`,
  `from backend.app.validators.constants import ...` all succeed.
- `grep -rn "^REGION_LABELS\s*[=:]" backend/app/` → only mappings/regions.py
- `grep -rn "^FILENAME_NOISE\s*=" backend/app/` → only utils/filename_utils.py
- `grep -rn "^ID_NUMBER_PATTERN\s*=" backend/app/` → only validators/constants.py
- `grep -rn "_infer_company_name_from_filename" backend/app/` → only the
  alias import in aggregate_service.py (the old underscored function name has been
  removed from the codebase).

## Deferred Issues
- `test_login_endpoint_returns_bearer_token_for_admin`,
  `test_login_endpoint_rejects_invalid_credentials`,
  `test_me_endpoint_returns_authenticated_user_profile` fail pre-existing due to
  admin seed DB state. Out of scope for this plan; should be fixed by resetting
  `.test_artifacts/auth_api/` between runs or fixing the seed strategy.

## Commits
- 34e4e96 — refactor(13-03): merge duplicate constants into shared modules
- ffba8a2 — fix(13-03): enforce explicit auth on /employees/self-service/query

## Self-Check: PASSED
- backend/app/mappings/regions.py — FOUND
- backend/app/utils/filename_utils.py — FOUND
- backend/app/validators/constants.py — FOUND
- commit 34e4e96 — FOUND
- commit ffba8a2 — FOUND
