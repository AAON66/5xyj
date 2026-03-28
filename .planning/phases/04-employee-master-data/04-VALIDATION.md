---
phase: 4
slug: employee-master-data
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none |
| **Quick run command** | `cd D:/execl_mix && .venv/Scripts/python.exe -m pytest backend/tests/test_employee_master_api.py -x -q` |
| **Full suite command** | `cd D:/execl_mix && .venv/Scripts/python.exe -m pytest tests/ backend/tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | MASTER-01 | unit | `pytest backend/tests/test_employee_master_api.py -x -k "region"` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | MASTER-02 | unit | `pytest backend/tests/test_employee_master_api.py -x -k "import"` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | MASTER-03 | unit | `pytest backend/tests/test_employee_master_api.py -x -k "filter or list"` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | MASTER-04 | unit | `pytest backend/tests/test_matching_service.py -x -k "employee_id"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_employee_master_api.py` — extend with region CRUD, import upsert, filter tests
- [ ] `backend/tests/test_matching_service.py` — extend with employee_id dimension matching tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 前端 region/company 筛选交互 | MASTER-03 | 需浏览器验证 UI | HR 登录后在员工列表页使用 region 和 company 下拉筛选 |
| 前端导入结果反馈 | MASTER-02 | 需浏览器验证渲染 | 上传 Excel 后确认显示新增/更新/失败统计 |
| 前端分页交互 | MASTER-03 | 需浏览器验证 | 员工超过 20 条时翻页功能正常 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
