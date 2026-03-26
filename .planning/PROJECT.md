# Social Security Spreadsheet Aggregation Tool

## What This Is

This is a brownfield React + FastAPI system for payroll and HR operations teams that process monthly social security and housing fund spreadsheets from multiple Chinese regions. It already ingests heterogeneous Excel files, detects usable sheets and headers, normalizes records into canonical fields, validates and matches employee data, and exports two mandatory downstream templates.

## Core Value

Turn messy monthly regional spreadsheets into reliable dual-template outputs with clear provenance and minimal manual cleanup.

## Requirements

### Validated

- [x] Import batches can accept both social security and housing fund source files and persist them with batch/file metadata - existing
- [x] Workbook and sheet discovery can identify usable worksheets without relying on fixed sheet names or fixed starting rows - existing
- [x] Header recognition and canonical field mapping follow a rules-first pipeline with DeepSeek fallback hooks rather than LLM-first parsing - existing
- [x] Non-detail rows such as totals, subtotals, and grouped personnel headings are filtered before normalized records are produced - existing
- [x] Normalized records preserve provenance fields and raw payload context needed for auditing and downstream troubleshooting - existing
- [x] Employee master import and record matching flows exist across backend APIs and frontend pages - existing
- [x] Dual-template export is implemented and treated as an all-or-nothing outcome for the monthly processing flow - existing
- [x] Dashboard, imports, mappings, results, compare, exports, and employee-facing routes already exist in the frontend and backend - existing

### Active

- [ ] Harden authentication so non-local environments cannot accidentally run with default credentials or predictable signing secrets
- [ ] Enforce upload-size limits during streaming, not only from request headers, so oversized files fail safely and consistently
- [ ] Make export verification self-contained and reproducible without depending on desktop-only template locations or skip-heavy test fallbacks
- [ ] Consolidate canonical run, deploy, and recovery paths so operators can distinguish supported workflows from ad hoc rescue scripts

### Out of Scope

- A greenfield rewrite of the current React + FastAPI stack - the existing system already covers the core data pipeline
- Replacing rules-first normalization with LLM-first parsing - this would conflict with the explicit project rule set
- Adding broad new regional/template coverage before core hardening is complete - stability and operational confidence come first

## Context

The repository already contains a working brownfield application with backend services under `backend/app/`, frontend flows under `frontend/src/`, region regression tests under `backend/tests/`, and codebase map documents under `.planning/codebase/`. `task.json` shows the original 32-task delivery chain marked complete, so the next useful GSD cycle is not first-build scope; it is hardening, verification, and operational cleanup around an already-functional system. The project also carries explicit business constraints from `AGENTS.md`: rules before LLM, provenance retention, non-detail row filtering, careful employee matching, and mandatory success on both export templates.

## Constraints

- **Tech stack**: Keep the existing React + TypeScript frontend and FastAPI + Python backend - replacing the stack adds churn without advancing the core payroll workflow
- **Parsing strategy**: Rules-first normalization remains mandatory, with DeepSeek only as fallback - this is an explicit project contract
- **Export contract**: Both the salary template and final tool template must succeed together - single-template success does not count as done
- **Traceability**: Standardized records must remain traceable to source file, sheet, header signature, and row - auditability is part of correctness
- **Environment dependencies**: Some current export verification still depends on local template files and sample availability - future work should reduce that coupling rather than ignore it

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat the current application as a brownfield baseline, not a fresh v1 build | The repo already contains the full import -> normalize -> validate -> match -> export chain | Good |
| Initialize GSD around hardening and maintainability rather than rebuilding completed scope | `task.json` marks the initial delivery sequence complete, so the next leverage is operational confidence | Good |
| Preserve the current stack and workflow contracts | Existing code, tests, and operator expectations are already aligned to React + FastAPI and rules-first parsing | Good |
| Delay new feature expansion until auth, upload, verification, and ops debt are tightened | The codebase map surfaced concrete concerns that are more urgent than adding surface area | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason
2. Requirements validated? Move to Validated with phase reference
3. New requirements emerged? Add to Active
4. Decisions to log? Add to Key Decisions
5. "What This Is" still accurate? Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-26 after GSD project initialization*
