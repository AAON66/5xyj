---
phase: 02-authentication-rbac
plan: 01
subsystem: auth
tags: [jwt, pyjwt, bcrypt, pwdlib, rbac, rate-limiting, sqlalchemy]

requires:
  - phase: 01-export-stabilization
    provides: "Stable backend with SQLAlchemy models, FastAPI app structure"
provides:
  - "PyJWT-based token issue/verify (HS256)"
  - "User SQLAlchemy model with bcrypt passwords"
  - "Employee triple-factor verification endpoint with rate limiting"
  - "require_role() RBAC dependency factory supporting admin/hr/employee"
  - "Auto-seeded default admin on first boot"
  - "Auth test infrastructure (conftest + 16 tests)"
affects: [02-authentication-rbac, frontend-auth, api-protection]

tech-stack:
  added: [PyJWT 2.12, pwdlib 0.3 with bcrypt]
  patterns: [dependency-factory RBAC, in-memory rate limiting, DB-stored passwords]

key-files:
  created:
    - backend/app/models/user.py
    - backend/app/services/user_service.py
    - backend/app/services/rate_limiter.py
    - tests/conftest.py
    - tests/test_auth.py
  modified:
    - backend/app/core/auth.py
    - backend/app/core/config.py
    - backend/app/schemas/auth.py
    - backend/app/api/v1/auth.py
    - backend/app/dependencies.py
    - backend/app/bootstrap.py
    - backend/app/models/__init__.py
    - backend/requirements.server.txt

key-decisions:
  - "Used pwdlib with BcryptHasher instead of PasswordHash.recommended() (which requires argon2)"
  - "Kept admin_login_username/password config fields for backward compat during transition"
  - "Rate limiter keys on employee_id, not IP address"

patterns-established:
  - "require_role(*roles) dependency factory pattern for endpoint RBAC"
  - "DB-backed user authentication replacing config-based credentials"
  - "Test infrastructure with in-memory SQLite and dependency overrides"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03, AUTH-06]

duration: 7min
completed: 2026-03-28
---

# Phase 02 Plan 01: Backend Auth Core Summary

**PyJWT auth with bcrypt passwords, employee triple-factor verification with rate limiting, and require_role RBAC dependency factory**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-28T13:05:07Z
- **Completed:** 2026-03-28T13:12:01Z
- **Tasks:** 1
- **Files modified:** 13

## Accomplishments
- Replaced custom HMAC token system with standard PyJWT (HS256) for all token operations
- Created User model with bcrypt-hashed passwords and DB-backed admin/HR authentication
- Built employee triple-factor verification (employee_id + id_number + person_name) with 5-attempt rate limiting
- Implemented require_role() dependency factory supporting 3-role RBAC (admin, hr, employee)
- Auto-seeds default admin user on first boot with must_change_password=True
- Full 16-test suite covering all auth flows, RBAC, rate limiting, JWT claims, and seeding

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend auth core** - `b31d215` (feat)

## Files Created/Modified
- `backend/app/models/user.py` - User SQLAlchemy model with username, hashed_password, role, is_active, must_change_password
- `backend/app/services/user_service.py` - Password hashing, user CRUD, authenticate_user_login, seed_default_admin
- `backend/app/services/rate_limiter.py` - Thread-safe in-memory rate limiter (5 failures / 15min lockout)
- `backend/app/core/auth.py` - Rewritten: PyJWT issue/verify, AuthRole now includes 'employee'
- `backend/app/core/config.py` - Added employee_token_expire_minutes=30
- `backend/app/schemas/auth.py` - Added EmployeeVerifyRequest/Response, must_change_password field
- `backend/app/api/v1/auth.py` - Rewritten: DB-backed login, employee-verify endpoint
- `backend/app/dependencies.py` - Added require_role() factory
- `backend/app/bootstrap.py` - Added seed_default_admin on startup
- `backend/app/models/__init__.py` - Registered User model
- `backend/requirements.server.txt` - Replaced python-jose/passlib with PyJWT/pwdlib
- `tests/conftest.py` - Test infrastructure with in-memory SQLite, fixtures
- `tests/test_auth.py` - 16 tests covering all auth behaviors

## Decisions Made
- Used pwdlib with explicit BcryptHasher instead of PasswordHash.recommended() which requires argon2 (not installed)
- Kept config-level admin_login_username/password for backward compat during transition period
- Rate limiter uses employee_id as key (not IP) per design decision D-04
- Login endpoint accepts but ignores role field for backward compat with existing frontend

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pwdlib PasswordHash.recommended() requiring argon2**
- **Found during:** Task 1 (test execution)
- **Issue:** pwdlib's `PasswordHash.recommended()` requires argon2 which was not installed
- **Fix:** Used explicit `PasswordHash((BcryptHasher(),))` instead
- **Files modified:** backend/app/services/user_service.py
- **Verification:** All 16 tests pass
- **Committed in:** b31d215

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor fix to use correct hasher. No scope creep.

## Issues Encountered
None beyond the pwdlib hasher fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Auth backend fully operational, ready for Plan 02 (user management API) and Plan 03 (frontend auth)
- Default admin auto-seeded, frontend can immediately use POST /auth/login
- Employee verification ready once EmployeeMaster records are populated

## Self-Check: PASSED

---
*Phase: 02-authentication-rbac*
*Completed: 2026-03-28*
