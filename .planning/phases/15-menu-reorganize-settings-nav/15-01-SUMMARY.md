---
phase: 15-menu-reorganize-settings-nav
plan: 01
subsystem: frontend-layout
tags: [menu, sidebar, ux, navigation, localStorage]
dependency_graph:
  requires: []
  provides: [grouped-menu, useMenuOpenKeys-hook, sub-route-resolution]
  affects: [MainLayout, sidebar-navigation]
tech_stack:
  added: []
  patterns: [localStorage-persistence-hook, sub-route-menu-key-resolution, grouped-submenu]
key_files:
  created:
    - frontend/src/hooks/useMenuOpenKeys.ts
  modified:
    - frontend/src/layouts/MainLayout.tsx
decisions:
  - Removed ALL_NAV_ITEMS array since LABEL_MAP is independent and ALL_NAV_ITEMS had no remaining consumers
  - Used eslint-disable comment for useEffect dependency to avoid infinite loop on openKeys auto-expand
metrics:
  duration: 274s
  completed: "2026-04-07T06:13:18Z"
  tasks: 2
  files: 2
---

# Phase 15 Plan 01: Sidebar Menu Grouping and Sub-Route Resolution Summary

Three collapsible SubMenu groups (common/analysis/admin) with quick-aggregate pinned top, localStorage open-state persistence via useMenuOpenKeys hook, and sub-route selectedKey resolution for detail pages.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create useMenuOpenKeys hook | e49e170 | frontend/src/hooks/useMenuOpenKeys.ts |
| 2 | Refactor MainLayout menu to grouped SubMenu structure | 85a00b7 | frontend/src/layouts/MainLayout.tsx |

## What Changed

### Task 1: useMenuOpenKeys hook
- New hook at `frontend/src/hooks/useMenuOpenKeys.ts`
- Reads/writes `menu-open-keys` localStorage key with JSON serialization
- `validKeys` parameter filters out stale group keys (handles role changes, feishu toggle)
- Defensive try/catch for Safari private mode and JSON parse errors
- `useCallback` wraps `onOpenChange` for stable reference

### Task 2: MainLayout grouped menu
- Replaced flat 14-item `ALL_NAV_ITEMS` menu with 3 `MenuGroupConfig` groups:
  - `group-common` (default expanded): dashboard, imports, results, exports
  - `group-analysis` (default collapsed): compare, period-compare, anomaly-detection, mappings
  - `group-admin` (default collapsed): employees, data-management, audit-logs, api-keys + feishu items
- `TOP_ITEM` pins quick-aggregate above all groups
- `resolveSelectedMenuKey()`: maps `/imports/:id` -> `/imports`, `/employees/new` -> `/employees`, `/feishu-mapping/:id` -> `/feishu-settings`
- `findParentGroupKey()`: auto-expands parent group when navigating to a child item
- Employee role returns single `['/employee/query']` without any groups
- Feishu items conditionally injected into admin group when `feishu_sync_enabled`
- Added `settings: '系统设置'` to LABEL_MAP for Plan 02 breadcrumb preparation
- `selectedKeys` now uses `resolvedKey` instead of raw `location.pathname`
- `openKeys` and `onOpenChange` controlled by `useMenuOpenKeys` hook

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Lint] Removed unused ALL_NAV_ITEMS constant**
- **Found during:** Task 2
- **Issue:** After refactoring menu to use MENU_GROUPS/TOP_ITEM, ALL_NAV_ITEMS was unreferenced, causing `@typescript-eslint/no-unused-vars` lint error
- **Fix:** Removed the constant entirely (LABEL_MAP is independent, doesn't reference ALL_NAV_ITEMS)
- **Files modified:** frontend/src/layouts/MainLayout.tsx
- **Commit:** 85a00b7

## Verification

- `npm run lint`: No errors in MainLayout.tsx (4 pre-existing errors in other files unchanged)
- `npm run build`: Passes (3.36s, 3300 modules)
- All acceptance criteria checked via grep

## Threat Surface

T-15-01 mitigated: `buildMenuItems` maintains `roles.includes(userRole)` filter for every NavItem.
T-15-02 accepted: localStorage tampering only affects UI expand state, not permissions.
T-15-03 mitigated: employee branch returns fixed `['/employee/query']`, never references MENU_GROUPS.

## Known Stubs

None - all data sources and logic are fully wired.

## Self-Check: PASSED

- All 2 created/modified files exist on disk
- All 2 task commits found in git history
- SUMMARY.md created at expected path
