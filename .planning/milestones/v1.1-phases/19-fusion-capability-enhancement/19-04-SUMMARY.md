---
phase: 19-fusion-capability-enhancement
plan: 04
title: "Phase 19 Plan 04: SimpleAggregate UI + fusion e2e"
subsystem: frontend
tags: [fusion, ui, quick-aggregate, playwright, mobile]
dependency_graph:
  requires: [fusion-runtime-overlay]
  provides: [fusion-rule-editor-ui, burden-source-ui, fusion-browser-coverage]
  affects: [simple-aggregate, aggregate-session, e2e-suite]
tech_stack:
  added: []
  patterns: [single-mobile-cta, drawer-rule-editor, multipart-payload-verification]
key_files:
  created:
    - frontend/src/services/fusionRules.ts
    - frontend/src/components/FusionRuleEditorDrawer.tsx
    - frontend/tests/e2e/fusion-aggregate.spec.ts
  modified:
    - frontend/src/services/aggregate.ts
    - frontend/src/services/aggregateSessionStore.ts
    - frontend/src/pages/SimpleAggregate.tsx
decisions:
  - "规则编辑抽屉直接复用现有 API client，不在页面里内联 CRUD 细节"
  - "飞书承担额来源复用 `fetchSyncConfigs()`，不新增第二套配置源"
  - "手机端继续保留单一 sticky 主按钮，新增配置全部放在表单区而不是新增底部动作"
metrics:
  duration: "n/a"
  completed: "2026-04-09T15:33:56+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
requirements:
  - FUSE-01
  - FUSE-03
---

# Phase 19 Plan 04: SimpleAggregate UI + fusion e2e Summary

快速融合页已经把 Phase 19 的能力暴露给用户，包括承担额来源选择、特殊规则创建/复用，以及浏览器级请求合同验证。

## What Was Done

### Task 1: fusion rules 前端 service 与规则编辑抽屉
- 新增 `fusionRules.ts`，提供 `fetch/create/update/delete` 规则接口
- 新增 `FusionRuleEditorDrawer`，支持 scope、targetField、overrideValue、note 编辑
- `SimpleAggregate` 页面加载 active rules，支持多选复用和单条编辑

### Task 2: aggregate 表单扩展与 Playwright 覆盖
- `aggregate.ts` 和 `aggregateSessionStore.ts` 扩展 burden source / fusion rule 请求字段
- `SimpleAggregate.tsx` 新增承担额来源区、飞书配置选择、规则区和融合提示展示
- 新增 `fusion-aggregate.spec.ts`，断言手机端只有一个 sticky 主按钮，并验证 multipart 请求体包含 `burden_source_mode`、`burden_feishu_config_id`、`fusion_rule_ids`

## Verification Results

- `cd frontend && ./node_modules/.bin/eslint src/services/fusionRules.ts src/components/FusionRuleEditorDrawer.tsx src/services/aggregate.ts src/services/aggregateSessionStore.ts src/pages/SimpleAggregate.tsx tests/e2e/fusion-aggregate.spec.ts`
- `cd frontend && npm run test:e2e`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- 全部通过；`npm run lint` 仍保留 2 条历史 fast-refresh warning

## Deviations from Plan

- 为了让 Playwright 稳定上传文件，`SimpleAggregate` 给上传容器补了 test hook wrapper，而不是依赖 Ant `Dragger` 的内部 DOM 结构。

## Commits

Deferred. Phase 19 在本轮中以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- 规则可以在快速融合页创建、保存、自动选中并复用
- Feishu burden source 复用现有同步配置接口
- 手机端 sticky CTA 仍然只有一个，没有被新增配置区破坏
