---
phase: 24-v1.2-tech-debt
plan: "01"
subsystem: tech-debt/v1.2-audit
tags: [tech-debt, nyquist, validation, testing, feishu-oauth, audit-closure]
dependency_graph:
  requires: []
  provides:
    - feishu-oauth-smoke-coverage
    - phase-21-nyquist-approved
    - phase-22-nyquist-approved
  affects:
    - v1.2-milestone-archive-readiness
tech_stack:
  added: []
  patterns:
    - pytest-monkeypatch-async
    - artifact-per-test-isolation
    - retroactive-validation-alignment
key_files:
  created:
    - backend/tests/test_feishu_auth.py
  modified:
    - .planning/phases/21-feishu-field-mapping/21-VALIDATION.md
    - .planning/phases/22-oauth/22-VALIDATION.md
decisions:
  - 32+-char auth_secret_key test value adopted to avoid jwt InsecureKeyLengthWarning and sidestep UNSAFE_AUTH_SECRET_KEYS guard
  - monkeypatch applied to BOTH feishu_oauth_service and feishu_auth API module symbols (because feishu_auth.py imports via `from ... import _fetch_feishu_user_info`)
  - HUMAN-UAT pending items honestly flagged rather than back-dated as signed
  - 22-VALIDATION.md corrects 22-VERIFICATION.md "9/16 OAuth red" claim — OAuth core is 22/22 green; failures were in unrelated TestFeatureFlags / TestSettingsEndpoints
metrics:
  duration: ~15m
  completed: "2026-04-20T02:30:00Z"
  tasks_completed: 3
  tasks_total: 3
  files_changed: 3
  commits: 3
---

# Phase 24 Plan 01: v1.2 Tech-Debt Gap Closure Summary

Close 3 non-blocking items from v1.2-MILESTONE-AUDIT.md so the milestone can be cleanly archived: add 3 minimum-viable backend smoke tests for Feishu OAuth at the standard `backend/tests/` path, and retroactively lift Phase 21 / Phase 22 `VALIDATION.md` from `draft` → `approved` + `nyquist_compliant: true` with honest UAT pending flags.

## Completed Tasks

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add 3 OAuth smoke tests at standard backend path | `b89bdb5` | `backend/tests/test_feishu_auth.py` (new, 181 lines) |
| 2 | Upgrade Phase 21 VALIDATION.md to nyquist_compliant | `421340d` | `.planning/phases/21-feishu-field-mapping/21-VALIDATION.md` |
| 3 | Upgrade Phase 22 VALIDATION.md to nyquist_compliant | `8c8c549` | `.planning/phases/22-oauth/22-VALIDATION.md` |

## Verification Results

### Task 1 — Backend OAuth smoke tests

```
$ .venv/bin/python -m pytest backend/tests/test_feishu_auth.py -q
... [3 tests]
3 passed in 1.67s
```

Re-run confirms artifact-per-test cleanup is idempotent (3 passed in 1.58s). No real HTTP traffic to accounts.feishu.cn / open.feishu.cn — monkeypatch intercepts `_fetch_feishu_user_info` on both the service module and the API module symbol.

Combined run with the existing settings suite: `6 passed, 18 warnings in 1.97s` — no regression.

### Tasks 2 / 3 — VALIDATION.md frontmatter

```
$ grep -Fq "nyquist_compliant: true" .planning/phases/21-feishu-field-mapping/21-VALIDATION.md  # PASS
$ grep -Fq "nyquist_compliant: true" .planning/phases/22-oauth/22-VALIDATION.md                 # PASS
$ grep -Fq "TBD-" .planning/phases/21-feishu-field-mapping/21-VALIDATION.md                     # (no match - PASS)
$ grep -Fq "TBD-" .planning/phases/22-oauth/22-VALIDATION.md                                    # (no match - PASS)
```

All acceptance-criteria grep patterns for Phase 21 (21-01-T1 / 21-02-T3 / FMAP-01 / FMAP-04) and Phase 22 (22-01-T1 / 22-02-T2 / 22-03-T2 / OAUTH-01 / OAUTH-04) resolve to matches.

## Deviations from Plan

### Corrected Factual Claim

**[Plan text clarification] "原 22-VERIFICATION.md 声称 test_feishu_auth.py 9/16 红是幻觉 — 该文件从未存在"**

- **Found during:** Task 3 context gathering
- **Actual state on ded59f80 base:** `tests/test_feishu_auth.py` **does exist** (815 lines) with 34 tests: 29 pass / 5 fail. The failures are entirely in `TestFeatureFlags` + `TestSettingsEndpoints` (feature-flag / credentials endpoint tests, unrelated to OAuth). The OAuth core — `TestOAuthAutoBinding` / `TestOAuthPendingCandidates` / `TestConfirmBind` / `TestFeishuBind` — runs **22/22 green**.
- **What 22-VERIFICATION.md actually got wrong:** the attribution of "9/16 red" to OAuth tests. When verified on current base, the 9 originally-red OAuth tests have been repaired (Plan 03 state_signed migration + test fixture updates at commit `a0356f2`). Residual reds are a different tech-debt class.
- **Resolution in 22-VALIDATION.md:** The "Acknowledged Tech Debt" section documents this honestly: OAuth smoke coverage at `backend/tests/` was the real gap (now closed by Task 1); the `tests/test_feishu_auth.py` OAuth subset is already green and provides the full state coverage.
- **No code change required** — only documentation truth.

### No other deviations

Rules 1 / 2 / 3 auto-fixes: none triggered.
Rule 4 architectural changes: none proposed.
Authentication gates: none (all tests use monkeypatched HTTP).

## Threat Model Adherence

| Threat | Mitigation Applied |
|--------|--------------------|
| T-24-01 (real Feishu HTTP leak) | monkeypatch on both `backend.app.services.feishu_oauth_service._fetch_feishu_user_info` and `backend.app.api.v1.feishu_auth._fetch_feishu_user_info`; app_id=`test-app-id` / app_secret=`test-app-secret` (placeholder values). |
| T-24-02 (test DB cross-contamination) | `ARTIFACTS_ROOT / test_name` per-test directory with `shutil.rmtree` on entry; rerun idempotent. |
| T-24-03 (VALIDATION.md pending-as-green) | 21-VALIDATION sign-off shows 6/7 checked + final UAT unchecked; 22-VALIDATION shows 6/7 checked + final UAT unchecked. No pending item was mark-as-approved. |
| T-24-04 (test_secret leak) | `_TEST_AUTH_SECRET = "feishu-auth-smoke-test-secret-key-2026"` — 38 chars, not a production key, not in UNSAFE_AUTH_SECRET_KEYS list. `app_id=test-app-id`, `app_secret=test-app-secret` are clearly placeholder. |

## Known Stubs

None — 3 tests are real assertions against real app state; VALIDATION.md sections contain no TBD placeholders.

## Self-Check: PASSED

- [x] `backend/tests/test_feishu_auth.py` exists (181 lines, 3 tests green)
- [x] `.planning/phases/21-feishu-field-mapping/21-VALIDATION.md` has `nyquist_compliant: true`
- [x] `.planning/phases/22-oauth/22-VALIDATION.md` has `nyquist_compliant: true`
- [x] 3 atomic commits in git log: `b89bdb5`, `421340d`, `8c8c549`
- [x] All acceptance-criteria grep patterns resolve
- [x] No TBD- placeholders in either VALIDATION.md
