---
phase: 18-responsive-adaptation
plan: 02
title: "Phase 18 Plan 02: Employee Self-Service Mobile Card Flow"
subsystem: employee-portal
tags: [responsive, employee-portal, collapse, mobile, cards]
dependency_graph:
  requires: [18-01]
  provides: [mobile-history-collapse, stacked-detail-cards]
  affects: [employee-self-service]
tech_stack:
  added: []
  patterns: [mobile-card-flow, latest-record-default-expand]
key_files:
  created: []
  modified:
    - frontend/src/pages/EmployeeSelfService.tsx
decisions:
  - "员工自助查询在手机端优先使用卡片流，而不是继续压缩桌面表格"
  - "历史月份默认仅展开最新一条，降低手机端信息密度"
metrics:
  duration: "n/a"
  completed: "2026-04-09T11:33:47+08:00"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 1
requirements:
  - UX-03
---

# Phase 18 Plan 02: Employee Self-Service Mobile Card Flow Summary

员工自助查询页已改为手机优先的资料卡 + 当月汇总 + 历史折叠卡片流，同时保留桌面端的表格展开体验。

## What Was Done

### Task 1: 手机端卡片流与历史折叠
- 接入 `useResponsiveViewport`，将移动端和桌面端分支明确分离
- 拉取数据后默认展开最新月份 `normalized_record_id`
- 移动端主视图改为 `Collapse`，明细卡片改为上下堆叠
- 桌面端继续保留 `Table + expandable row`

## Verification Results

- `cd frontend && ./node_modules/.bin/eslint src/pages/EmployeeSelfService.tsx`
- 通过，退出码 0

## Deviations from Plan

None - plan executed exactly as written.

## Commits

Deferred. Phase 18 is waiting on human responsive UAT, so no completion commit was created in this run.

## Self-Check: PASSED

- `Collapse` and latest-record default expansion logic are present
- 移动端不再以 Table 作为历史记录主视图
- 桌面端表格交互未被移除
