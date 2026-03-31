---
phase: 9
slug: api-system
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | backend/pytest.ini or pyproject.toml |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v --timeout=60` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | AUTH-07 | unit | `pytest tests/test_api_key.py -k test_create_key` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | AUTH-08 | unit | `pytest tests/test_api_key.py -k test_auth_with_key` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | API-01 | integration | `pytest tests/test_api_endpoints.py -k test_query` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | API-02 | integration | `pytest tests/test_api_endpoints.py -k test_pagination` | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 2 | API-03 | unit | `pytest tests/test_api_docs.py -k test_openapi` | ❌ W0 | ⬜ pending |
| 09-02-04 | 02 | 2 | API-04 | integration | `pytest tests/test_api_endpoints.py -k test_error_codes` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api_key.py` — stubs for AUTH-07, AUTH-08
- [ ] `tests/test_api_endpoints.py` — stubs for API-01, API-02, API-04
- [ ] `tests/test_api_docs.py` — stubs for API-03

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Swagger UI accessible and grouped | API-03 | Browser-only visual verification | Open /docs, verify Chinese descriptions, grouping, examples visible |
| /docs restricted to admin | API-03 | Browser auth flow required | Try accessing /docs without login, verify redirect/block |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
