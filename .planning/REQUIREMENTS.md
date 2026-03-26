# Requirements: Social Security Spreadsheet Aggregation Tool

**Defined:** 2026-03-26
**Core Value:** Turn messy monthly regional spreadsheets into reliable dual-template outputs with clear provenance and minimal manual cleanup.

## v1 Requirements

### Security

- [x] **SEC-01**: Operators cannot deploy the application with default admin or HR passwords in non-local environments
- [x] **SEC-02**: Operators cannot deploy the application with a predictable default authentication signing secret in non-local environments

### Pipeline Hardening

- [x] **PIPE-01**: Upload size limits are enforced while file data is streamed, even when `content-length` is missing or incorrect
- [x] **PIPE-02**: Oversized or invalid uploads fail with explainable API responses and do not leave ambiguous persisted artifacts behind
- [x] **PIPE-03**: Hardening changes preserve the current import, normalization, validation, matching, and dual-template export behavior across existing regional regression samples

### Verification

- [ ] **VER-01**: Dual-template export regression tests can run from repository-controlled or explicitly configured template locations without depending on a developer desktop path
- [ ] **VER-02**: Mandatory export verification fails loudly when required fixtures or templates are missing instead of silently weakening confidence through broad skips

### Operations

- [ ] **OPS-01**: The repository documents one canonical local run path and one canonical deployment path for the supported system workflow
- [ ] **OPS-02**: Ad hoc repair or one-off deployment scripts are clearly separated from supported operator workflows
- [ ] **OPS-03**: GSD planning state exists in-repo so future work can route cleanly into discuss, plan, execute, and verify phases

## v2 Requirements

### Matching

- **MATCH-01**: Employee matching supports controlled fuzzy or alias-aware fallback beyond exact ID and exact name/company rules

### Templates and Regions

- **TPL-01**: New export templates can be onboarded without coupling logic directly to the current two-template implementation
- **REG-01**: New region-specific parser rules can be added through clearer configuration and fixture workflows

### Frontend Quality

- **FE-01**: Critical frontend workflows have automated tests around auth restoration, imports, and export/result views

## Out of Scope

| Feature | Reason |
|---------|--------|
| Rewriting the existing app into a new stack | High churn with little value compared to targeted hardening |
| LLM-first spreadsheet parsing | Conflicts with the project's explicit rules-first requirement |
| Large new product areas unrelated to payroll spreadsheet processing | Would distract from the core operational pipeline |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 1 | Complete |
| SEC-02 | Phase 1 | Complete |
| PIPE-01 | Phase 2 | Complete |
| PIPE-02 | Phase 2 | Complete |
| PIPE-03 | Phase 2 | Complete |
| VER-01 | Phase 3 | Pending |
| VER-02 | Phase 3 | Pending |
| OPS-01 | Phase 4 | Pending |
| OPS-02 | Phase 4 | Pending |
| OPS-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

---
*Requirements defined: 2026-03-26*
*Last updated: 2026-03-26 after Phase 2 execution*
