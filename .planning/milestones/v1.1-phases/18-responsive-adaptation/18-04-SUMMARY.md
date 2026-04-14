---
phase: 18-responsive-adaptation
plan: 04
title: "Phase 18 Plan 04: Mobile Workflow CTAs + Import Page Stacking"
subsystem: workflow-ui
tags: [responsive, sticky-cta, imports, results, exports]
dependency_graph:
  requires: [18-01]
  provides: [mobile-primary-actions, stacked-import-layouts]
  affects: [simple-aggregate, results, exports, imports]
tech_stack:
  added: []
  patterns: [single-mobile-primary-action, stacked-summary-cards, scrollable-preview-tables]
key_files:
  created: []
  modified:
    - frontend/src/pages/SimpleAggregate.tsx
    - frontend/src/pages/Results.tsx
    - frontend/src/pages/Exports.tsx
    - frontend/src/pages/Imports.tsx
    - frontend/src/pages/ImportBatchDetail.tsx
decisions:
  - "移动端固定底栏只保留唯一主动作，次要动作继续留在页面内容区"
  - "导入详情页在小屏改为单列信息流，预览表继续通过横向滚动保留可读性"
metrics:
  duration: "n/a"
  completed: "2026-04-09T11:33:47+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 5
requirements:
  - UX-03
---

# Phase 18 Plan 04: Mobile Workflow CTAs + Import Page Stacking Summary

上传、校验、匹配、导出链路已经具备手机端唯一主操作入口，导入页面也切换为更可读的小屏布局。

## What Was Done

### Task 1: 长流程页面移动端主操作
- `SimpleAggregate` 使用固定底部 `开始聚合并导出`
- `Results` 根据阶段切换 `执行数据校验` / `执行工号匹配`
- `Exports` 提供固定底部 `执行双模板导出`
- 三页在移动端统一增加 `paddingBottom: 96`

### Task 2: Imports / ImportBatchDetail 小屏重排
- 上传入口、摘要卡、详情卡片在手机端堆叠为单列
- 批次列表、标准化预览、字段映射仍保留横向滚动
- 批次详情头部和 `Descriptions` 根据宽度自动紧凑化

## Verification Results

- `cd frontend && ./node_modules/.bin/eslint src/pages/SimpleAggregate.tsx src/pages/Results.tsx src/pages/Exports.tsx src/pages/Imports.tsx src/pages/ImportBatchDetail.tsx`
- `cd frontend && npm run build`
- 均通过，退出码 0

## Deviations from Plan

None - plan executed exactly as written.

## Commits

Deferred. Phase 18 is waiting on human responsive UAT, so no completion commit was created in this run.

## Self-Check: PASSED

- Workflow pages expose only one mobile sticky primary action
- Imports and ImportBatchDetail are readable in single-column mobile layouts
- Preview and mapping tables remain accessible via horizontal scrolling
