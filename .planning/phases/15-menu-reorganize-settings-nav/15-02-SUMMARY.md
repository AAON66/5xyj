---
phase: 15-menu-reorganize-settings-nav
plan: "02"
subsystem: frontend-settings
tags: [settings-page, search, navigation, card-grid, role-filtering]
dependency_graph:
  requires: [15-01]
  provides: [settings-page, settings-route, settings-menu-entry]
  affects: [App.tsx, MainLayout.tsx, pages/index.ts]
tech_stack:
  added: []
  patterns: [card-grid-layout, search-filter-highlight, auto-scroll-navigation, role-based-card-visibility]
key_files:
  created:
    - frontend/src/pages/Settings.tsx
  modified:
    - frontend/src/pages/index.ts
    - frontend/src/App.tsx
    - frontend/src/layouts/MainLayout.tsx
decisions:
  - "Removed 'account' placeholder card -- Phase 16 will implement account management"
  - "Used indexOf-based highlight instead of regex to avoid special character issues"
  - "Theme card kept with inline toggle despite header button duplication -- settings page provides more context"
metrics:
  duration: "149s"
  completed: "2026-04-07"
  tasks_completed: 1
  tasks_total: 2
  checkpoint_pending: true
---

# Phase 15 Plan 02: Settings Page with Search and Navigation Summary

Settings page with card-based layout, search filtering with keyword highlighting, auto-scroll to first match, and role-based card visibility for admin/hr users.

## What Was Done

### Task 1: Create Settings page with search, card grid, and auto-scroll navigation

Created `frontend/src/pages/Settings.tsx` with the following features:

- **Card-based layout**: 4 settings cards (appearance, audit logs, API keys, Feishu integration) displayed in responsive grid (xs=24, md=12, lg=8)
- **Search filtering**: Input.Search filters cards by title, description, and keyword tags
- **Keyword highlighting**: Matched text highlighted with `colorWarningBg` using safe indexOf-based approach (no regex, no dangerouslySetInnerHTML)
- **Auto-scroll navigation**: First matching card receives `colorPrimary` border focus and `scrollIntoView` smooth scroll
- **Empty state**: Shows "未找到匹配的设置项" with "请尝试其他关键词" hint
- **Role-based visibility**: Admin sees all 4 cards; HR sees only appearance card
- **Feishu conditional**: Feishu card only shown when `feishu_sync_enabled` is true
- **Theme toggle inline**: Appearance card contains Sun/Moon switch for dark/light mode
- **Navigation links**: Audit, API keys, and Feishu cards have "前往" links to their dedicated pages

Route and menu integration:
- Exported `SettingsPage` from `frontend/src/pages/index.ts`
- Added `/settings` route in `App.tsx` inside `RoleRoute allowedRoles={['admin', 'hr']}`
- Added `/settings` menu item to `group-admin` children in `MainLayout.tsx` with `roles: ['admin', 'hr']`

### Task 2: Verify menu grouping and settings page (CHECKPOINT PENDING)

This is a `checkpoint:human-verify` task requiring manual browser verification of both Plan 01 (menu grouping) and Plan 02 (settings page) features. Not executed -- awaiting human verification.

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | f65f887 | feat(15-02): create Settings page with search, card grid, and auto-scroll navigation |

## Verification Results

- `npm run lint`: PASSED (no new errors in modified files; 3 pre-existing errors in unrelated files)
- `npm run build`: PASSED (3301 modules transformed, built in 3.81s)
- `/settings` route in RoleRoute `['admin', 'hr']`: CONFIRMED
- Settings.tsx contains search, highlight, scrollIntoView: CONFIRMED
- Settings.tsx does not contain dangerouslySetInnerHTML: CONFIRMED
- Settings.tsx does not contain key 'account': CONFIRMED
- MainLayout.tsx group-admin contains `/settings` with roles `['admin', 'hr']`: CONFIRMED

## Self-Check: PASSED

All created files exist and commits verified:
- frontend/src/pages/Settings.tsx: EXISTS
- Commit f65f887: EXISTS
