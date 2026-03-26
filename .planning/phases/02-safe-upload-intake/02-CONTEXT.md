# Phase 2: Safe Upload Intake - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning
**Source:** Auto-created from roadmap, codebase map, current upload implementation, and existing regression coverage

<domain>
## Phase Boundary

This phase is only about making file intake fail safely and deterministically when uploads are oversized or malformed, while preserving the current end-to-end spreadsheet pipeline. It does not redesign parsing, matching, exports, auth, or frontend product structure. The target outcome is a hardened upload path that enforces size limits during streaming, leaves no ambiguous partially persisted artifacts behind, and proves the aggregate/import flows still work after the hardening changes.

</domain>

<decisions>
## Implementation Decisions

### Locked Decisions

- Keep the existing React + FastAPI architecture and the current batch/import APIs intact for this phase.
- Preserve the current rules-first parsing, provenance retention, employee matching, and dual-template export contracts from `AGENTS.md`.
- Enforce upload limits during file streaming, not only from `content-length` headers.
- Oversized or invalid uploads must fail with explainable API responses; they must not leave behind ambiguous saved files or partially persisted import-batch state.
- The quick aggregate path and the stepwise `/api/v1/imports` path must both remain usable after the upload hardening changes.
- Verification for this phase must include real regression coverage across existing regional samples, not only unit tests around helpers.
- `AGENTS.md` must remain unchanged during this phase.

### the agent's Discretion

- Whether the stream-time enforcement lives entirely inside `import_service._store_upload()` or is split between middleware and service logic, as long as the streamed limit cannot be bypassed when `content-length` is missing or wrong.
- Exact exception types and HTTP status details, as long as failures are deterministic and actionable.
- Whether temporary file cleanup is handled inline, via helper utilities, or via batch rollback helpers, as long as failed uploads do not leave ambiguous persisted artifacts behind.
- How much existing upload middleware should remain as a fast-path optimization versus deferring fully to service-layer enforcement.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Upload entry and request boundary
- `backend/app/core/upload_guard.py` - current header-based upload rejection; this is the gap Phase 2 must close, not duplicate blindly
- `backend/app/main.py` - app bootstrap and middleware wiring for `UploadGuardMiddleware`
- `backend/app/api/v1/imports.py` - stepwise import endpoints and current API error translation for upload flows
- `backend/app/api/v1/aggregate.py` - quick aggregate upload entry that must keep working after hardening

### Upload persistence and cleanup behavior
- `backend/app/services/import_service.py` - `create_import_batch()`, `_store_upload()`, rollback/cleanup paths, parse orchestration, and the current streamed-write gap
- `backend/app/services/aggregate_service.py` - quick aggregate orchestration that depends on `create_import_batch()` and `parse_import_batch()`
- `backend/app/core/config.py` - `max_upload_size_mb` / `max_upload_size_bytes` runtime configuration used by upload enforcement

### Existing regression coverage
- `backend/tests/test_import_batches_api.py` - current import API coverage and the best existing place to extend upload hardening tests
- `backend/tests/test_aggregate_api.py` - quick aggregate coverage that must still pass after upload changes
- `backend/tests/test_app_initialization.py` - current middleware-level payload-too-large coverage showing the present header-only behavior

### Project constraints
- `.planning/PROJECT.md` - brownfield scope and active hardening context
- `.planning/REQUIREMENTS.md` - `PIPE-01`, `PIPE-02`, `PIPE-03`
- `.planning/ROADMAP.md` - phase goal and success criteria
- `.planning/STATE.md` - current project position and sequencing
- `.planning/codebase/CONCERNS.md` - rationale for prioritizing streamed upload enforcement now
- `.planning/codebase/ARCHITECTURE.md` - request/data-flow overview for import and aggregate paths
- `AGENTS.md` - project-specific mandatory testing and scope rules

</canonical_refs>

<specifics>
## Specific Ideas

- `UploadGuardMiddleware` currently rejects oversized multipart requests only when `content-length` exists and exceeds the configured threshold.
- `import_service._store_upload()` currently writes uploaded bytes chunk by chunk and tracks `file_size`, but it never stops writing when `file_size` crosses `settings.max_upload_size_bytes`.
- `create_import_batch()` already has rollback code for saved files and persisted batch rows; the safest likely implementation path is to reuse and tighten that cleanup behavior instead of adding a second disconnected cleanup mechanism.
- `PIPE-03` means the plan must preserve successful parsing/aggregation behavior across the existing regional regression samples, especially for `/api/v1/imports` and `/api/v1/aggregate` paths.
- Current test coverage already proves header-based middleware rejection and import-batch happy paths; Phase 2 should extend these tests to cover missing/incorrect `content-length`, streamed overflow, and cleanup behavior.

</specifics>

<deferred>
## Deferred Ideas

- Template fixture reproducibility and skip-heavy export verification belong to Phase 3, not this phase.
- Canonical operator workflows and deployment-script cleanup belong to Phase 4, not this phase.
- Auth/session redesign is already handled separately in Phase 1 and should not be reopened here.
- New parser regions, matching heuristics, or frontend UX redesign are outside this phase.

</deferred>

---
*Phase: 02-safe-upload-intake*
*Context gathered: 2026-03-26 via roadmap, concerns, and upload-path analysis*