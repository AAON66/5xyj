---
phase: 17-data-management-enhancement
plan: 03
title: "Phase 17 Plan 03: Batch Deletion Impact Preview"
subsystem: data-management
tags: [deletion, confirmation, cascade, api]
dependency_graph:
  requires: [17-02]
  provides: [deletion-impact-endpoint, enhanced-delete-modal]
  affects: [imports-page, import-service]
tech_stack:
  added: []
  patterns: [pre-deletion-impact-query, enhanced-confirmation-modal]
key_files:
  created: []
  modified:
    - backend/app/schemas/imports.py
    - backend/app/services/import_service.py
    - backend/app/api/v1/imports.py
    - backend/tests/test_import_batches_api.py
    - frontend/src/services/imports.ts
    - frontend/src/pages/Imports.tsx
decisions:
  - "Impact query returns counts only (not data) to minimize information disclosure"
  - "Impact endpoint placed before DELETE route to avoid path conflict"
metrics:
  duration: "3m 27s"
  completed: "2026-04-08T03:07:19Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
requirements:
  - DATA-03
---

# Phase 17 Plan 03: Batch Deletion Impact Preview Summary

Batch deletion confirmation modal now pre-queries and displays associated data counts (records, matches, issues) before user confirms, with backend cascade delete validation.

## What Was Done

### Task 1: Backend Batch Deletion Impact Endpoint
- Added `BatchDeletionImpactRead` schema with `record_count`, `match_count`, `issue_count` fields
- Added `get_batch_deletion_impact` service function that queries NormalizedRecord, MatchResult, ValidationIssue counts via `func.count`
- Added `GET /imports/{batch_id}/deletion-impact` API endpoint with proper 404 handling
- Added 2 tests: normal case (with seeded data) and 404 for unknown batch

### Task 2: Frontend Delete Confirmation Modal Enhancement
- Added `BatchDeletionImpact` TypeScript interface and `fetchBatchDeletionImpact` API function
- Modified `handleDeleteBatch` to fetch impact data before showing modal
- Single batch delete modal now displays: X records, Y matches, Z issues to be deleted
- Bulk delete modal content updated to explicitly mention associated data cleanup

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- `pytest backend/tests/test_import_batches_api.py -x`: 17/17 passed
- `tsc --noEmit`: passed (zero errors)
- `npm run lint`: 8 issues (all pre-existing, zero new)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | db96550 | feat(17-03): add batch deletion impact preview endpoint |
| 2 | 641b3b4 | feat(17-03): enhance delete confirmation modal with impact preview |

## Self-Check: PASSED
