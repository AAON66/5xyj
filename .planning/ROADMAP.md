# Roadmap

**Project:** Social Security Spreadsheet Aggregation Tool
**Type:** Brownfield hardening roadmap
**Granularity:** Coarse
**Coverage:** 10/10 v1 requirements mapped

## Phases

- [x] **Phase 1: Deployment Security Guardrails** - Fail fast outside local development when auth credentials or signing secrets are unsafe.
- [x] **Phase 2: Safe Upload Intake** - Enforce upload limits during streaming and preserve current pipeline behavior under hardening changes.
- [x] **Phase 3: Reproducible Export Verification** - Make dual-template export checks repo-controlled and fail-loud instead of skip-heavy.
- [ ] **Phase 4: Supported Operations Path** - Clarify canonical run/deploy workflows, separate rescue scripts, and anchor future GSD work in-repo.

## Phase Details

### Phase 1: Deployment Security Guardrails
**Goal**: Operators can only run authenticated non-local environments with explicit, non-default secrets and passwords.
**Depends on**: Nothing
**Requirements**: SEC-01, SEC-02
**Success Criteria** (what must be TRUE):
1. A non-local deployment refuses to start when the admin password is still the default value.
2. A non-local deployment refuses to start when the HR password is still the default value.
3. A non-local deployment refuses to start when the authentication signing secret is still predictable or unchanged from the default.
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md - Enforce explicit non-local auth secret and password startup guardrails with regression tests.

Summary:
- [x] 01-01-SUMMARY.md - Startup now fails loudly for unsafe non-local auth defaults while local development remains usable.

### Phase 2: Safe Upload Intake
**Goal**: File ingestion fails safely under oversized or invalid uploads without regressing the working import-to-export pipeline.
**Depends on**: Phase 1
**Requirements**: PIPE-01, PIPE-02, PIPE-03
**Success Criteria** (what must be TRUE):
1. An oversized upload is stopped during streaming even when `content-length` is missing or incorrect.
2. An oversized or invalid upload returns an explainable API failure and does not leave ambiguous persisted artifacts behind.
3. Existing regional regression samples still complete the supported import, normalization, validation, matching, and dual-template export flow after the hardening changes.
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md - Enforce shared streamed upload limits and extend import/aggregate regression coverage without changing the existing pipeline contract.

Summary:
- [x] 02-01-SUMMARY.md - Streamed upload limits are now enforced during write-time with deterministic cleanup and consistent oversize API failures.

### Phase 3: Reproducible Export Verification
**Goal**: Dual-template export confidence is reproducible from repo-controlled or explicitly configured inputs instead of one developer workstation.
**Depends on**: Phase 2
**Requirements**: VER-01, VER-02
**Success Criteria** (what must be TRUE):
1. Export regression verification can locate both required templates from repository-controlled fixtures or an explicit configuration path.
2. Verification fails loudly when required export fixtures or templates are missing.
3. Dual-template export coverage can be rerun on another machine without editing code to point at a desktop-only template path.
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md - Establish repo-controlled export fixtures, shared export test helpers, and fail-loud explicit template resolution.
- [x] 03-02-PLAN.md - Migrate exporter, aggregate, and dashboard verification onto the shared fixture contract and remove missing placeholder dependencies.

Summary:
- [x] 03-01-SUMMARY.md - Repo-controlled regression templates and shared export fixture helpers now anchor fail-loud export API verification.
- [x] 03-02-SUMMARY.md - Exporter, aggregate, and dashboard verification now rerun on shared repo fixtures without Desktop or placeholder assumptions.

### Phase 4: Supported Operations Path
**Goal**: Operators and future agents can follow one supported local workflow and one supported deployment workflow without confusing rescue tooling for the canonical path.
**Depends on**: Phase 3
**Requirements**: OPS-01, OPS-02, OPS-03
**Success Criteria** (what must be TRUE):
1. The repository documents one canonical local run path for the supported system workflow.
2. The repository documents one canonical deployment path for the supported system workflow.
3. One-off repair and deployment scripts are clearly marked or separated so operators can distinguish them from supported workflows.
4. In-repo GSD planning state exists and points future work toward discuss, plan, execute, and verify flows.
**Plans**: 2 plans

Plans:
- [x] 04-01-PLAN.md - Define the canonical supported local and Linux/systemd deployment workflows in operator-facing docs without changing runtime behavior.
- [ ] 04-02-PLAN.md - Classify rescue and legacy operational tooling, demote server-specific notes, and add explicit `.planning/` future-agent handoff guidance.

Summary:
- [x] 04-01-SUMMARY.md - Canonical local startup and Linux/systemd deployment now have one supported operator path in repo docs.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Deployment Security Guardrails | 1/1 | Complete | 2026-03-26 |
| 2. Safe Upload Intake | 1/1 | Complete | 2026-03-26 |
| 3. Reproducible Export Verification | 2/2 | Complete | 2026-03-26 |
| 4. Supported Operations Path | 1/2 | In Progress | - |
