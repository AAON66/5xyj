---
phase: 19
slug: fusion-capability-enhancement
status: passed
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-09
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + ESLint + TypeScript/Vite build + Playwright |
| **Config file** | `backend/pytest.ini` (implicit via pytest discovery), `frontend/package.json`, `frontend/playwright.config.ts` |
| **Quick run command** | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_aggregate_service.py -q -k special_rule && python3 -m pytest backend/tests/test_aggregate_api.py -q -k "burden or feishu" && cd frontend && ./node_modules/.bin/eslint src/services/fusionRules.ts src/components/FusionRuleEditorDrawer.tsx src/services/aggregate.ts src/services/aggregateSessionStore.ts src/pages/SimpleAggregate.tsx tests/e2e/fusion-aggregate.spec.ts` |
| **Full suite command** | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_fusion_rules_api.py backend/tests/test_fusion_input_service.py -q && python3 -m pytest backend/tests/test_aggregate_service.py -q -k special_rule && python3 -m pytest backend/tests/test_aggregate_api.py -q -k "burden or feishu" && python3 -m pytest backend/tests/test_template_exporter.py backend/tests/test_api_compatibility.py backend/tests/test_salary_regression.py -q -k "fusion or salary or burden" && cd frontend && npm run lint && npm run build && npm run test:e2e` |
| **Estimated runtime** | ~8 minutes |

---

## Sampling Rate

- **After every task commit:** Run the task-specific pytest/eslint command listed below
- **After every plan wave:** Run the quick run command plus `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run test:e2e` after frontend changes
- **Before `/gsd-verify-work`:** Full suite must be green, including Playwright quick-aggregate checks
- **Max feedback latency:** ~8 minutes

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 1 | FUSE-03 | T-19-01 | Saved rules cannot silently target the wrong employee key or unsupported field | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_fusion_rules_api.py -q` | ✅ | ✅ green |
| 19-01-02 | 01 | 1 | FUSE-03 | T-19-02 | Rule CRUD preserves active/inactive state and reusable retrieval semantics | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_fusion_rules_api.py -q` | ✅ | ✅ green |
| 19-02-01 | 02 | 1 | FUSE-01 | T-19-03 | Burden adapter rejects ambiguous employee matches instead of misapplying values | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_fusion_input_service.py -q` | ✅ | ✅ green |
| 19-02-02 | 02 | 1 | FUSE-01 | T-19-04 | Mocked Feishu source mapping only imports explicitly mapped burden fields | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_aggregate_api.py -q -k "burden or feishu"` | ✅ | ✅ green |
| 19-03-01 | 03 | 2 | FUSE-01 | T-19-05 | Tool export receives overlay values while Salary export remains unchanged | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_template_exporter.py backend/tests/test_api_compatibility.py backend/tests/test_salary_regression.py -q -k "fusion or salary or burden"` | ✅ | ✅ green |
| 19-03-02 | 03 | 2 | FUSE-01,FUSE-03 | T-19-06 | Aggregate runtime applies persisted rules and optional burden source only to the current batch | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_aggregate_service.py -q -k special_rule && python3 -m pytest backend/tests/test_aggregate_api.py -q -k "burden or feishu"` | ✅ | ✅ green |
| 19-04-01 | 04 | 3 | FUSE-03 | T-19-07 | Quick aggregate UI saves and reuses rules without duplicating destructive actions on mobile | eslint | `cd /Users/mac/PycharmProjects/5xyj/frontend && ./node_modules/.bin/eslint src/services/fusionRules.ts src/components/FusionRuleEditorDrawer.tsx src/services/aggregate.ts src/services/aggregateSessionStore.ts src/pages/SimpleAggregate.tsx tests/e2e/fusion-aggregate.spec.ts` | ✅ | ✅ green |
| 19-04-02 | 04 | 3 | FUSE-01,FUSE-03 | T-19-08 | Browser-level flow can choose burden source, save a rule, rerun, and keep mobile operability | e2e | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run test:e2e` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_aggregate_api.py` — existing aggregate API coverage can host Phase 19 scenarios
- [x] `backend/tests/test_aggregate_service.py` — existing runtime orchestration tests can host overlay/rule application coverage
- [x] `backend/tests/test_template_exporter.py` — existing dual-template regression tests can host Salary/Tool boundary checks
- [x] `frontend/tests/e2e/responsive.spec.ts` / Playwright infra — existing browser harness can host quick aggregate behavior tests

*Existing infrastructure covers all phase requirements once Phase 19 scenarios are added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Feishu tenant connectivity with real credentials | FUSE-01 | Local CI/test env has no guaranteed tenant credentials; mocked client is sufficient for product logic but not network/auth reality | After implementation, open Feishu settings, choose a real config, run one burden-source fusion on staging, and confirm Tool export burden columns match the selected source |

---

## Validation Sign-Off

- [x] All planned tasks have `<automated>` verify targets or existing Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** execution complete
