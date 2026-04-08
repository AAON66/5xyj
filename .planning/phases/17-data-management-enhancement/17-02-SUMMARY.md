---
phase: 17-data-management-enhancement
plan: 02
subsystem: data-management
tags: [multi-select, filter, match-status, api, frontend]
dependency_graph:
  requires: []
  provides: [multi-value-api, match-status-filter, multi-select-ui]
  affects: [data-management-page, data-management-api]
tech_stack:
  added: []
  patterns: [multi-value-query-params, in-clause-filtering, outerjoin-match-filter]
key_files:
  created:
    - backend/tests/test_data_management_service.py
  modified:
    - backend/app/api/v1/data_management.py
    - backend/app/services/data_management_service.py
    - frontend/src/pages/DataManagement.tsx
    - frontend/src/services/dataManagement.ts
decisions:
  - "matchStatus 默认值为 'matched' 而非 'all'，因为 HR 日常主要查看已匹配记录"
  - "多选值在 URL 中使用逗号分隔而非重复参数键，简化 URL 可读性"
  - "unmatched 过滤包含无 MatchResult 记录和非 MATCHED 状态记录，使用 outerjoin + or_ 实现"
metrics:
  duration: 12m
  completed: 2026-04-08
  tasks_completed: 2
  tasks_total: 2
  files_changed: 5
---

# Phase 17 Plan 02: Multi-select Filters + Match Status Summary

**One-liner:** 数据管理页面筛选改为多选下拉，新增匹配状态过滤，后端支持多值 Query 参数和 MatchResult JOIN 过滤

## What Was Built

### Task 1: 后端多值参数 + 匹配状态过滤 + 测试

**TDD 流程:**
- RED: 6 个测试覆盖多地区、多公司、匹配过滤(matched/unmatched/all)、级联选项过滤
- GREEN: 服务层 4 个函数签名改为 `regions: Optional[list[str]]`，使用 `.in_()` 过滤；records 新增 `match_filter` 参数，matched 使用 JOIN，unmatched 使用 outerjoin + or_
- API 层 4 个端点参数改为 `Optional[List[str]]`，records 端点新增 `match_status` 参数

**Commit:** f94c3db (RED), 9a3b845 (GREEN)

### Task 2: 前端多选下拉 + 匹配状态过滤 + URL 持久化

- 地区/公司/账期 Select 改为 `mode="multiple"`，每个顶部有全选选项 (`__ALL__`)
- `maxTagCount={2}` + `maxTagPlaceholder` 折叠显示
- 新增匹配状态单选下拉（全部/已匹配/未匹配），默认已匹配
- URL searchParams 使用逗号分隔存储多选值
- 级联关系保持：地区变化时清空公司和账期选中值
- Service 层参数改为数组类型，使用 `searchParams.append()` 多值追加

**Commit:** f95cf87

## Verification Results

- pytest backend/tests/test_data_management_service.py: 6/6 passed
- TypeScript 编译 (tsc --noEmit): 通过
- ESLint: 无新增错误（3 个预存错误在无关文件中）

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- All 5 key files exist on disk
- All 3 commits verified in git log (f94c3db, 9a3b845, f95cf87)
- All acceptance criteria counts verified (mode="multiple" x3, __ALL__ x1, maxTagCount x3, matchStatus x6, .in_() x11, MatchResult.match_status x2)
