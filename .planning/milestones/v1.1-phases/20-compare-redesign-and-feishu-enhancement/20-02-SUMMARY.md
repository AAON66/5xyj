---
phase: 20-compare-redesign-and-feishu-enhancement
plan: 02
title: "Phase 20 Plan 02: 共享 workbook diff viewer 与 Compare/PeriodCompare 重做"
subsystem: frontend
tags: [compare, diff-viewer, react, playwright, responsive]
dependency_graph:
  requires: [period-compare-window-contract]
  provides: [shared-compare-workbook-viewer, compare-ui-redesign]
  affects: [compare-page, period-compare-page, responsive-regression]
tech_stack:
  added: []
  patterns: [shared-component, synchronized-scroll, route-mocked-playwright]
key_files:
  created:
    - frontend/src/components/CompareWorkbookDiff.tsx
    - frontend/tests/e2e/compare-diff.spec.ts
  modified:
    - frontend/src/services/compare.ts
    - frontend/src/pages/Compare.tsx
    - frontend/src/pages/PeriodCompare.tsx
    - frontend/tests/e2e/responsive.spec.ts
decisions:
  - "Compare 与 PeriodCompare 统一复用同一套左右 workbook viewer，避免两份差异渲染逻辑继续分叉"
  - "PeriodCompare 只请求当前服务端窗口；Compare 只渲染当前客户端分页窗口，500+ 行时不再落回卡片级全量渲染"
  - "紧凑视口不再依赖 Ant Table 固定列，而是通过共享面板自身横向滚动保持可操作性"
metrics:
  duration: "n/a"
  completed: "2026-04-09T23:22:19+08:00"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 6
requirements:
  - COMP-01
---

# Phase 20 Plan 02: 共享 workbook diff viewer 与 Compare/PeriodCompare 重做 Summary

Compare 相关前端已经真正切到 diff 风格：左右 workbook 面板、同步滚动、差异单元格高亮，以及统一的窄屏行为都落在同一个共享组件上。

## What Was Done

### Task 1: 新建共享 CompareWorkbookDiff 组件
- 新增 `frontend/src/components/CompareWorkbookDiff.tsx`
- 左右面板横向/纵向滚动同步，身份列 sticky，changed cell 高亮，left_only/right_only 行分色
- 对 `editable`/`onCellChange` 做了保留，Compare 页面仍可在 viewer 内联修改后导出

### Task 2: Compare 与 PeriodCompare 重构到共享 viewer
- `PeriodCompare.tsx` 接上服务端分页、搜索和 diff-only 窗口元数据，不再请求大批量后前端二次分块
- `Compare.tsx` 保留本地文件/线上批次双源、表类型切换、onlyDifferences、导出能力，但结果区改为共享 viewer
- `PeriodCompare` 在加载到账期选项后会自动预填最近两个账期，减少固定的首次操作成本

### Task 3: 补浏览器级 compare diff 回归
- 新增 `frontend/tests/e2e/compare-diff.spec.ts`
- 断言 shared viewer、差异高亮、分页请求参数、同步滚动、Compare 表类型切换
- 同步更新 `frontend/tests/e2e/responsive.spec.ts`，让 Phase 18 的紧凑视口合同适配新的 diff DOM

## Verification Results

- `cd frontend && ./node_modules/.bin/eslint src/services/compare.ts src/components/CompareWorkbookDiff.tsx src/pages/PeriodCompare.tsx src/pages/Compare.tsx tests/e2e/compare-diff.spec.ts`
- `cd frontend && npm run test:e2e -- compare-diff.spec.ts`
- `cd frontend && npm run test:e2e`

## Deviations from Plan

None - plan executed as intended.

## Commits

Deferred. Phase 20 本轮以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- 共享 workbook diff viewer 已落地并被两页复用
- PeriodCompare 与 Compare 都只渲染当前窗口
- Phase 18 的紧凑视口可用性没有因 diff 重做回归
