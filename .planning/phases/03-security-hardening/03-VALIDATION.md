---
phase: 3
slug: security-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | SEC-01 | integration | `python -m pytest tests/test_security.py::test_pii_endpoints_require_auth -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | SEC-02 | unit | `python -m pytest tests/test_security.py::test_login_rate_limit -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | SEC-03 | integration | `python -m pytest tests/test_audit.py -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | SEC-04 | unit | `python -m pytest tests/test_masking.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_security.py` — stubs for SEC-01, SEC-02
- [ ] `tests/test_audit.py` — stubs for SEC-03
- [ ] `tests/test_masking.py` — stubs for SEC-04
- [ ] pytest installed (`pip install pytest`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 前端审计日志页面展示 | SEC-03 | 需浏览器验证 UI | 管理员登录后导航到审计日志页面，验证日志列表和筛选功能 |
| 前端身份证号脱敏显示 | SEC-04 | 需浏览器验证渲染 | 以员工角色登录，查看个人记录中身份证号是否显示为 310***1234 格式 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
