---
phase: 20-compare-redesign-and-feishu-enhancement
plan: 04
title: "Phase 20 Plan 04: 飞书前端设置工作台、flags 刷新与 e2e"
subsystem: frontend
tags: [feishu, settings, feature-flags, react, playwright, responsive]
dependency_graph:
  requires: [db-backed-feishu-runtime-settings, effective-feishu-settings]
  provides: [feishu-settings-hub, sync-page-state-cta]
  affects: [feishu-settings-page, feishu-sync-page, mobile-regression]
tech_stack:
  added: []
  patterns: [refreshable-feature-flags, settings-hub, state-aware-empty-state]
key_files:
  created:
    - frontend/tests/e2e/feishu-settings.spec.ts
  modified:
    - frontend/src/services/feishu.ts
    - frontend/src/hooks/useFeishuFeatureFlag.ts
    - frontend/src/pages/FeishuSettings.tsx
    - frontend/src/pages/FeishuSync.tsx
    - frontend/tests/e2e/responsive.spec.ts
decisions:
  - "FeishuSettings 不再只是 SyncConfig 列表，而是合并运行时开关、凭证状态和同步目标管理的单页工作台"
  - "FeishuSync 在功能关闭或凭证缺失时显示明确 CTA，不再直接重定向回首页"
  - "flags 保存后显式 `refreshFlags()`，确保页面间状态切换不依赖整页刷新"
metrics:
  duration: "n/a"
  completed: "2026-04-09T23:22:19+08:00"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 5
requirements:
  - FEISHU-01
---

# Phase 20 Plan 04: 飞书前端设置工作台、flags 刷新与 e2e Summary

飞书前端配置流已经闭环：管理员可直接在页面里保存运行时开关和凭证，sync 页会感知当前状态并给出禁用/缺凭证的恢复入口。

## What Was Done

### Task 1: 扩展 feishu client 与 feature flags hook
- `frontend/src/services/feishu.ts` 新增 runtime settings 与 credentials 读写 client
- `useFeishuFeatureFlag()` 新增 `refreshFlags()`，供 settings 页保存后显式刷新

### Task 2: 重构 FeishuSettings 与 FeishuSync
- `FeishuSettings.tsx` 现在同时提供运行时开关、脱敏凭证状态、凭证编辑表单和 SyncConfig CRUD
- `FeishuSync.tsx` 在 sync disabled / credentials missing 两种状态下给出清晰提示与“去设置页” CTA
- 页面保留移动端可操作性，drawer/form/CTA 都在窄屏下继续工作

### Task 3: 新增浏览器级前端配置回归
- 新增 `frontend/tests/e2e/feishu-settings.spec.ts`
- 覆盖凭证保存、runtime flags 保存、sync disabled CTA、移动端 SyncConfig 创建
- 更新 `frontend/tests/e2e/responsive.spec.ts`，确保 Phase 18 的窄屏可用性继续成立

## Verification Results

- `cd frontend && ./node_modules/.bin/eslint src/services/feishu.ts src/hooks/useFeishuFeatureFlag.ts src/pages/FeishuSettings.tsx src/pages/FeishuSync.tsx tests/e2e/feishu-settings.spec.ts`
- `cd frontend && npm run test:e2e -- feishu-settings.spec.ts`
- `cd frontend && npm run test:e2e`

## Deviations from Plan

None - plan executed as intended.

## Commits

Deferred. Phase 20 本轮以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- settings 页已支持 runtime settings + credentials + SyncConfig 全部配置
- sync 页缺凭证/已禁用时不再沉默失败
- 浏览器级回归覆盖了桌面和移动端主流程
