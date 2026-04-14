---
phase: 20-compare-redesign-and-feishu-enhancement
plan: 01
title: "Phase 20 Plan 01: compare API 分页/过滤窗口合同"
subsystem: backend
tags: [compare, pagination, filters, fastapi, pytest]
dependency_graph:
  requires: []
  provides: [period-compare-window-contract]
  affects: [period-compare-ui, compare-diff-viewer]
tech_stack:
  added: []
  patterns: [fastapi-query-params, filtered-pagination, pytest-api-regression]
key_files:
  created: []
  modified:
    - backend/app/schemas/compare.py
    - backend/app/services/compare_service.py
    - backend/app/api/v1/compare.py
    - backend/tests/test_compare_api.py
decisions:
  - "账期对比先完成左右记录配对，再应用搜索/差异过滤，最后才分页，避免窗口切片破坏比对语义"
  - "summary groups 与 changed/same/left_only/right_only 统计都基于过滤后的结果重算，防止页面看到的页窗口和顶部统计不一致"
metrics:
  duration: "n/a"
  completed: "2026-04-09T23:22:19+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 4
requirements:
  - COMP-01
---

# Phase 20 Plan 01: compare API 分页/过滤窗口合同 Summary

Phase 20 的 compare 后端合同已经扩展到可支撑真正的 diff UI：账期对比支持服务端搜索、仅差异过滤和分页窗口元数据。

## What Was Done

### Task 1: 扩展 PeriodCompare schema 与查询参数
- 在 `PeriodCompareRead` 中新增 `page`、`page_size`、`total_pages`、`returned_row_count`、`diff_only`、`search_text`
- `/api/v1/compare/periods` 新增 `search_text` 与 `diff_only` 查询参数

### Task 2: 重写 compare service 的过滤/分页顺序并补回归
- `compare_periods()` 改为先在完整配对结果上执行搜索与 diff-only 过滤，再基于过滤结果分页
- 过滤后重新计算 grouped summary 和各类计数，避免 UI 统计错位
- `backend/tests/test_compare_api.py` 新增分页/过滤组合回归，并调整既有断言以匹配新增测试种子

## Verification Results

- `python3 -m pytest backend/tests/test_compare_api.py -q`
- 通过，覆盖 period compare 的分页、搜索、diff-only 组合，以及 batch compare 既有合同不回归

## Deviations from Plan

None - plan executed as intended.

## Commits

Deferred. Phase 20 本轮以内联执行完成，没有额外创建提交。

## Self-Check: PASSED

- Period compare API 已暴露窗口元数据
- 过滤与分页顺序符合 diff UI 预期
- compare 既有 batch/export 路径没有因为新 schema 回归
