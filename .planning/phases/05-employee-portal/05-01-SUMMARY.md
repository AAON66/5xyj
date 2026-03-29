---
phase: 05-employee-portal
plan: 01
subsystem: api
tags: [fastapi, jwt, rbac, employee-portal, self-service]

requires:
  - phase: 02-auth-rbac
    provides: JWT auth system with role-based access control (admin/hr/employee)
  - phase: 04-data-management
    provides: Employee master data model and normalized records
provides:
  - EmployeeSelfServiceRecordRead schema with 9 insurance breakdown fields
  - lookup_employee_portal service function for token-based employee data access
  - GET /self-service/my-records endpoint with employee role enforcement
  - Data isolation guarantee (employee sees only own records)
affects: [05-employee-portal plan 02, 07-design-system, 08-page-rebuild]

tech-stack:
  added: []
  patterns: [separate portal router to bypass admin/hr router-level RBAC]

key-files:
  created:
    - backend/app/api/v1/employee_portal.py
  modified:
    - backend/app/schemas/employees.py
    - backend/app/services/employee_service.py
    - backend/app/api/v1/router.py
    - backend/tests/test_employee_portal_api.py

key-decisions:
  - "Created separate employee_portal router instead of adding endpoint to existing employees router, because the employees router has router-level require_role(admin, hr) dependency that blocks employee role access"

patterns-established:
  - "Employee portal endpoints use a separate router (employee_portal.py) to avoid router-level RBAC conflicts"
  - "Token-based employee lookup uses employee_id from JWT sub claim, not user input parameters"

requirements-completed: [PORTAL-01, PORTAL-02, PORTAL-03, PORTAL-04, PORTAL-05]

duration: 28min
completed: 2026-03-29
---

# Phase 05 Plan 01: Employee Portal Backend API Summary

**Token-bound GET /self-service/my-records endpoint with 9 insurance breakdown fields, housing fund data, multi-period ordering, and data isolation via separate portal router**

## Performance

- **Duration:** 28 min
- **Started:** 2026-03-29T08:24:18Z
- **Completed:** 2026-03-29T08:53:11Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 5

## Accomplishments

- Extended EmployeeSelfServiceRecordRead with payment_base, pension_company/personal, medical_company/personal, unemployment_company/personal, injury_company, maternity_amount
- Implemented lookup_employee_portal service function using employee_id from JWT token
- Created separate employee_portal router with GET /self-service/my-records endpoint enforcing employee role
- 6 tests pass: insurance breakdown, housing fund, multi-period ordering, data isolation, auth enforcement, old endpoint regression

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests** - `ebcb2e3` (test)
2. **Task 1 (GREEN): Schema + service + endpoint implementation** - `9ec6c20` (feat)

## Files Created/Modified

- `backend/app/api/v1/employee_portal.py` - New router for employee portal endpoints (separate from admin/hr employees router)
- `backend/app/schemas/employees.py` - Added 9 Optional[Decimal] insurance breakdown fields to EmployeeSelfServiceRecordRead
- `backend/app/services/employee_service.py` - Added lookup_employee_portal function and extended _to_self_service_record with insurance field mappings
- `backend/app/api/v1/router.py` - Registered employee_portal_router without admin/hr restriction
- `backend/tests/test_employee_portal_api.py` - 6 tests covering PORTAL-01~05

## Decisions Made

- **Separate portal router:** Created `employee_portal.py` as a distinct router because the existing `employees` router has a router-level `require_role("admin", "hr")` dependency (applied in `router.py`). Adding an employee-role endpoint to that router would be blocked by the parent RBAC. The portal router is registered without router-level dependencies, relying on endpoint-level `require_role("employee")` instead.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Router-level RBAC conflict required separate router**
- **Found during:** Task 1 GREEN phase
- **Issue:** Plan specified adding GET /self-service/my-records to employees.py, but the employees router has router-level `dependencies=[Depends(require_role("admin", "hr"))]` in router.py, blocking employee role tokens with 403.
- **Fix:** Created a separate `employee_portal.py` router and registered it without router-level RBAC restrictions in router.py.
- **Files modified:** backend/app/api/v1/employee_portal.py (new), backend/app/api/v1/router.py
- **Verification:** All 6 tests pass, employee token receives 200 on /self-service/my-records
- **Committed in:** 9ec6c20

**2. [Rule 1 - Bug] BatchStatus.COMPLETED does not exist**
- **Found during:** Task 1 RED phase
- **Issue:** Test used `BatchStatus.COMPLETED` which doesn't exist in the enum (valid values: UPLOADED, PARSING, NORMALIZED, etc.)
- **Fix:** Changed to `BatchStatus.MATCHED` in seed helper
- **Committed in:** 9ec6c20

**3. [Rule 1 - Bug] SourceFile field names mismatch**
- **Found during:** Task 1 RED phase
- **Issue:** Test used `original_filename` and `stored_path` but SourceFile model uses `file_name` and `file_path`
- **Fix:** Updated seed helper to use correct field names
- **Committed in:** 9ec6c20

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correctness. The separate router pattern is architecturally cleaner and avoids RBAC conflicts. No scope creep.

## Issues Encountered

- Pre-existing test failure in `test_auth_api.py::test_login_endpoint_returns_bearer_token_for_admin` (401 instead of 200). Not caused by this plan's changes -- verified by running the test independently. Logged as out-of-scope.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all fields are wired to NormalizedRecord model attributes with real data flow.

## Next Phase Readiness

- Backend API complete for employee portal
- Ready for Phase 05 Plan 02 (frontend employee portal page)
- Token-based endpoint verified with data isolation

---
*Phase: 05-employee-portal*
*Completed: 2026-03-29*
