---
phase: 19-fusion-capability-enhancement
plan: 02
title: "Phase 19 Plan 02: burden Excel / Feishu 输入适配器"
subsystem: backend
tags: [fusion, burden, excel, feishu, diagnostics]
dependency_graph:
  requires: [fusion-rule-model]
  provides: [burden-excel-adapter, burden-feishu-adapter, burden-diagnostics]
  affects: [aggregate-runtime]
tech_stack:
  added: []
  patterns: [header-alias-whitelist, duplicate-key-rejection, rules-first-import]
key_files:
  created:
    - backend/app/schemas/fusion_inputs.py
    - backend/app/services/fusion_input_service.py
  modified: []
decisions:
  - "burden 输入主键优先命中工号，其次身份证号"
  - "重复键与缺少主键的 burden 行不做模糊合并，直接进入 diagnostics"
metrics:
  duration: "n/a"
  completed: "2026-04-09T15:33:56+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
requirements:
  - FUSE-01
---

# Phase 19 Plan 02: burden Excel / Feishu 输入适配器 Summary

承担额输入源已经支持 Excel 和 Feishu 两种入口，并且在进入 runtime 前就完成了主键、重复和字段白名单收口。

## What Was Done

### Task 1: burden Excel 解析器
- 新增 `FusionBurdenRow` / `FusionBurdenDiagnostics`
- `parse_burden_workbook()` 支持表头别名映射、前 5 行表头扫描和金额转换
- 缺少工号/身份证号的行、重复 employee key 的行会被显式跳过并进入 diagnostics

### Task 2: burden Feishu 适配器
- `load_burden_rows_from_feishu()` 复用现有 `SyncConfig` 与 `FeishuClient.search_records`
- 只导入 `employee_id`、`id_number`、`personal_social_burden`、`personal_housing_burden` 白名单字段
- 修正了配置映射方向，确保用飞书列名读取、映射到系统字段

## Verification Results

- `python3 -m pytest backend/tests/test_fusion_input_service.py -q`
- 通过，覆盖 Excel 别名解析、重复键 diagnostics、Feishu 白名单映射与 diagnostics

## Deviations from Plan

None - plan executed as intended.

## Commits

Deferred. Phase 19 在本轮中以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- Excel / Feishu burden 入口都能产出统一 `FusionBurdenRow`
- diagnostics 会记录缺键、重复键和未识别场景
- Feishu 适配器没有越权导入非白名单字段
