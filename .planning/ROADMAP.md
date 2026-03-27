# Roadmap

**Project:** Social Security Spreadsheet Aggregation Tool
**Current state:** v1.1 audit gap closure milestone active

## Milestones

- [x] **v1.0 Brownfield Hardening Baseline** - Phases 1-4 shipped on 2026-03-26. Archive: `.planning/milestones/v1.0-ROADMAP.md`
- [ ] **v1.1 Audit Gap Closure** - Phases 5-7 planned on 2026-03-27 from `.planning/v1.0-MILESTONE-AUDIT.md`

## Active Milestone

### v1.1 Audit Gap Closure

**Goal:** Close the v1.0 audit gaps before expanding roadmap scope or treating the brownfield hardening baseline as audit-clean.
**Source Audit:** `.planning/v1.0-MILESTONE-AUDIT.md`
**Phases:** 5-7

### Phase 5: Repair Supported Deployment Guardrails

**Goal:** Ensure the supported deployment path truly activates the non-local security guardrails implemented in Phase 1.
**Requirements:** `SEC-01`, `SEC-02`, `OPS-01`
**Gap Closure:** Closes the deployment-path integration gap and the supported deployment workflow break in the v1.0 audit.
**Depends on:** Nothing

### Phase 6: Restore Stream-Safe Quick Aggregate Entry Path

**Goal:** Make the primary quick aggregate UI entrypoint honor streamed upload enforcement instead of buffering before the authoritative limit check runs.
**Requirements:** `PIPE-01`, `PIPE-02`
**Gap Closure:** Closes the quick-aggregate integration gap and the supported upload flow break in the v1.0 audit.
**Depends on:** Phase 5

### Phase 7: Backfill Audit Evidence Chain

**Goal:** Restore a clean verification trail for the hardening milestone by backfilling missing verification artifacts and machine-checkable requirement metadata.
**Requirements:** `PIPE-03`, `VER-01`, `VER-02`
**Gap Closure:** Closes the missing verification-artifact debt for Phases 1-2 and the Phase 3 summary metadata gaps found by the v1.0 audit.
**Depends on:** Phase 6

## Deferred Optional

- Split or budget longer runtime for the timeout-prone Windows Phase 3 export reruns after the audit-clean gap closure work ships.

## Progress

| Milestone | Phases | Plans Complete | Status | Shipped |
|-----------|--------|----------------|--------|---------|
| v1.0 Brownfield Hardening Baseline | 1-4 | 6/6 | Archived with known gaps | 2026-03-26 |
| v1.1 Audit Gap Closure | 5-7 | 0/0 | Planned | - |
