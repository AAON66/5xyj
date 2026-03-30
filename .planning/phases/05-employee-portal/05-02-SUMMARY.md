---
phase: 05-employee-portal
plan: 02
subsystem: ui
tags: [react, typescript, employee-portal, self-service, rbac, role-route]

requires:
  - phase: 05-employee-portal plan 01
    provides: GET /self-service/my-records endpoint with insurance breakdown fields
  - phase: 02-auth-rbac
    provides: ProtectedRoute, RoleRoute, AuthContext, authSession utilities
provides:
  - Rewritten EmployeeSelfService page with overview + expandable insurance details
  - fetchPortalRecords API function for token-bound GET /self-service/my-records
  - EmployeeSelfServiceRecord extended with 9 insurance breakdown fields
  - Route protection via ProtectedRoute + RoleRoute(['employee'])
  - Token expiry detection with auto-redirect to login
  - Role-based route restriction ensuring employee role cannot access admin/hr pages
affects: [07-design-system, 08-page-rebuild]

tech-stack:
  added: []
  patterns: [expandable record list with Set-based toggle state, inline insurance detail grid]

key-files:
  created: []
  modified:
    - frontend/src/services/employees.ts
    - frontend/src/pages/EmployeeSelfService.tsx
    - frontend/src/App.tsx

key-decisions:
  - "Restricted all non-portal routes (admin/hr pages) with RoleRoute(['admin','hr']) to prevent employee role from accessing other pages"

patterns-established:
  - "Employee portal pages use RoleRoute(['employee']) inside ProtectedRoute for access control"
  - "Expandable record lists use useState<Set<string>> for tracking open items by ID"

requirements-completed: [PORTAL-01, PORTAL-02, PORTAL-03, PORTAL-04, PORTAL-05]

duration: ~25min
completed: 2026-03-30
---

# Phase 05 Plan 02: Employee Portal Frontend Summary

**React portal page with personal info overview, expandable insurance/housing fund details per billing period, and full role-based route protection for employee isolation**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-29T09:00:00Z (approx)
- **Completed:** 2026-03-30T00:31:00Z
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 3

## Accomplishments

- Extended EmployeeSelfServiceRecord TypeScript interface with 9 insurance breakdown fields (payment_base, pension, medical, unemployment, injury, maternity)
- Rewrote EmployeeSelfService.tsx as overview + expandable detail page: personal info card, latest month summary, historical records with per-record insurance/housing fund breakdown
- Protected /employee/query route with ProtectedRoute + RoleRoute(['employee']) and restricted all admin/hr routes from employee access
- Token expiry detection with 2-second auto-redirect to login page
- Empty-state handling with friendly message when no records exist

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend TS interface + fetchPortalRecords + route protection** - `e993c02` (feat)
2. **Task 2: Rewrite portal page with overview + expandable details** - `69d25ab` (feat)
3. **Bug fix: Restrict non-portal routes to admin/hr roles** - `42f9313` (fix)
4. **Task 3: Human-verify checkpoint** - N/A (approved by user)

## Files Created/Modified

- `frontend/src/services/employees.ts` - Added 9 insurance breakdown fields to EmployeeSelfServiceRecord interface + fetchPortalRecords() API function
- `frontend/src/pages/EmployeeSelfService.tsx` - Complete rewrite: personal info card, latest month summary, expandable historical records with insurance/housing fund detail grids, token expiry handling, empty state
- `frontend/src/App.tsx` - Moved /employee/query inside ProtectedRoute + RoleRoute(['employee']); added RoleRoute(['admin','hr']) around all other protected routes

## Decisions Made

- **Restricted all non-portal routes to admin/hr:** During human verification, discovered that employee role could navigate to admin/hr pages (e.g., user management, audit logs). Added RoleRoute(['admin','hr']) wrapper around all non-employee protected routes to enforce proper isolation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Employee role could access admin/hr pages**
- **Found during:** Task 3 (human verification)
- **Issue:** After moving /employee/query inside ProtectedRoute + RoleRoute(['employee']), the remaining admin/hr routes (user management, audit logs, data management, etc.) were still accessible to any authenticated user including employees. An employee could navigate to these pages.
- **Fix:** Wrapped all non-employee protected routes with `<Route element={<RoleRoute allowedRoles={['admin', 'hr']} />}>` to restrict access.
- **Files modified:** frontend/src/App.tsx
- **Verification:** Employee role can only access /employee/query; all other protected routes return permission denied for employee role.
- **Committed in:** 42f9313

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential security fix to enforce proper role isolation. No scope creep.

## Issues Encountered

None - implementation and verification proceeded smoothly after the role restriction fix.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all fields are wired to the backend API response with real data flow.

## Next Phase Readiness

- Employee portal (Phase 5) is fully complete: backend API (Plan 01) + frontend page (Plan 02)
- Employees can verify identity, view overview, and browse historical records with insurance breakdown
- Ready for Phase 6 (Data Management) or Phase 7 (Design System)

## Self-Check: PASSED

- All 3 key files FOUND
- All 3 commit hashes FOUND (e993c02, 69d25ab, 42f9313)
- SUMMARY.md created and verified

---
*Phase: 05-employee-portal*
*Completed: 2026-03-30*
