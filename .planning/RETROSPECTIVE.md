# Retrospective

## Milestone: v1.0 - Brownfield Hardening Baseline

**Shipped:** 2026-03-26
**Phases:** 4 | **Plans:** 6

### What Was Built

- Non-local auth startup now rejects unsafe defaults when the guardrail is correctly configured.
- Streamed uploads now enforce size limits and clean up partial artifacts on the covered API paths.
- Dual-template export verification now runs against repo-controlled fixtures or explicit paths.
- Supported operator and future-agent workflows now have one documented lane, with rescue tooling demoted and separated.

### What Worked

- The hardening scope stayed narrow and aligned with the existing brownfield runtime.
- Repo-controlled fixtures materially improved export verification portability.
- Operator docs and `.planning/` state became much easier to navigate after the Phase 4 cleanup.

### What Was Inefficient

- Phase 1 and Phase 2 were executed without formal phase verification reports, which created avoidable milestone audit debt.
- The supported deployment docs drifted from the actual Phase 1 settings contract.
- The quick aggregate stream entrypath drifted from the intended Phase 2 streamed-enforcement guarantee.

### Patterns Established

- Hardening work should preserve the current business workflow and narrow changes to the riskiest operational seams.
- Export verification should prefer tracked fixtures, explicit paths, and fail-loud resolution.
- Supported workflows belong in top-level operator docs; rescue tooling belongs in a clearly demoted filesystem surface.

### Key Lessons

- Brownfield milestones need verification artifacts and cross-phase wiring checks as diligently as code changes.
- Documentation is only done when the documented env names and runtime knobs really match the implementation.
- Supported frontend entrypaths need the same hardening guarantees as the backend helper paths they eventually call.

### Cost Observations

- Model mix: mostly mainline execution with one focused integration audit agent at closeout.
- Sessions: one closeout session after four completed phases.
- Notable: the cheapest closeout was archival, but the highest-value output was discovering two cross-phase regressions before calling the milestone clean.

## Cross-Milestone Trends

| Trend | Observation |
|-------|-------------|
| Verification discipline | Needs improvement before the next milestone to avoid archive-time gaps |
| Cross-phase drift | Supported docs and supported entrypaths need explicit final-pass integration checks |
| Windows test runtime | Remains the main operational verification friction |
