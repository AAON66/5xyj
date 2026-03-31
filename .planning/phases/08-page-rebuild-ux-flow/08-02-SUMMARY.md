---
phase: 08-page-rebuild-ux-flow
plan: 02
subsystem: frontend-ui
tags: [workflow-steps, table-scroll, fixed-columns, navigation]
dependency_graph:
  requires: [08-01]
  provides: [WorkflowSteps-component, table-scroll-config]
  affects: [SimpleAggregate, Dashboard, Results, Exports, DataManagement, Employees, Imports]
tech_stack:
  added: []
  patterns: [shared-workflow-steps, fixed-column-tables]
key_files:
  created:
    - frontend/src/components/WorkflowSteps.tsx
  modified:
    - frontend/src/components/index.ts
    - frontend/src/pages/SimpleAggregate.tsx
    - frontend/src/pages/Dashboard.tsx
    - frontend/src/pages/Results.tsx
    - frontend/src/pages/Exports.tsx
    - frontend/src/pages/DataManagement.tsx
    - frontend/src/pages/Employees.tsx
    - frontend/src/pages/Imports.tsx
decisions:
  - WorkflowSteps uses useAggregateSession for status derivation and react-router for navigation
  - Fixed columns use 'as const' for TypeScript type narrowing on ColumnsType
  - Pre-existing lint errors in ImportBatchDetail.tsx and Imports.tsx left untouched (out of scope)
metrics:
  duration: 7min
  completed: 2026-03-31
  tasks: 2
  files: 9
---

# Phase 08 Plan 02: WorkflowSteps and Table Scroll Summary

Shared WorkflowSteps navigation bar with session-aware status, integrated into all 4 workflow pages, plus horizontal scroll and fixed-column configuration across all data tables.

## What Was Done

### Task 1: WorkflowSteps Shared Component (cfd1426)

Created `frontend/src/components/WorkflowSteps.tsx` with:
- 4-step navigation bar: upload, parse, validate, export
- Status derivation from `useAggregateSession` snapshot (idle/running/completed/failed maps to wait/process/finish/error)
- Click-to-navigate between /aggregate, /dashboard, /results, /exports via `useNavigate`
- Current page highlighted as active step via `useLocation`
- Compact Card wrapper with small Steps for minimal vertical space

Integrated into all 4 workflow pages:
- SimpleAggregate.tsx: below title bar, above health card
- Dashboard.tsx: below title bar, above page error
- Results.tsx: below title, above notice alerts
- Exports.tsx: below title, above notice alerts

### Task 2: Table Scroll and Fixed Columns (5c0d48c)

Audited all Table components across 7 pages:

**Added scroll + fixed columns (previously had none):**
- SimpleAggregate: source files table - scroll={{ x: true }}, file_name fixed left
- Dashboard: quality table and recent batches table - scroll={{ x: true }}, first columns fixed left
- Results: validation issues and match results tables - scroll={{ x: true }}, first columns fixed left
- Exports: artifacts table - scroll={{ x: true }}, template_type fixed left

**Added fixed columns (already had scroll):**
- DataManagement: person_name fixed left in detail table, employee_id fixed left in summary, billing_period fixed left in period summary
- Employees: employee_id fixed left, actions fixed right
- Imports: batch_name fixed left, actions fixed right

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | cfd1426 | WorkflowSteps component + 4-page integration |
| 2 | 5c0d48c | Table scroll and fixed-column configuration |

## Known Stubs

None - all components are fully wired to data sources.

## Self-Check: PASSED
