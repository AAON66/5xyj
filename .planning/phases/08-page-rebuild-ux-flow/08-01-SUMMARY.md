---
phase: 08-page-rebuild-ux-flow
plan: 01
subsystem: frontend-layout-errors
tags: [responsive, sidebar, error-messages, chinese-localization, ux]
dependency_graph:
  requires: []
  provides: [error-message-mapping, responsive-sidebar, chinese-api-errors]
  affects: [frontend/src/services/api.ts, frontend/src/layouts/MainLayout.tsx]
tech_stack:
  added: []
  patterns: [matchMedia-hook, error-code-mapping]
key_files:
  created:
    - frontend/src/constants/errorMessages.ts
  modified:
    - frontend/src/services/api.ts
    - frontend/src/layouts/MainLayout.tsx
decisions:
  - "getChineseErrorMessage returns a fallback with error code suffix when no mapping found"
  - "useResponsiveCollapse hook resets manual override on breakpoint crossing"
metrics:
  duration: 5min
  completed: "2026-03-31T03:36:00Z"
---

# Phase 8 Plan 01: Responsive Sidebar & Chinese Error Messages Summary

Responsive sidebar auto-collapse at 1440px breakpoint using matchMedia hook, plus centralized Chinese error message mapping for all API errors via getChineseErrorMessage.

## Changes Made

### Task 1: Chinese Error Message Mapping (801d390)

Created `frontend/src/constants/errorMessages.ts` with three exports:
- `ERROR_MESSAGES` - Maps error codes (validation_error, token_expired, etc.) to Chinese strings
- `HTTP_STATUS_MESSAGES` - Maps HTTP status codes (400-503) to Chinese strings
- `getChineseErrorMessage()` - Lookup function: error code first, then HTTP status, then fallback

Updated `frontend/src/services/api.ts` `normalizeApiError` to:
- Import and use `getChineseErrorMessage` for all non-timeout errors
- Handle network errors (no response, not timeout) with dedicated `network_error` Chinese message
- Preserve existing Chinese timeout message unchanged

### Task 2: Responsive Sidebar Auto-Collapse (3b80f47)

Added `useResponsiveCollapse` hook in `frontend/src/layouts/MainLayout.tsx`:
- Uses `window.matchMedia` to detect viewport width <= 1440px
- Sidebar auto-collapses to 64px icon mode below breakpoint
- Manual toggle via `manualCollapse` state still works
- Breakpoint crossing resets manual override so auto behavior takes over

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- TypeScript compilation: PASSED (zero errors)
- ESLint: PASSED (only pre-existing errors in unrelated files: ImportBatchDetail.tsx, Imports.tsx)
- Role-based menu filtering: Preserved (buildMenuItems unchanged)
- ConfigProvider locale={zhCN}: Untouched in main.tsx

## Known Stubs

None.

## Self-Check: PASSED

- frontend/src/constants/errorMessages.ts: FOUND
- Commit 801d390: FOUND
- Commit 3b80f47: FOUND
