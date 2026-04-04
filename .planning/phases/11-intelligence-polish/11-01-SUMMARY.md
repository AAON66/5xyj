---
phase: 11-intelligence-polish
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, anomaly-detection, period-comparison]

requires:
  - phase: 06-data-quality
    provides: validation framework and data quality patterns
  - phase: 09-api-system
    provides: API router patterns and Chinese endpoint descriptions
provides:
  - compare_periods() for cross-billing-period record comparison
  - AnomalyRecord model for persisting anomaly detection results
  - detect_anomalies() service with configurable per-field thresholds
  - Anomaly CRUD API (POST /detect, GET /, PATCH /status)
affects: [11-02-frontend, 11-03-frontend]

tech-stack:
  added: []
  patterns: [period-excluded-fields-in-comparison, per-field-threshold-configuration]

key-files:
  created:
    - backend/app/models/anomaly_record.py
    - backend/app/schemas/anomaly.py
    - backend/app/services/anomaly_detection_service.py
    - backend/app/api/v1/anomaly.py
    - tests/test_period_compare.py
    - tests/test_anomaly_detection.py
    - tests/test_anomaly_api.py
  modified:
    - backend/app/services/compare_service.py
    - backend/app/schemas/compare.py
    - backend/app/api/v1/compare.py
    - backend/app/models/__init__.py
    - backend/app/core/config.py
    - backend/app/api/v1/router.py

key-decisions:
  - "Excluded billing_period/period_start/period_end from period comparison diff fields since they always differ across periods"
  - "Per-field threshold configuration via Settings with override support in detect request"

patterns-established:
  - "PERIOD_COMPARE_EXCLUDED_FIELDS: frozenset of fields excluded from cross-period diff detection"
  - "INSURANCE_FIELDS mapping: field_name to config threshold key for anomaly detection"

requirements-completed: [INTEL-01, INTEL-02]

duration: 8min
completed: 2026-04-04
---

# Phase 11 Plan 01: Period Comparison + Anomaly Detection Backend Summary

**Cross-period comparison API and anomaly detection service with configurable per-field thresholds and status workflow**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-04T06:39:00Z
- **Completed:** 2026-04-04T06:47:16Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Built compare_periods() reusing existing identity matching infrastructure for cross-billing-period comparison
- Created AnomalyRecord model with pending/confirmed/excluded status workflow
- Implemented detect_anomalies() with 7 configurable thresholds (payment_base at 15%, pension at 20%, etc.)
- Anomaly CRUD API with audit logging on status updates, admin/hr RBAC protection

## Task Commits

Each task was committed atomically:

1. **Task 1: Period comparison backend + AnomalyRecord model + anomaly detection service** - `ff33104` (feat)
2. **Task 2: Anomaly API endpoints + router registration** - `2a9302d` (feat)

## Files Created/Modified
- `backend/app/models/anomaly_record.py` - AnomalyRecord SQLAlchemy model
- `backend/app/schemas/anomaly.py` - Pydantic schemas for anomaly API
- `backend/app/services/anomaly_detection_service.py` - Detection logic with per-field thresholds
- `backend/app/api/v1/anomaly.py` - REST endpoints for anomaly CRUD
- `backend/app/services/compare_service.py` - Added compare_periods() function
- `backend/app/schemas/compare.py` - Added PeriodCompareRead and PeriodCompareSummaryGroup
- `backend/app/api/v1/compare.py` - Added GET /compare/periods endpoint
- `backend/app/core/config.py` - Added anomaly threshold settings
- `backend/app/models/__init__.py` - Registered AnomalyRecord
- `backend/app/api/v1/router.py` - Registered anomaly_router
- `tests/test_period_compare.py` - 8 tests for period comparison
- `tests/test_anomaly_detection.py` - 14 tests for anomaly detection
- `tests/test_anomaly_api.py` - 8 tests for anomaly API endpoints

## Decisions Made
- Excluded billing_period, period_start, period_end, raw_sheet_name, raw_header_signature, source_file_name from period comparison diff fields since these always differ across periods and would create false positives
- Used per-field threshold configuration mapped to Settings attributes, allowing request-level overrides

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Excluded period-related fields from cross-period diff detection**
- **Found during:** Task 1 (period comparison implementation)
- **Issue:** billing_period is always different between two periods, causing every matched employee to show as "changed"
- **Fix:** Added PERIOD_COMPARE_EXCLUDED_FIELDS frozenset to filter out fields that inherently differ across periods
- **Files modified:** backend/app/services/compare_service.py
- **Verification:** Tests pass with correct same/changed/left_only/right_only counts
- **Committed in:** ff33104 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed issue_access_token return type in API tests**
- **Found during:** Task 2 (API test writing)
- **Issue:** issue_access_token returns tuple (token, datetime), not just token string
- **Fix:** Destructured return value in test helpers
- **Files modified:** tests/test_anomaly_api.py
- **Verification:** All 8 API tests pass
- **Committed in:** 2a9302d (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Test directory is at project root `tests/` not `backend/tests/` as plan specified -- adjusted paths accordingly

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all services are fully implemented with real database operations.

## Next Phase Readiness
- Period comparison and anomaly detection APIs are ready for frontend consumption in plans 11-02 and 11-03
- Thresholds are configurable via environment variables (ANOMALY_THRESHOLD_*)

---
*Phase: 11-intelligence-polish*
*Completed: 2026-04-04*
