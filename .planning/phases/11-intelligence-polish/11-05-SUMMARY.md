---
phase: 11-intelligence-polish
plan: 05
subsystem: database
tags: [sqlalchemy, alembic, anomaly-detection, deduplication, unique-constraint]

requires:
  - phase: 11-intelligence-polish
    provides: AnomalyRecord model and detect_anomalies service (plan 01)
provides:
  - Idempotent anomaly detection with delete-before-insert deduplication
  - UniqueConstraint on AnomalyRecord preventing duplicate anomaly rows
  - Alembic migration 20260404_0009 for anomaly_records table
affects: [anomaly-detection, cross-period-comparison]

tech-stack:
  added: []
  patterns: [delete-before-insert deduplication, named unique constraints]

key-files:
  created:
    - backend/alembic/versions/20260404_0009_add_anomaly_record.py
  modified:
    - backend/app/models/anomaly_record.py
    - backend/app/services/anomaly_detection_service.py

key-decisions:
  - "Used delete-before-insert instead of upsert for simplicity and compatibility with SQLite"
  - "Named unique constraint uq_anomaly_identity for explicit migration control"

patterns-established:
  - "delete-before-insert: Delete existing records for period pair before inserting new anomalies, within single transaction"

requirements-completed: [INTEL-01, INTEL-02, INTEL-03, INTEL-04]

duration: 2min
completed: 2026-04-04
---

# Phase 11 Plan 05: Anomaly Detection Deduplication Summary

**UniqueConstraint and delete-before-insert deduplication ensuring idempotent anomaly detection re-runs**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-04T07:13:38Z
- **Completed:** 2026-04-04T07:15:50Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added UniqueConstraint(employee_identifier, left_period, right_period, field_name) named uq_anomaly_identity to AnomalyRecord model
- Added delete-before-insert logic to detect_anomalies() so re-running for the same period pair replaces previous results
- Created Alembic migration 20260404_0009 with full table schema and unique constraint

## Task Commits

Each task was committed atomically:

1. **Task 1: Add UniqueConstraint and delete-before-insert** - `c53e723` (fix)
2. **Task 2: Create Alembic migration** - `54b42f1` (chore)

## Files Created/Modified
- `backend/app/models/anomaly_record.py` - Added UniqueConstraint __table_args__
- `backend/app/services/anomaly_detection_service.py` - Added delete-before-insert deduplication
- `backend/alembic/versions/20260404_0009_add_anomaly_record.py` - New migration for anomaly_records table

## Decisions Made
- Used delete-before-insert instead of upsert for simplicity and SQLite compatibility
- Named the unique constraint uq_anomaly_identity for explicit control in migrations

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Anomaly detection is now idempotent and safe to re-run
- Frontend tooltip promise of overwrite behavior is now backed by actual backend logic

---
*Phase: 11-intelligence-polish*
*Completed: 2026-04-04*
