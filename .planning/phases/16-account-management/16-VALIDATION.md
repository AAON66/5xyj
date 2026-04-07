---
phase: 16
slug: account-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) / vitest (frontend — not yet set up) |
| **Config file** | `backend/pytest.ini` or `pyproject.toml` |
| **Quick run command** | `cd backend && python -m pytest tests/test_users.py tests/test_auth.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_users.py tests/test_auth.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 1 | ACCT-04 | T-16-01 | Old password verified before change | unit | `python -m pytest tests/test_auth.py -k change_password -x -q` | ❌ W0 | ⬜ pending |
| 16-01-02 | 01 | 1 | ACCT-03 | T-16-02 | Reset sets must_change_password=True | unit | `python -m pytest tests/test_users.py -k reset_password -x -q` | ✅ | ⬜ pending |
| 16-02-01 | 02 | 2 | ACCT-01 | — | N/A | manual | Frontend user creation | ❌ | ⬜ pending |
| 16-02-02 | 02 | 2 | ACCT-02 | — | N/A | manual | Frontend role change | ❌ | ⬜ pending |
| 16-02-03 | 02 | 2 | ACCT-03 | — | N/A | manual | Frontend password reset | ❌ | ⬜ pending |
| 16-02-04 | 02 | 2 | ACCT-04 | — | N/A | manual | Frontend change password modal | ❌ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_auth.py` — add test cases for change-password endpoint (old password verification, must_change_password clear)
- [ ] `tests/test_users.py` — update reset_password test to verify must_change_password=True after reset

*Existing infrastructure covers backend test requirements. Frontend tests are manual.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin creates user via UI | ACCT-01 | Frontend interaction | Login as admin → /users → Create → Fill form → Verify user appears in list |
| Admin changes user role | ACCT-02 | Frontend interaction | Login as admin → /users → Edit user → Change role → Verify tag updates |
| Admin resets password | ACCT-03 | Frontend interaction | Login as admin → /users → Reset password → Verify success message |
| User changes own password | ACCT-04 | Frontend interaction | Login → Header dropdown → Change password → Verify old password required |
| Force change password modal | ACCT-04 | Frontend interaction | Login with must_change_password=true → Verify unclosable modal appears |
| Admin self-protection | ACCT-02 | Frontend interaction | Login as admin → /users → Verify own row has disabled switch and edit |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
