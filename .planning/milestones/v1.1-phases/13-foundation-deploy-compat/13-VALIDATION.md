---
phase: 13
slug: foundation-deploy-compat
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (frontend) |
| **Config file** | `backend/pytest.ini`, `frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v && cd ../frontend && npm run lint && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | 01 | 1 | INFRA-01 | unit | `python -m pytest tests/ -k "slots or dataclass"` | ⬜ W0 | ⬜ pending |
| TBD | 01 | 1 | INFRA-02 | unit | `python -m pytest tests/ -k "requirements"` | ⬜ W0 | ⬜ pending |
| TBD | 01 | 1 | INFRA-03 | unit | `python -m pytest tests/test_audit.py` | ✅ | ⬜ pending |
| TBD | 02 | 2 | INFRA-04 | unit | `python -m pytest tests/ -k "tech_debt"` | ⬜ W0 | ⬜ pending |
| TBD | 02 | 2 | FUSE-02 | integration | `cd frontend && npm run build` | ✅ | ⬜ pending |
| TBD | 02 | 2 | FUSE-04 | integration | `cd frontend && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_python39_compat.py` — stubs for INFRA-01 (slots removal verification)
- [ ] `tests/test_ip_resolution.py` — stubs for INFRA-03 (audit IP parsing)

*Existing infrastructure covers most phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Python 3.9 server boot | INFRA-01 | Requires 3.9 runtime | Deploy to 3.9 server, run `python -c "import backend.app.main"` |
| Nginx X-Forwarded-For | INFRA-03 | Requires reverse proxy | Deploy behind nginx, check audit log IP != 127.0.0.1 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
