---
phase: 11
reviewers: [claude]
reviewed_at: 2026-04-04T12:00:00Z
plans_reviewed: [11-01-PLAN.md, 11-02-PLAN.md, 11-03-PLAN.md, 11-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 11

## Claude Review

# Phase 11: Intelligence & Polish — Plan Review

## 1. Summary Assessment

Phase 11 comprises 4 plans across 2 waves, implementing 4 requirements (INTEL-01 through INTEL-04). The plans are well-structured, incremental extensions of existing infrastructure rather than greenfield builds. They follow a sensible wave pattern: Wave 1 (Plans 01, 02) builds backend services in parallel, Wave 2 (Plans 03, 04) builds frontend pages that depend on Wave 1 outputs. The scope is appropriate and well-bounded by the 15 decisions in 11-CONTEXT.md.

**Overall verdict: READY with minor issues to address.**

---

## 2. Strengths

- **Strong reuse of existing patterns.** All 4 plans explicitly reference and extend existing services (`compare_service.py`, `housing_fund_service.py`, `mapping_service.py`) rather than building from scratch.
- **Clear wave dependency structure.** Plan 03 depends on Plan 01, Plan 04 depends on Plan 02. Plans 01 and 02 are independent and can execute in parallel.
- **Thorough `must_haves` contracts.** Each plan specifies truths, artifacts (with `contains` matchers), and key_links — providing verifiable success criteria beyond just "tests pass."
- **Unicode escape enforcement.** Every plan includes `grep -P '\\u[0-9A-Fa-f]{4}'` checks, addressing a known historical issue (commit `e67c314`).
- **Comprehensive research.** 11-RESEARCH.md identifies 5 pitfalls with mitigations, documents the Wuhan sample gap, and provides concrete code examples.
- **Audit trail design.** D-15 is properly threaded through Plans 01, 02, and 04 — anomaly status changes and mapping overrides both log to audit.
- **TDD approach in Plan 01.** Behaviors are specified before implementation actions.

---

## 3. Concerns

### HIGH Severity

**H1: Validation strategy mismatch with actual plans.**
The `11-VALIDATION.md` lists task `11-01-03` for INTEL-03 (housing fund) under Plan 01, but housing fund work is actually in Plan 02. It also maps only 4 tasks across all plans when there are 8 tasks total (2 per plan). This validation map is incomplete and will cause confusion during execution.

**H2: No database migration strategy for AnomalyRecord.**
Plan 01 creates a new SQLAlchemy model (`AnomalyRecord`) but never mentions Alembic migrations or table creation. If the project uses Alembic, a migration step is missing.

**H3: Plan 01 Task 1 is oversized.**
Task 1 of Plan 01 covers 8 distinct deliverables: period comparison service, compare schemas, compare API, AnomalyRecord model, anomaly threshold config, anomaly detection service, anomaly schemas, and tests for both features. This is effectively 2-3 tasks bundled into one, increasing risk of partial failure and making atomic commits difficult.

### MEDIUM Severity

**M1: Anomaly detection performance not addressed.**
`detect_anomalies()` loads all records for both periods into memory. For companies with thousands of employees, this could be slow or OOM. No batching specified for the detection process itself.

**M2: No handling of duplicate anomaly records on re-detection.**
If HR runs detection for the same two periods twice, duplicates will be created. No upsert logic, no "clear previous results" step, and no unique constraint on `(employee_identifier, left_period, right_period, field_name)`.

**M3: Plan 03 depends on `11-01-SUMMARY.md` that doesn't exist yet.**
The context section references a file that is an output of Plan 01 execution.

**M4: Frontend plans (03, 04) have no automated tests.**
Only TypeScript compilation and build success. Complex business logic (color-coding, pagination, batch operations) in AnomalyDetection.tsx has no tests.

**M5: Inconsistent page_size defaults.**
Plan 01 uses `page_size=50` for comparison, Plan 03 specifies 20 rows default, anomaly list uses 20.

### LOW Severity

**L1:** Plan 04 mapping service reads may be stale.
**L2:** Anomaly threshold slider range (0-100%) may be too wide. Consider 5-80%.
**L3:** No error handling specified for period comparison with no data.

---

## 4. Suggestions

1. **Split Plan 01 Task 1** into two tasks: (a) period comparison + tests, (b) anomaly model + detection + tests
2. **Add upsert/idempotency logic** to `detect_anomalies()` — unique constraint or clear-before-detect
3. **Fix 11-VALIDATION.md** to correctly map all 8 tasks
4. **Add migration mention** to Plan 01 (Alembic migration for AnomalyRecord)
5. **Consider chunked processing** in `detect_anomalies()` for large datasets
6. **Align page_size defaults** across backend and frontend to 20
7. **Add basic frontend tests** for anomaly status update logic and threshold mapping

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Plan 01 Task 1 too large, partial failure | Medium | Medium | Split into 2 tasks |
| Duplicate anomaly records on re-run | High | Medium | Add unique constraint + upsert |
| Wuhan housing fund sample missing | Medium | Low | Skip test with documentation |
| Performance issue with large period comparison | Low | Medium | Pagination planned; add chunking |
| Missing DB migration breaks deployment | Medium | High | Add explicit migration step |
| Frontend visual bugs undetected | Medium | Low | Manual verification acceptable |
| Stale summary dependency in Plan 03 | Low | Low | Executor reads actual code |

**Overall risk: MODERATE.**

---

## Consensus Summary

*(Single reviewer — no cross-reviewer consensus available.)*

### Key Strengths
- Strong reuse of existing services and patterns
- Clear wave dependency structure with parallel backend execution
- Unicode escape enforcement in all acceptance criteria
- Comprehensive audit trail design

### Top Concerns (must address before execution)
1. **H2:** Missing Alembic migration for AnomalyRecord model → add migration step to Plan 01
2. **H3:** Plan 01 Task 1 oversized (8 deliverables) → split into 2 tasks
3. **M2:** Duplicate anomaly records on re-detection → add unique constraint or clear-before-detect

### Improvement Suggestions
- Add chunked processing for anomaly detection on large datasets (M1)
- Align page_size defaults to 20 across all plans (M5)
- Fix VALIDATION.md to match actual 8-task structure (H1)
