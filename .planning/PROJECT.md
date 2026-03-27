# Social Security Spreadsheet Aggregation Tool

## What This Is

This is a brownfield React + FastAPI system for payroll and HR operations teams that process monthly social security and housing fund spreadsheets from multiple Chinese regions. It already ingests heterogeneous Excel files, detects usable sheets and headers, normalizes records into canonical fields, validates and matches employee data, and exports two mandatory downstream templates.

## Core Value

Turn messy monthly regional spreadsheets into reliable dual-template outputs with clear provenance and minimal manual cleanup.

## Current State

v1.0 is archived as a hardening baseline, and v1.1 is now planned as an audit gap closure milestone. The brownfield system still centers on the existing import -> normalize -> validate -> match -> dual-template export flow, but the next work is explicitly aimed at repairing the documented deployment contract, fixing the supported quick-aggregate stream entrypath, and backfilling the missing verification evidence chain surfaced by the v1.0 audit.

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
- [x] Non-local deployments now fail fast on default credentials or predictable auth secrets - Phase 1
- [x] Streamed upload-size enforcement now fails safely without leaving ambiguous persisted artifacts - Phase 2
- [x] Dual-template export verification now runs from repo-controlled or explicit template paths and fails loudly when fixtures are missing - Phase 3
- [x] Supported operator workflows are now explicit in `OPERATIONS.md`, while rescue tooling is demoted into `OPERATIONS_RESCUE.md` and `scripts/operations/rescue/` - Phase 4

### Active

- [x] Define the next milestone scope after reviewing the completed hardening roadmap
- [ ] Fix the supported deployment env contract so Phase 1 guardrails activate on the documented path
- [ ] Fix the supported quick-aggregate stream path so streamed upload enforcement holds on the primary UI entrypoint
- [ ] Backfill formal verification artifacts for Phase 1 and Phase 2, plus machine-checkable summary metadata for Phase 3
- [ ] Reduce or split the Windows timeout-prone export regression reruns

### Out of Scope

- A greenfield rewrite of the current React + FastAPI stack - the existing system already covers the core data pipeline
- Replacing rules-first normalization with LLM-first parsing - this would conflict with the explicit project rule set
- Adding broad new regional/template coverage before core hardening is complete - stability and operational confidence come first

## Context

The repository contains a working brownfield application with backend services under `backend/app/`, frontend flows under `frontend/src/`, region regression tests under `backend/tests/`, and codebase map documents under `.planning/codebase/`. `task.json` shows the original 32-task delivery chain marked complete, and v1.0 hardening work is now archived under `.planning/milestones/`. The project still carries explicit business constraints from `AGENTS.md`: rules before LLM, provenance retention, non-detail row filtering, careful employee matching, and mandatory success on both export templates. Operator-facing runbook clarity now centers on `OPERATIONS.md` for supported workflows and `OPERATIONS_RESCUE.md` for demoted rescue or legacy helpers. The main unresolved closeout issues are now explicit: the supported deployment docs drifted from the Phase 1 settings contract, the supported quick-aggregate stream path drifts from the intended Phase 2 enforcement guarantee, and the milestone evidence chain is incomplete for Phase 1 and Phase 2.

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
| Document one supported local path and one supported deployment path, while relocating rescue helpers out of the repo root | Operators and future agents needed an obvious supported lane that matched existing brownfield behavior | Good |
| Archive v1.0 with known audit gaps instead of reopening hardening work during closeout | The issues are real but now clearly bounded and can be planned explicitly into the next milestone | Revisit |
| Start the next milestone as a narrow audit gap closure effort before any new feature expansion | The v1.0 audit isolated three focused workstreams that unblock a clean re-audit without reopening completed brownfield scope | Good |

## Next Milestone Goals

- Repair the documented deployment path so it truly activates the Phase 1 production guardrails.
- Repair the supported quick aggregate entrypath so upload-size enforcement is authoritative while client data streams.
- Tighten verification discipline so future milestones do not close with missing phase verification artifacts.

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
*Last updated: 2026-03-27 after v1.1 gap-closure milestone planning*
