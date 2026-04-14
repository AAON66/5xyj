---
phase: 18-responsive-adaptation
plan: 03
title: "Phase 18 Plan 03: Drawer Filters For Data Pages"
subsystem: data-management
tags: [responsive, filters, drawer, tables, ant-design]
dependency_graph:
  requires: [18-01]
  provides: [shared-filter-drawer, draft-apply-filter-pattern]
  affects: [data-management, employees, audit-logs]
tech_stack:
  added: []
  patterns: [draft-filter-state, drawer-apply-reset, wide-table-scroll]
key_files:
  created:
    - frontend/src/components/ResponsiveFilterDrawer.tsx
  modified:
    - frontend/src/pages/DataManagement.tsx
    - frontend/src/pages/Employees.tsx
    - frontend/src/pages/AuditLogs.tsx
decisions:
  - "筛选抽屉只承载草稿态，关闭抽屉不会污染已应用筛选"
  - "关键身份列继续固定在左侧，响应式通过横向滚动而不是删列实现"
metrics:
  duration: "n/a"
  completed: "2026-04-09T11:33:47+08:00"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 4
requirements:
  - UX-03
---

# Phase 18 Plan 03: Drawer Filters For Data Pages Summary

DataManagement、Employees、AuditLogs 已统一为桌面内联筛选 + 小屏抽屉筛选，并建立了共享的 draft/apply/reset 模式。

## What Was Done

### Task 1: 共享筛选抽屉组件
- 新增 `ResponsiveFilterDrawer`
- 固定底部 footer 提供 `应用筛选` 和 `清空`
- 支持安全区 padding，适合移动端底部交互

### Task 2: DataManagement 响应式筛选
- 引入草稿态 `draftFilters`
- `<992px` 时切换为筛选按钮 + Drawer
- 统一桌面和移动端的应用逻辑
- 3 张数据表的 `scroll.x` 提升并保留固定左列

### Task 3: Employees / AuditLogs 小屏筛选改造
- 两页都改为共享的抽屉筛选模式
- 标题区按钮支持换行
- 宽表格继续保留横向滚动和关键列

## Verification Results

- `cd frontend && ./node_modules/.bin/eslint src/components/ResponsiveFilterDrawer.tsx src/pages/DataManagement.tsx src/pages/Employees.tsx src/pages/AuditLogs.tsx`
- 通过，退出码 0

## Deviations from Plan

None - plan executed exactly as written.

## Commits

Deferred. Phase 18 is waiting on human responsive UAT, so no completion commit was created in this run.

## Self-Check: PASSED

- Shared drawer component exists with apply/reset footer
- Data pages no longer auto-query on every mobile filter change
- Key tables retain fixed left columns and explicit horizontal scroll
