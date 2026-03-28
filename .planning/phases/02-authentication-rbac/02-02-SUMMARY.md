---
phase: 02-authentication-rbac
plan: 02
subsystem: auth
tags: [rbac, user-management, crud, api-routes]
dependency_graph:
  requires: [02-01]
  provides: [user-crud-endpoints, system-wide-rbac]
  affects: [all-api-routes]
tech_stack:
  added: []
  patterns: [admin-only-endpoints, role-based-route-protection, StaticPool-for-test-sqlite]
key_files:
  created:
    - backend/app/schemas/users.py
    - backend/app/api/v1/users.py
  modified:
    - backend/app/services/user_service.py
    - backend/app/api/v1/router.py
    - tests/conftest.py
    - tests/test_users.py
decisions:
  - Used StaticPool for in-memory SQLite in tests to prevent cross-connection table-not-found errors
  - All business routes protected with require_role('admin', 'hr') instead of just require_authenticated_user
  - employees_router also now requires admin or HR role (was previously unprotected)
metrics:
  duration: 15min
  completed: 2026-03-28T13:30:48Z
  tasks: 2
  files: 6
---

# Phase 02 Plan 02: User Management CRUD and System-Wide RBAC Summary

Admin-only user CRUD endpoints (create, list, get, update, password-reset) with require_role enforced on all API routes for 3-role RBAC.

## What Was Done

### Task 1: User management CRUD endpoints (admin-only) [TDD]
- Created `UserCreate`, `UserUpdate`, `UserPasswordReset`, `UserRead` Pydantic schemas in `backend/app/schemas/users.py`
- Extended `user_service.py` with `create_user`, `update_user`, `reset_user_password`, `list_users`, `get_user_by_id` functions plus `UsernameExistsError`
- Created `backend/app/api/v1/users.py` with POST/GET/PUT endpoints for user management
- Registered `users_router` with `require_role("admin")` dependency
- Fixed conftest.py to use `StaticPool` for in-memory SQLite (prevents cross-connection table-not-found on commit/refresh)
- 13 tests covering: admin CRUD, duplicate username 409, HR 403, employee 403, disable+login rejection, password reset

### Task 2: Apply require_role to all API routes
- Replaced all `require_authenticated_user` with `require_role("admin", "hr")` on business routes
- Added role protection to `employees_router` (was previously unprotected)
- Auth and system routes remain public
- Removed `require_authenticated_user` import from router.py entirely

## Commits

| Task | Hash | Message |
|------|------|---------|
| 1 (RED) | b40dcba | test(02-02): add failing tests for user management CRUD endpoints |
| 1 (GREEN) | 19a7d55 | feat(02-02): add user management CRUD endpoints with admin-only access |
| 2 | 91c3402 | feat(02-02): apply require_role to all API routes for system-wide RBAC |

## Verification

- `python -m pytest tests/ -x -v` -- all 29 tests pass (16 auth + 13 users)
- `grep -c "require_role" backend/app/api/v1/router.py` returns 8
- `grep -c "require_authenticated_user" backend/app/api/v1/router.py` returns 0

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed SQLite in-memory StaticPool for test sessions**
- **Found during:** Task 1 GREEN phase
- **Issue:** In-memory SQLite with default connection pool creates a new database per connection. After `db.commit()`, SQLAlchemy expires attributes and the subsequent `db.refresh()` opens a new connection to an empty database, causing "no such table: users" errors.
- **Fix:** Added `poolclass=StaticPool` to conftest.py `db_engine` fixture, ensuring all connections share the same in-memory database.
- **Files modified:** tests/conftest.py
- **Commit:** 19a7d55

## Known Stubs

None -- all endpoints are fully wired with working service functions and database operations.

## Self-Check: PASSED

All 6 files verified present. All 3 commits verified in git log.
