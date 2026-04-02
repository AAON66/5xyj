---
phase: 10
slug: feishu-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3 (backend) / vitest or manual (frontend) |
| **Config file** | `backend/pytest.ini` or pyproject.toml |
| **Quick run command** | `pytest tests/ -x -q --tb=short` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | FEISHU-01 | unit+integration | `pytest tests/test_feishu_sync.py -k push` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | FEISHU-02 | unit+integration | `pytest tests/test_feishu_sync.py -k pull` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | FEISHU-03 | unit | `pytest tests/test_feishu_sync.py -k status` | ❌ W0 | ⬜ pending |
| 10-01-04 | 01 | 1 | FEISHU-04 | unit | `pytest tests/test_feishu_sync.py -k manual` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 2 | FEISHU-05 | unit+integration | `pytest tests/test_feishu_oauth.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_feishu_sync.py` — stubs for FEISHU-01 through FEISHU-04
- [ ] `tests/test_feishu_oauth.py` — stubs for FEISHU-05
- [ ] `tests/conftest.py` — shared fixtures for Feishu API mocking (httpx mock)

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drag-and-drop field mapping UI | FEISHU-01/02 | Visual interaction cannot be automated without browser test | Open mapping page, drag system fields to Feishu columns, verify connections render |
| NDJSON streaming progress | FEISHU-01/02 | Real-time streaming hard to verify in unit tests | Trigger sync, observe progress bar updating in real-time |
| Feishu OAuth redirect flow | FEISHU-05 | Requires real Feishu app credentials | Click "飞书登录", verify redirect to Feishu, login, verify redirect back with JWT |
| Conflict preview UI | FEISHU-02 | Visual comparison requires browser | Pull data with conflicts, verify diff highlighting and strategy buttons |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
