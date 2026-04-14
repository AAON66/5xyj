---
phase: 17
slug: data-management-enhancement
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — uses default pytest discovery |
| **Quick run command** | `pytest backend/tests/test_data_management_service.py backend/tests/test_header_normalizer.py -x` |
| **Full suite command** | `pytest backend/tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest backend/tests/test_data_management_service.py backend/tests/test_header_normalizer.py -x`
- **After every plan wave:** Run `pytest backend/tests/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green + `npm run lint && npm run build`
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | DATA-04 | — | N/A | unit | `pytest backend/tests/test_header_normalizer.py -x -k payment_base` | ❌ W0 | ⬜ pending |
| 17-02-01 | 02 | 1 | DATA-01 | — | FastAPI Query List[str] type validation | unit | `pytest backend/tests/test_data_management_service.py -x -k multi` | ❌ W0 | ⬜ pending |
| 17-02-02 | 02 | 1 | DATA-02 | — | N/A | unit | `pytest backend/tests/test_data_management_service.py -x -k match_filter` | ❌ W0 | ⬜ pending |
| 17-03-01 | 03 | 2 | DATA-03 | — | N/A | unit | `pytest backend/tests/test_import_batches_api.py -x -k delete` | ✅ partial | ⬜ pending |
| 17-04-01 | 04 | 2 | DATA-01 | — | N/A | manual | `npm run lint && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_data_management_service.py` — stubs for DATA-01 (multi-filter), DATA-02 (match_filter)
- [ ] `backend/tests/test_header_normalizer.py` — add payment_base excludes test cases for DATA-04

*Existing `test_import_batches_api.py` partially covers DATA-03 delete scenarios.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 多选下拉交互 + 级联联动 | DATA-01 | 前端交互无 E2E 测试框架 | 1. 打开数据管理页面 2. 地区多选 → 验证公司下拉联动 3. 全选 → 验证全选/取消 4. 检查 URL searchParams |
| 匹配状态默认值 | DATA-02 | 前端默认值行为 | 1. 打开数据管理页面 2. 验证匹配状态下拉默认选中"已匹配" |
| 删除确认弹窗内容 | DATA-03 | UI 弹窗内容展示 | 1. 选中批次点击删除 2. 验证弹窗显示关联数据条数 3. 确认删除后验证数据清理 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
