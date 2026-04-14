---
phase: 17-data-management-enhancement
plan: 01
subsystem: data-processing
tags: [field-mapping, alias-rules, payment-base, header-normalizer]

requires:
  - phase: 13-parsing-pipeline
    provides: AliasRule dataclass and MANUAL_ALIAS_RULES mapping infrastructure
provides:
  - payment_base and payment_salary excludes rules that prevent insurance sub-column mismatches
affects: [data-normalization, batch-reparse, export]

tech-stack:
  added: []
  patterns: [excludes-based field disambiguation for AliasRule]

key-files:
  created: []
  modified:
    - backend/app/mappings/manual_field_aliases.py
    - backend/tests/test_header_normalizer.py

key-decisions:
  - "Use 8 insurance keywords as excludes tuple to reject all known insurance sub-column signatures"

patterns-established:
  - "AliasRule excludes pattern: when a generic field name appears as sub-column under insurance types, add insurance keywords to excludes"

requirements-completed: [DATA-04]

duration: 18min
completed: 2026-04-08
---

# Phase 17 Plan 01: payment_base/payment_salary Excludes Fix Summary

**AliasRule excludes 修复，防止 payment_base/payment_salary 错误匹配险种子列中的缴费基数/缴费工资**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-08T02:42:11Z
- **Completed:** 2026-04-08T02:59:52Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments
- payment_base AliasRule 添加 excludes，不再匹配 "基本养老保险(单位缴纳) / 缴费基数" 等险种子列签名
- payment_salary AliasRule 添加 excludes，不再匹配 "基本养老保险 / 缴费工资" 等险种子列签名
- 独立的 "缴费基数"、"缴费工资" 和 "职工明细 / 缴费基数"（武汉格式）仍可正确匹配
- 添加 13 个回归测试用例覆盖排除和匹配场景

## Task Commits

Each task was committed atomically (TDD):

1. **Task 1 RED: 添加失败测试** - `3fc51ad` (test)
2. **Task 1 GREEN: 修复 AliasRule excludes** - `366825a` (feat)

## Files Created/Modified
- `backend/app/mappings/manual_field_aliases.py` - 为 payment_salary 和 payment_base 的 AliasRule 添加 excludes 元组
- `backend/tests/test_header_normalizer.py` - 添加 TestPaymentBaseExcludesInsuranceColumns 和 TestPaymentSalaryExcludesInsuranceColumns 测试类

## Decisions Made
- 使用 8 个保险关键词 ("养老", "医疗", "失业", "工伤", "生育", "补充", "大病", "大额") 作为 excludes -- 覆盖所有已知险种名称变体

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- payment_base/payment_salary 映射修复完成，重新解析批次即可获得正确值
- 建议后续 plan 验证端到端：上传文件 -> 解析 -> 查看 payment_base 字段是否正确显示

---
*Phase: 17-data-management-enhancement*
*Completed: 2026-04-08*
