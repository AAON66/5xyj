---
phase: 13-foundation-deploy-compat
plan: "02"
subsystem: frontend
tags: [cleanup, ux, components]
dependency_graph:
  requires: []
  provides: [deprecated-component-cleanup, file-count-display, smart-employee-default]
  affects: [frontend/src/components/index.ts, frontend/src/pages/SimpleAggregate.tsx]
tech_stack:
  added: []
  patterns: [useRef-for-race-condition-guard]
key_files:
  created: []
  modified:
    - frontend/src/components/index.ts
    - frontend/src/pages/SimpleAggregate.tsx
  deleted:
    - frontend/src/components/AppShell.tsx
    - frontend/src/components/GlobalFeedback.tsx
    - frontend/src/components/PageContainer.tsx
    - frontend/src/components/SectionState.tsx
    - frontend/src/components/SurfaceNotice.tsx
decisions:
  - Used useRef (not useState) for manual-selection tracking to avoid race conditions with async API callback
metrics:
  duration: 2min
  completed: "2026-04-04T19:57:33Z"
---

# Phase 13 Plan 02: Frontend Deprecated Component Cleanup + SimpleAggregate Fixes Summary

Deleted 5 unused v1.0 components, added file count display and smart employee master defaults to the quick aggregate page.

## Commits

| # | Hash | Description |
|---|------|-------------|
| 1 | 6f8bba7 | chore(13-02): delete 5 deprecated components and update barrel export |
| 2 | f410791 | feat(13-02): add file counts and smart employee master defaults to SimpleAggregate |

## Task Results

### Task 1: Delete 5 deprecated components + update barrel export

- Deleted: AppShell.tsx, GlobalFeedback.tsx, PageContainer.tsx, SectionState.tsx, SurfaceNotice.tsx
- Updated components/index.ts to export only ApiFeedbackProvider, AuthProvider, WorkflowSteps
- Verified zero remaining references across all .ts/.tsx files
- Frontend build passes cleanly

### Task 2: File counts + smart employee master defaults

- Added per-area file count after social and housing fund Dragger components, using `socialDisplayList.length` and `housingDisplayList.length` (deduplicated, session-aware)
- Added summary count line: "共 N 个文件（社保 X | 公积金 Y）"
- Added `employeeMasterManualRef` (useRef) to track whether user manually changed employee master mode
- Modified fetchEmployeeMasters useEffect to auto-set mode to 'existing' when server has masters and user hasn't manually changed
- Modified Select onChange to set `employeeMasterManualRef.current = true`

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Verification

- `npm run build` passes for both tasks
- grep confirms 3 occurrences of "个文件" in SimpleAggregate.tsx (social, housing, summary)
- grep confirms 3 occurrences of "employeeMasterManualRef" (declaration, set, check)
- grep confirms 0 remaining references to deleted components

## Self-Check: PASSED

- All 5 deprecated components verified deleted
- components/index.ts and SimpleAggregate.tsx verified modified
- Both commits (6f8bba7, f410791) exist in git log
- Frontend builds successfully
