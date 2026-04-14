---
phase: 16-account-management
plan: 01
subsystem: auth
tags: [fastapi, password, rbac, self-protection, tdd]

requires:
  - phase: 13-auth-rbac
    provides: JWT auth, User model, role-based access control

provides:
  - PUT /auth/change-password endpoint (admin/hr only)
  - Fixed GET /auth/me returning real display_name and must_change_password from DB
  - must_change_password=True on user creation and password reset
  - Admin self-protection (cannot disable self, change own role, reset own password)

affects: [16-account-management-plan-02, frontend-account-pages]

tech-stack:
  added: []
  patterns:
    - "Self-protection pattern: API endpoint checks if actor is targeting self before allowing destructive operations"
    - "TDD for backend API: write failing tests first, implement, verify"

key-files:
  created: []
  modified:
    - backend/app/schemas/auth.py
    - backend/app/services/user_service.py
    - backend/app/api/v1/auth.py
    - backend/app/api/v1/users.py
    - tests/test_users.py

key-decisions:
  - "Employee role returns 403 on change-password since employees use three-factor auth without password accounts"
  - "Admin self-protection at API layer (not service layer) to keep service functions reusable"
  - "GET /auth/me reads from DB for admin/hr roles, falls back to token data for employee role"

patterns-established:
  - "Self-protection: check current_user.username == target_user.username before destructive operations"
  - "must_change_password lifecycle: True on create/reset, False on self-change"

requirements-completed: [ACCT-03, ACCT-04]

duration: 6min
completed: 2026-04-07
---

# Phase 16 Plan 01: Backend Account Management API Summary

**Change-password endpoint with old password verification, fixed /auth/me to return real DB state, must_change_password lifecycle fixes, and admin self-protection guards**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-07T08:10:11Z
- **Completed:** 2026-04-07T08:16:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added PUT /auth/change-password endpoint with old password verification, employee 403 protection, and audit logging
- Fixed GET /auth/me to return real display_name and must_change_password from database instead of hardcoded values
- Fixed must_change_password flag: now True on user creation and admin password reset, cleared on self-change
- Added admin self-protection: cannot disable own account, change own role, or reset own password via admin endpoint
- 15 new tests added (9 for Task 1 + 6 for Task 2), all 44 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: change-password endpoint + fix /auth/me** - `79fdfae` (test: RED), `9d4e5a8` (feat: GREEN)
2. **Task 2: must_change_password fixes + admin self-protection** - `a60447a` (test: RED), `80e9244` (feat: GREEN)

_TDD tasks each have RED (failing test) + GREEN (implementation) commits_

## Files Created/Modified
- `backend/app/schemas/auth.py` - Added ChangePasswordRequest schema (old_password + new_password with validation)
- `backend/app/services/user_service.py` - Added change_own_password method; fixed create_user and reset_user_password to set must_change_password=True
- `backend/app/api/v1/auth.py` - Added PUT /change-password endpoint; fixed GET /me to read from DB
- `backend/app/api/v1/users.py` - Added self-protection checks in update_user_endpoint and reset_password_endpoint
- `tests/test_users.py` - Added TestChangePassword (6), TestAuthMe (3), TestResetPasswordMustChange (1), TestCreateUserMustChange (1), TestSelfProtection (4)

## Decisions Made
- Employee role returns 403 on change-password since employees use three-factor auth without password accounts
- Admin self-protection implemented at API layer (not service layer) to keep service functions reusable for programmatic use
- GET /auth/me reads from DB for admin/hr roles to get real must_change_password and display_name; falls back to token data for employee role

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test assertion to match global exception handler format**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Test expected `resp.json()["detail"]` but global exception handler wraps HTTPException into `{"error": {"message": ...}}` format
- **Fix:** Changed test assertion to `resp.json()["error"]["message"]`
- **Files modified:** tests/test_users.py
- **Verification:** All 9 Task 1 tests pass
- **Committed in:** 9d4e5a8 (part of Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Minor test assertion format fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend API fully ready for Phase 16 Plan 02 (frontend account management pages)
- All endpoints tested: change-password, /me, create user, update user, reset password
- Self-protection guards in place to prevent admin lockout

---
## Self-Check: PASSED

- All 5 source files exist
- All 4 commits verified in git log
- All 11 acceptance criteria confirmed

*Phase: 16-account-management*
*Completed: 2026-04-07*
