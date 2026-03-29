---
phase: 5
slug: employee-portal
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 5 — Validation Strategy

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Quick run command** | `cd D:/execl_mix && .venv/Scripts/python.exe -m pytest tests/test_employee_portal.py -x -q` |
| **Full suite command** | `cd D:/execl_mix && .venv/Scripts/python.exe -m pytest tests/ backend/tests/ -v` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Quick run command
- **After every plan wave:** Full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | PORTAL-01,05 | unit | `pytest tests/test_employee_portal.py -k "insurance_breakdown"` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | PORTAL-02 | unit | `pytest tests/test_employee_portal.py -k "housing_fund"` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | PORTAL-04 | unit | `pytest tests/test_employee_portal.py -k "data_isolation"` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/test_employee_portal.py` — covers PORTAL-01, PORTAL-02, PORTAL-04, PORTAL-05

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 概览首页展示 | PORTAL-01 | 需浏览器验证 UI | 员工验证后确认看到个人信息+最新月份汇总 |
| 险种明细可展开 | PORTAL-05 | 需浏览器验证交互 | 点击展开查看各险种单位/个人拆分 |
| 历史记录浏览 | PORTAL-03 | 需浏览器验证 | 确认按月份倒序显示 |
| Token 过期跳转 | N/A | 需等待30分钟 | 等 token 过期后确认提示+跳转 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity
- [ ] Wave 0 covers all MISSING references
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
