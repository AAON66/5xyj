# Roadmap

**Project:** Social Security Spreadsheet Aggregation Tool
**Type:** Brownfield hardening roadmap
**Granularity:** Coarse
**Coverage:** 10/10 v1 requirements mapped

## Phases

- [ ] **Phase 1: Deployment Security Guardrails** - Fail fast outside local development when auth credentials or signing secrets are unsafe.
- [ ] **Phase 2: Safe Upload Intake** - Enforce upload limits during streaming and preserve current pipeline behavior under hardening changes.
- [ ] **Phase 3: Reproducible Export Verification** - Make dual-template export checks repo-controlled and fail-loud instead of skip-heavy.
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
**Plans**: TBD

### Phase 2: Safe Upload Intake
**Goal**: File ingestion fails safely under oversized or invalid uploads without regressing the working import-to-export pipeline.
**Depends on**: Phase 1
**Requirements**: PIPE-01, PIPE-02, PIPE-03
**Success Criteria** (what must be TRUE):
1. An oversized upload is stopped during streaming even when `content-length` is missing or incorrect.
2. An oversized or invalid upload returns an explainable API failure and does not leave ambiguous persisted artifacts behind.
3. Existing regional regression samples still complete the supported import, normalization, validation, matching, and dual-template export flow after the hardening changes.
**Plans**: TBD

### Phase 3: Reproducible Export Verification
**Goal**: Dual-template export confidence is reproducible from repo-controlled or explicitly configured inputs instead of one developer workstation.
**Depends on**: Phase 2
**Requirements**: VER-01, VER-02
**Success Criteria** (what must be TRUE):
1. Export regression verification can locate both required templates from repository-controlled fixtures or an explicit configuration path.
2. Verification fails loudly when required export fixtures or templates are missing.
3. Dual-template export coverage can be rerun on another machine without editing code to point at a desktop-only template path.
**Plans**: TBD

### Phase 4: Supported Operations Path
**Goal**: Operators and future agents can follow one supported local workflow and one supported deployment workflow without confusing rescue tooling for the canonical path.
**Depends on**: Phase 3
**Requirements**: OPS-01, OPS-02, OPS-03
**Success Criteria** (what must be TRUE):
1. The repository documents one canonical local run path for the supported system workflow.
2. The repository documents one canonical deployment path for the supported system workflow.
3. One-off repair and deployment scripts are clearly marked or separated so operators can distinguish them from supported workflows.
4. In-repo GSD planning state exists and points future work toward discuss, plan, execute, and verify flows.
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Deployment Security Guardrails | 0/0 | Not started | - |
| 2. Safe Upload Intake | 0/0 | Not started | - |
| 3. Reproducible Export Verification | 0/0 | Not started | - |
| 4. Supported Operations Path | 0/0 | Not started | - |

