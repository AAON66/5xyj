---
phase: 11
slug: intelligence-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3 (backend) / tsc + build (frontend) |
| **Config file** | backend pytest config |
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
| 11-01-01 | 01 | 1 | INTEL-01 | unit | `pytest tests/test_period_compare.py` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | INTEL-02 | unit | `pytest tests/test_anomaly_detection.py` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | INTEL-03 | unit | `pytest tests/test_housing_fund.py` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 2 | INTEL-04 | unit | `npx tsc --noEmit && npm run build` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_period_compare.py` — stubs for INTEL-01
- [ ] `tests/test_anomaly_detection.py` — stubs for INTEL-02
- [ ] `tests/test_housing_fund.py` — stubs for INTEL-03 (extend existing)

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cross-period comparison table with color highlighting | INTEL-01 | Visual rendering | Open comparison page, select two periods, verify green/red highlighting |
| Anomaly threshold slider interaction | INTEL-02 | Interactive UI | Adjust sliders, verify detection results update |
| Field mapping inline editor | INTEL-04 | Complex UI interaction | Navigate to import results, modify mapping, verify change applies |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
