---
phase: 22
slug: oauth
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + vitest/manual (frontend) |
| **Config file** | `backend/pytest.ini` or `pyproject.toml` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v && cd ../frontend && npm run lint && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | OAUTH-01, OAUTH-02 | T-22-01 | OAuth callback validates state | unit | `pytest tests/test_oauth_matching.py` | ❌ W0 | ⬜ pending |
| 22-01-02 | 01 | 1 | OAUTH-03 | — | Candidate list uses masked employee_id | unit | `pytest tests/test_oauth_matching.py` | ❌ W0 | ⬜ pending |
| 22-01-03 | 01 | 1 | OAUTH-04 | T-22-02 | Bind requires JWT auth | unit | `pytest tests/test_oauth_bind.py` | ❌ W0 | ⬜ pending |
| 22-02-01 | 02 | 2 | OAUTH-01 | — | N/A | manual | frontend visual check | N/A | ⬜ pending |
| 22-02-02 | 02 | 2 | OAUTH-03 | — | N/A | manual | frontend visual check | N/A | ⬜ pending |
| 22-02-03 | 02 | 2 | OAUTH-04 | — | N/A | manual | frontend visual check | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_oauth_matching.py` — stubs for OAUTH-01, OAUTH-02, OAUTH-03 (三级匹配 + 候选列表)
- [ ] `tests/test_oauth_bind.py` — stubs for OAUTH-04 (绑定/解绑)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 飞书登录完整流程 | OAUTH-01 | 需要真实飞书 OAuth | 点击飞书登录，完成扫码/自动登录，验证跳转到系统主页 |
| 同名候选列表 Modal | OAUTH-03 | 视觉 UI 验证 | 用同名飞书账号登录，确认弹出候选列表 Modal，选择后成功绑定 |
| 绑定飞书卡片 | OAUTH-04 | 视觉 UI 验证 | 在设置页点击绑定飞书，完成 OAuth，确认显示已绑定状态 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
