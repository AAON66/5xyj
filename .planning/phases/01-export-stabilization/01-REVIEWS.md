---
phase: 1
reviewers: [codex]
reviewed_at: 2026-03-27T15:17:30Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 1

## Codex Review (GPT-5.4)

### Plan 01-01: Split monolithic exporter + Salary regression tests

**Summary:** This is the right first move. Splitting the current monolith before changing Tool logic reduces blast radius, and a thin facade preserves downstream callers. The plan is directionally strong for EXPORT-02 and EXPORT-03, but it needs sharper safeguards around API compatibility, shared helper ownership, and test selection.

**Strengths:**
- Correct dependency ordering: refactor first, behavior fix second
- Thin facade approach minimizes churn for callers such as `batch_export_service`
- Explicit separation matches the phase goal and future maintainability needs
- Salary regression protection is appropriately prioritized
- "No logic changes" is the correct discipline for this wave

**Concerns:**
- `HIGH`: The current exporter has shared helper logic, region-specific handling, and merge behavior. A "mechanical" split can still change behavior through import cycles, moved constants, or subtly altered helper access patterns
- `HIGH`: Three Salary snapshot tests may be too narrow if they do not cover edge-case branches (burden/housing calculations, region-specific resolution)
- `MEDIUM`: The plan does not explicitly protect the public API surface. If the facade changes import paths or symbols, callers can break
- `MEDIUM`: Adding a separate snapshot suite may duplicate existing exporter regression coverage
- `LOW`: "No shared mutable state" is stated, but the plan does not say how constants/context builders will be kept immutable

**Suggestions:**
- Add one explicit API-compatibility test for `backend.app.exporters` public imports
- Capture regression baselines from current output before the refactor
- Choose Salary regression fixtures that hit more than the happy path
- Reuse and extend the existing exporter test suite instead of creating a parallel snapshot-only testing style
- Define helper ownership up front: pure shared helpers in `export_utils.py`, template-specific row builders only in template modules

**Risk Assessment:** MEDIUM

---

### Plan 01-02: Fix Tool template alignment + dual export verification

**Summary:** This plan attacks the actual defect well. The current Tool row builder is tightly coupled to Salary row positions, so rewriting `_tool_row_values` as an explicit 42-position mapping is a sensible fix. The main risk is manual off-by-one drift.

**Strengths:**
- Targets the real root cause: positional coupling to `_salary_row_values`
- TDD is a good fit because the bug is structural and easy to encode with failing tests
- Position-by-position mapping makes the Tool exporter auditable
- Dual export verification aligns directly with EXPORT-04
- Decoupling Tool from Salary reduces future regression risk

**Concerns:**
- `HIGH`: A handwritten 42-element list is still easy to misalign, especially with spacer columns and `None` positions. Length test alone does not prove correctness
- `HIGH`: The plan does not explicitly say the mapping will be verified against the real template workbook, not just `TOOL_HEADERS`
- `MEDIUM`: Dual export "success" is not enough — Salary output must remain identical, need Salary non-regression assertion
- `MEDIUM`: Full decoupling can accidentally duplicate business calculations that should remain shared
- `LOW`: Error handling is underspecified — if the row builder returns wrong length, the exporter should fail loudly

**Suggestions:**
- Keep derived amount calculations in shared pure helpers; only make the Tool column ordering explicit
- Add a guard test asserting exact Tool cell values at known coordinates in the generated workbook
- Add a failure-fast assertion in code that Tool row length matches `TOOL_HEADERS` length
- Include a Salary regression assertion in this wave as well
- Test with at least two representative data shapes (straightforward + edge case with housing/supplementary amounts)

**Risk Assessment:** MEDIUM

---

## Consensus Summary

### Agreed Strengths
- Two-wave structure (refactor first, fix second) is sound and reduces risk
- Targeting the real root cause (positional coupling) is correct
- Salary regression protection is appropriately prioritized

### Agreed Concerns
- **HIGH**: Mechanical split can still break behavior through import cycles and helper placement
- **HIGH**: Test coverage may be too narrow (single sample, no edge cases)
- **MEDIUM**: Public API compatibility not explicitly guarded
- **MEDIUM**: Manual 42-element list is fragile for off-by-one errors

### Key Recommendations
1. Add explicit API compatibility test for public imports
2. Extend test fixtures beyond single sample to include edge cases (housing, burden, region-specific)
3. Add runtime length guard in `_tool_row_values` (assert len matches TOOL_HEADERS)
4. Verify against real workbook layout, not just the constant
5. Include Salary regression checks in Plan 01-02 as well

---
*Review completed: 2026-03-27*
*Reviewers: Codex (GPT-5.4)*
