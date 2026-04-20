---
phase: 22-oauth
plan: "01"
subsystem: backend/auth
tags: [feishu, oauth, binding, matching]
dependency_graph:
  requires: []
  provides: [feishu-oauth-3level-matching, confirm-bind-api, bind-unbind-api, feishu-bound-status]
  affects: [frontend-oauth-flow, frontend-bind-ui]
tech_stack:
  added: []
  patterns: [3-level-matching, pending-token-jwt, employee-id-masking]
key_files:
  created: []
  modified:
    - backend/app/services/feishu_oauth_service.py
    - backend/app/api/v1/feishu_auth.py
    - backend/app/api/v1/auth.py
    - backend/app/services/user_service.py
    - backend/app/schemas/auth.py
    - tests/test_feishu_auth.py
    - tests/conftest.py
decisions:
  - "pending_token uses PyJWT with 5-minute expiry and purpose=confirm_bind claim"
  - "employee_id masked as ****XXXX (last 4 chars visible)"
  - "bind state uses bind: prefix in OAuth state to differentiate from login flow"
  - "/me endpoint extended with feishu_bound for all user roles (not just admin/hr)"
metrics:
  duration: "~9 minutes"
  completed: "2026-04-16"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 7
---

# Phase 22 Plan 01: Feishu OAuth Auto-Matching Backend Summary

Three-level OAuth matching (matched/auto_bound/pending_candidates/new_user) with confirm-bind, bind/unbind endpoints, and feishu_bound status in /me.

## What Was Done

### Task 1: Three-level matching + confirm-bind

Refactored `exchange_code_for_user` to implement 4-status flow:
- **Layer 1 (matched):** open_id exact match to existing User -- preserves existing role
- **Layer 2 (auto_bound):** Feishu name uniquely matches one active EmployeeMaster -- creates/finds user, binds feishu_open_id
- **Layer 3 (pending_candidates):** Multiple name matches -- returns candidate list with masked employee_id (****XXXX), issues 5-minute pending JWT
- **Layer 4 (new_user):** No match at all -- creates new employee-role user

Added `confirm-bind` endpoint that validates the pending JWT, checks open_id uniqueness (409 on conflict), and completes the binding.

Added `bind_feishu` and `unbind_feishu` methods to `user_service.py`.

### Task 2: bind/unbind endpoints + feishu_bound

- `GET /auth/feishu/bind-authorize-url` -- requires JWT auth, returns Feishu authorize URL with bind-prefixed state
- `POST /auth/feishu/bind-callback` -- requires JWT auth, validates state cookie, exchanges code, checks open_id uniqueness, binds to current user
- `POST /auth/feishu/unbind` -- requires JWT auth, clears feishu_open_id and feishu_union_id
- `/me` endpoint extended with `feishu_bound: bool` field for all user roles

## Test Results

28 tests pass (excluding 6 pre-existing failures in TestFeatureFlags and TestSettingsEndpoints unrelated to this plan):
- TestOAuthAutoBinding: 4 tests (matched, auto_bound, new_user, role enforcement)
- TestOAuthPendingCandidates: 1 test (multiple match + masking)
- TestConfirmBind: 4 tests (success, invalid token, expired token, conflict)
- TestFeishuBind: 7 tests (auth requirements, bind flow, unbind, /me status)
- Existing tests: 12 tests continue passing

Broader suite: 211 passed, 2 pre-existing failures in test_data_management.py (unrelated).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] /me endpoint simplified for all roles**
- **Found during:** Task 2
- **Issue:** Original /me had separate code paths for admin/hr vs employee, only looking up DB record for admin/hr. This meant employee users would never get feishu_bound status.
- **Fix:** Unified to always look up DB record first, falling back to default payload only when no DB record exists.
- **Files modified:** backend/app/api/v1/auth.py

## Threat Mitigations Applied

| Threat | Mitigation |
|--------|------------|
| T-22-01 (Spoofing confirm-bind) | Pending JWT with 5-min expiry + purpose=confirm_bind claim |
| T-22-02 (EoP bind-callback) | require_authenticated_user dependency injection |
| T-22-03 (Info disclosure candidates) | employee_id masked to ****XXXX |
| T-22-04 (Tampering employee_master_id) | Validated against EmployeeMaster table |
| T-22-05 (OAuth state spoofing) | HMAC-signed state cookie (existing) + bind: prefix |
| T-22-06 (open_id uniqueness) | Explicit check before bind, 409 on conflict |
| T-22-07 (Role escalation) | New users always employee, existing users keep role |

## Known Stubs

None -- all endpoints are fully wired to database operations.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 RED | b8303b4 | Failing tests for 3-level matching + confirm-bind |
| 1 GREEN | 803236d | Implement 3-level matching + confirm-bind |
| 2 RED | 9f946a9 | Failing tests for bind/unbind/me |
| 2 GREEN | b8a3f79 | Implement bind/unbind + feishu_bound in /me |

## Self-Check: PASSED

All 7 files verified present. All 4 commits verified in git log.
