---
phase: 19-fusion-capability-enhancement
plan: 03
title: "Phase 19 Plan 03: aggregate runtime overlay + Tool/Salary 导出边界"
subsystem: backend
tags: [fusion, aggregate, exporter, tool-template, salary-template]
dependency_graph:
  requires: [fusion-rule-model, burden-excel-adapter, burden-feishu-adapter]
  provides: [fusion-runtime-overlay, tool-only-burden-export, salary-trimmed-structure]
  affects: [aggregate-api, export-utils, template-exporter]
tech_stack:
  added: []
  patterns: [overlay-payload, rule-overrides-burden, tool-only-export-boundary]
key_files:
  created:
    - backend/app/services/fusion_runtime_service.py
  modified:
    - backend/app/api/v1/aggregate.py
    - backend/app/services/aggregate_service.py
    - backend/app/schemas/aggregate.py
    - backend/app/exporters/export_utils.py
    - backend/app/exporters/salary_exporter.py
    - backend/tests/test_aggregate_api.py
    - backend/tests/test_aggregate_service.py
    - backend/tests/test_template_exporter.py
    - backend/tests/test_api_compatibility.py
    - backend/tests/test_salary_regression.py
    - backend/tests/test_template_exporter_regression.py
decisions:
  - "aggregate contract 新增 burden source / fusion rule 字段，但保持旧调用不传这些字段时仍可运行"
  - "显式承担额覆盖写入 `raw_payload.fusion_overrides`，由导出器读取，避免新增 NormalizedRecord 列"
  - "Salary 输出删除承担额列，Tool 保留承担额列并读取 overlay 值"
metrics:
  duration: "n/a"
  completed: "2026-04-09T15:33:56+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 12
requirements:
  - FUSE-01
  - FUSE-03
---

# Phase 19 Plan 03: aggregate runtime overlay + Tool/Salary 导出边界 Summary

Phase 19 的后端主链路已经真正贯通。快速融合现在可以接收 burden source 和特殊规则，并把承担额只注入 Tool 模板，不再污染 Salary 模板。

## What Was Done

### Task 1: aggregate contract 与 runtime overlay
- `aggregate` / `aggregate/stream` 新增 `burden_file`、`burden_source_mode`、`burden_feishu_config_id`、`fusion_rule_ids`
- 新增 `fusion_runtime_service.py`，实现 burden source -> special rule 的覆盖顺序和 diagnostics 汇总
- 在 `aggregate_service.py` 里把 overlay 应用到 `NormalizedRecord.raw_payload.fusion_overrides`，并把提示信息回传给 API 结果

### Task 2: Tool-only burden export + Salary 结构回退
- `export_utils.py` 改为从显式 `fusion_overrides` 读取承担额，没有命中时回退为 0
- `salary_exporter.py` 删除承担额列并在导出时裁掉旧模板的两列尾部 burden 列
- `tool_exporter.py` 保持承担额列位置不变，但改由 overlay 驱动

## Verification Results

- `python3 -m pytest backend/tests/test_aggregate_service.py -q -k special_rule`
- `python3 -m pytest backend/tests/test_aggregate_api.py -q -k "burden or feishu"`
- `python3 -m pytest backend/tests/test_template_exporter.py backend/tests/test_api_compatibility.py backend/tests/test_salary_regression.py -q -k "fusion or salary or burden"`
- 全部通过

## Deviations from Plan

- 没有新增 `schemas/aggregate.py` 的复杂 diagnostics 对象，而是用 `fusion_messages` 收口最终提示信息，避免快速融合返回结构过度复杂。

## Commits

Deferred. Phase 19 在本轮中以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- runtime overlay 优先级为 burden source -> special rule
- Tool 模板承担额来自显式 overlay，Salary 模板不再输出承担额列
- 旧 aggregate 调用在不传新字段时仍可正常导出
