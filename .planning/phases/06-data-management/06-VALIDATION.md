---
phase: 6
slug: data-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured) |
| **Config file** | backend/pyproject.toml |
| **Quick run command** | `pytest tests/test_data_management.py tests/test_data_quality.py tests/test_import_created_by.py -x -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_data_management.py tests/test_data_quality.py tests/test_import_created_by.py -x -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | DATA-01 | integration | `pytest tests/test_data_management.py::test_filter_records -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | DATA-01 | integration | `pytest tests/test_data_management.py::test_filter_options -x` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | DATA-01 | manual-only | Manual browser test (URL query param persistence) | N/A | ⬜ pending |
| 06-01-04 | 01 | 1 | DATA-02 | unit | `pytest tests/test_data_management.py::test_employee_summary -x` | ❌ W0 | ⬜ pending |
| 06-01-05 | 01 | 1 | DATA-02 | unit | `pytest tests/test_data_management.py::test_period_summary -x` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | DATA-03 | unit | `pytest tests/test_data_quality.py::test_missing_fields -x` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 1 | DATA-03 | unit | `pytest tests/test_data_quality.py::test_anomalous_amounts -x` | ❌ W0 | ⬜ pending |
| 06-02-03 | 02 | 1 | DATA-03 | unit | `pytest tests/test_data_quality.py::test_duplicate_records -x` | ❌ W0 | ⬜ pending |
| 06-02-04 | 02 | 1 | DATA-04 | integration | `pytest tests/test_import_created_by.py -x` | ❌ W0 | ⬜ pending |
| 06-02-05 | 02 | 1 | DATA-04 | unit | `pytest tests/test_import_created_by.py::test_legacy_null -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_data_management.py` — stubs for DATA-01, DATA-02 (filter records, filter options, employee summary, period summary)
- [ ] `tests/test_data_quality.py` — stubs for DATA-03 (missing fields, anomalous amounts, duplicate records)
- [ ] `tests/test_import_created_by.py` — stubs for DATA-04 (created_by populated, legacy null)
- [ ] Test fixtures: NormalizedRecord factory with varied region/company/period data

*Existing infrastructure covers framework setup; only test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| URL query param persistence | DATA-01 | Browser URL bar state cannot be tested in pytest | 1. Apply filters on data browse page 2. Copy URL 3. Open in new tab 4. Verify same filters are applied |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
