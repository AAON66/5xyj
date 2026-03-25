# Architecture

**Analysis Date:** 2026-03-25

## Pattern Overview

**Overall:** Layered monolith with a React SPA frontend and a FastAPI backend. The backend keeps request handling, orchestration, parsing, persistence, validation, matching, and export concerns in separate modules under `backend/app/`, but all of them run inside one deployable application process.

**Key Characteristics:**
- Use `backend/app/api/v1/*.py` only for HTTP transport, request parsing, and HTTP error translation. Business flow lives in `backend/app/services/*.py`.
- Keep spreadsheet interpretation inside parser/normalizer modules such as `backend/app/parsers/workbook_discovery.py`, `backend/app/parsers/header_extraction.py`, `backend/app/services/header_normalizer.py`, `backend/app/services/normalization_service.py`, and `backend/app/services/housing_fund_service.py`.
- Persist every pipeline stage in database-backed models under `backend/app/models/*.py`; later stages read from persisted `ImportBatch`, `SourceFile`, `HeaderMapping`, `NormalizedRecord`, `ValidationIssue`, `MatchResult`, and `ExportJob` rows instead of relying on in-memory state.

## Layers

**Frontend Shell and Routing:**
- Purpose: Boot the SPA, restore auth state, enforce route guards, and wrap pages in a common shell.
- Location: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/components/AppShell.tsx`, `frontend/src/components/AuthProvider.tsx`
- Contains: React root render, `BrowserRouter`, auth restoration, global API feedback wiring, protected route composition, sidebar navigation.
- Depends on: `frontend/src/hooks/*.ts`, `frontend/src/services/api.ts`, `frontend/src/services/auth.ts`, `frontend/src/services/authSession.ts`
- Used by: All pages in `frontend/src/pages/*.tsx`

**Frontend Feature Pages:**
- Purpose: Present workflow-specific UI for aggregate runs, imports, mappings, employees, compare, dashboard, exports, and employee self-service.
- Location: `frontend/src/pages/*.tsx`
- Contains: Page-local state, API calls via service modules, upload forms, preview tables, download actions, route-specific UX.
- Depends on: `frontend/src/services/*.ts`, shared shell/components in `frontend/src/components/*.tsx`
- Used by: Route tree in `frontend/src/App.tsx`

**Frontend API Adapters:**
- Purpose: Centralize HTTP transport, auth header injection, timeouts, and typed response shapes.
- Location: `frontend/src/services/api.ts`, `frontend/src/services/*.ts`
- Contains: Shared Axios client, per-domain request helpers such as `frontend/src/services/imports.ts`, `frontend/src/services/aggregate.ts`, `frontend/src/services/employees.ts`, `frontend/src/services/mappings.ts`
- Depends on: `frontend/src/config/env.ts`, `frontend/src/services/authSession.ts`
- Used by: Pages and providers

**Backend Application Bootstrap:**
- Purpose: Create the FastAPI app, attach middleware, initialize runtime directories, and expose the API router.
- Location: `backend/app/main.py`, `backend/app/bootstrap.py`, `backend/run.py`
- Contains: lifespan setup, CORS, upload size guard, health endpoint, exception handlers, runtime directory creation.
- Depends on: `backend/app/core/config.py`, `backend/app/core/logging.py`, `backend/app/core/upload_guard.py`, `backend/app/api/v1/router.py`
- Used by: `uvicorn` via `backend/run.py` or `backend.app.main:app`

**Backend Transport Layer:**
- Purpose: Define versioned HTTP endpoints and convert service exceptions into HTTP responses.
- Location: `backend/app/api/v1/*.py`
- Contains: Routers for aggregate, auth, compare, dashboard, employees, imports, mappings, and system health.
- Depends on: `backend/app/dependencies.py`, `backend/app/schemas/*.py`, `backend/app/services/*.py`
- Used by: `backend/app/api/v1/router.py`

**Backend Domain Services:**
- Purpose: Orchestrate cross-step workflows and single-domain business logic.
- Location: `backend/app/services/*.py`
- Contains:
  - `backend/app/services/aggregate_service.py` for one-shot aggregate runs and progress streaming
  - `backend/app/services/import_service.py` for upload persistence and parse orchestration
  - `backend/app/services/batch_runtime_service.py` for validation and employee matching
  - `backend/app/services/batch_export_service.py` for dual-template export orchestration
  - `backend/app/services/employee_service.py`, `backend/app/services/dashboard_service.py`, `backend/app/services/compare_service.py`, `backend/app/services/mapping_service.py`
- Depends on: parsers, mappings, validators, exporters, and models
- Used by: API routers

**Parsing and Normalization Pipeline:**
- Purpose: Convert region-specific spreadsheets into canonical preview records and then database rows.
- Location: `backend/app/parsers/*.py`, `backend/app/services/header_normalizer.py`, `backend/app/services/normalization_service.py`, `backend/app/services/housing_fund_service.py`
- Contains: sheet discovery, header row extraction, alias-rule mapping, optional LLM fallback, row filtering, region-specific coercion, housing-fund-specific parsing, record merge logic.
- Depends on: `backend/app/mappings/manual_field_aliases.py`, `backend/app/services/llm_mapping_service.py`, `backend/app/validators/non_detail_row_filter.py`
- Used by: `backend/app/services/import_service.py`, `backend/app/services/batch_runtime_service.py`

**Persistence Layer:**
- Purpose: Represent batches, files, normalized rows, issues, matches, exports, and employee master state.
- Location: `backend/app/models/*.py`, `backend/app/core/database.py`
- Contains: SQLAlchemy models, enums, engine/session factory, SQLite PRAGMA configuration.
- Depends on: `backend/app/core/config.py`
- Used by: services and dependencies

## Data Flow

**Standard Batch Flow (`/api/v1/imports` family):**

1. `frontend/src/pages/Imports.tsx` uploads Excel files through `frontend/src/services/imports.ts`.
2. `backend/app/api/v1/imports.py` calls `backend/app/services/import_service.py:create_import_batch`, which stores files under `data/uploads/<batch-id>/`, creates `ImportBatch` and `SourceFile` rows, and runs filename/workbook region detection.
3. `backend/app/services/import_service.py:parse_import_batch` builds per-file analysis contexts and analyzes files in parallel with a thread pool.
4. For social security files, parsing flows through `backend/app/parsers/workbook_discovery.py` -> `backend/app/parsers/header_extraction.py` -> `backend/app/services/header_normalizer.py` -> `backend/app/services/normalization_service.py`.
5. For housing fund files, parsing flows through `backend/app/services/housing_fund_service.py`, which performs its own header detection and standardized record construction.
6. `backend/app/services/import_service.py` persists `HeaderMapping` rows and preview-derived `NormalizedRecord` rows, then marks the batch `normalized`.
7. `backend/app/services/batch_runtime_service.py:validate_batch` generates `ValidationIssue` rows and `backend/app/services/batch_runtime_service.py:match_batch` generates `MatchResult` rows plus `NormalizedRecord.employee_id` assignments.
8. `backend/app/services/batch_export_service.py:export_batch` calls `backend/app/exporters/template_exporter.py:export_dual_templates`, writes two Excel outputs under `data/outputs/<batch-id>/<job-id>/`, and persists `ExportJob` and `ExportArtifact` rows.

**One-Click Aggregate Flow (`/api/v1/aggregate`):**

1. `frontend/src/pages/SimpleAggregate.tsx` submits social security files, housing fund files, and optional employee master input with `frontend/src/services/aggregate.ts`.
2. `backend/app/api/v1/aggregate.py` calls `backend/app/services/aggregate_service.py:run_simple_aggregate`.
3. `run_simple_aggregate` composes employee import, batch creation, parse, validate, match, and export in one server-side sequence rather than making the client call each stage separately.
4. The `/api/v1/aggregate/stream` endpoint uses an NDJSON stream; `aggregate_service.py` pushes structured progress events that the page renders into stage cards and parse-worker status panels.

**Manual Mapping Correction Flow:**

1. `frontend/src/pages/Mappings.tsx` reads mappings with `frontend/src/services/mappings.ts`.
2. `backend/app/api/v1/mappings.py` calls `backend/app/services/mapping_service.py`.
3. `update_header_mapping` marks the row as `manual`, stores the canonical field override, and preserves candidate fields for traceability.
4. The next parse of that source file re-applies persisted manual overrides inside `backend/app/services/import_service.py:_apply_manual_mapping_overrides`.

**Employee Master and Self-Service Flow:**

1. HR/admin pages use `frontend/src/pages/Employees.tsx` and related service calls to manage `EmployeeMaster` records through `backend/app/api/v1/employees.py`.
2. `backend/app/services/employee_service.py` imports roster files with pandas, writes audit rows, and exposes active/historical identities for matching.
3. Public self-service requests hit `POST /api/v1/employees/self-service/query`; `employee_service.py` joins employee master data with `NormalizedRecord` and `ImportBatch` history to return employee-facing records.

**Monthly Compare Flow:**

1. `frontend/src/pages/Compare.tsx` requests batch diff data through `frontend/src/services/compare.ts`.
2. `backend/app/services/compare_service.py` loads two batches with normalized records, groups records by stable identities, computes field-level differences, and can export a comparison workbook.

## State Management

**Backend State:**
- Persistent process state is database-first. `backend/app/models/import_batch.py` and related models track stage progression with `BatchStatus`.
- Runtime filesystem state is split by purpose:
  - Uploads in `data/uploads/`
  - Templates in `data/templates/`
  - Generated outputs in `data/outputs/`
  - External reference inputs in `data/external/`
- `backend/app/core/database.py` currently defaults to SQLite at `data/app.db`, with WAL enabled for concurrent reads/writes.

**Frontend State:**
- Global auth state is provided by `frontend/src/components/AuthProvider.tsx`.
- Global API activity/error state is provided by `frontend/src/components/ApiFeedbackProvider.tsx` and `frontend/src/components/GlobalFeedback.tsx`.
- Long-running aggregate state is persisted outside component memory with `frontend/src/services/aggregateSessionStore.ts` and consumed via `frontend/src/hooks/useAggregateSession.ts`.
- Most page data is page-local React state; there is no global client-side entity cache.

## Key Abstractions

**`HeaderExtraction`:**
- Purpose: Represent the discovered workbook sheet, header rows, data start row, and flattened header columns before mapping.
- Examples: `backend/app/parsers/header_extraction.py`
- Pattern: Immutable dataclass boundary between sheet discovery and field normalization.

**`HeaderNormalizationResult` and `HeaderMappingDecision`:**
- Purpose: Represent canonical-field decisions, candidate fields, match source, and LLM status for each raw header.
- Examples: `backend/app/services/header_normalizer.py`
- Pattern: Rule-first header mapping object that can be overridden manually and persisted to `HeaderMapping`.

**`StandardizationResult` and `NormalizedPreviewRecord`:**
- Purpose: Represent cleaned record previews before they are converted into `NormalizedRecord` database rows.
- Examples: `backend/app/services/normalization_service.py`, `backend/app/services/housing_fund_service.py`
- Pattern: Intermediate normalized projection with raw values, unmapped values, and trace payloads.

**`SourceRecordBundle`:**
- Purpose: Merge social security and housing fund records into final normalized rows for a batch.
- Examples: `backend/app/services/normalization_service.py`
- Pattern: Small adapter object passed into `merge_batch_standardized_records`.

**`ImportBatch`:**
- Purpose: Root aggregate for the whole processing lifecycle of a user upload run.
- Examples: `backend/app/models/import_batch.py`
- Pattern: Parent entity with cascading relationships to source files, normalized rows, issues, matches, and exports.

**`AggregateRunRead`:**
- Purpose: Return a full end-to-end result for the quick aggregate path, including artifacts and progress-compatible summary data.
- Examples: `backend/app/schemas/aggregate.py`, produced by `backend/app/services/aggregate_service.py`
- Pattern: Composite read model spanning multiple backend domains.

## Entry Points

**Backend App Entry:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn backend.app.main:app` or `backend/run.py`
- Responsibilities: Build the FastAPI app, register middleware/handlers, include `api_router`, expose `/health`.

**Backend CLI-Like Runner:**
- Location: `backend/run.py`
- Triggers: `python backend/run.py`
- Responsibilities: Bootstrap settings and run uvicorn with the resolved log level.

**Frontend App Entry:**
- Location: `frontend/src/main.tsx`
- Triggers: Vite dev/build runtime
- Responsibilities: Mount the SPA and wrap it in router, auth, and API feedback providers.

**Frontend Route Composition:**
- Location: `frontend/src/App.tsx`
- Triggers: Browser navigation
- Responsibilities: Root redirect, public vs protected routes, role-gated workspace routes, page-to-route mapping.

**Import Workflow Entry:**
- Location: `backend/app/api/v1/imports.py`
- Triggers: `/api/v1/imports`, `/parse`, `/preview`, `/validate`, `/match`, `/export`
- Responsibilities: Drive the stepwise batch-processing workflow.

**Aggregate Workflow Entry:**
- Location: `backend/app/api/v1/aggregate.py`
- Triggers: `/api/v1/aggregate` and `/api/v1/aggregate/stream`
- Responsibilities: Execute the full pipeline in one request, with optional progress streaming.

## Error Handling

**Strategy:** Keep domain/service errors as Python exceptions, then translate them into stable API response envelopes at the router or app boundary.

**Patterns:**
- Use app-wide exception wrappers in `backend/app/main.py` for unexpected errors, FastAPI validation errors, and generic HTTP exceptions.
- Use domain-specific exceptions inside services, such as `InvalidUploadError`, `BatchNotFoundError`, `ExportBlockedError`, `EmployeeImportError`, and convert them to HTTP codes inside the corresponding router.
- Keep frontend HTTP normalization in `frontend/src/services/api.ts:normalizeApiError`, so pages deal with a single `ApiClientError` shape.

## Cross-Cutting Concerns

**Logging:** `backend/app/bootstrap.py` calls `backend/app/core/logging.py:configure_logging` during startup; the aggregate stream endpoint in `backend/app/api/v1/aggregate.py` also logs unexpected stream failures.

**Validation:** 
- Request validation uses Pydantic schemas in `backend/app/schemas/*.py`.
- Spreadsheet row validation lives in `backend/app/services/validation_service.py` and `backend/app/services/batch_runtime_service.py`.
- Non-detail row filtering lives in `backend/app/validators/non_detail_row_filter.py`.

**Authentication:**
- Backend token issue/verification lives in `backend/app/core/auth.py`.
- Route protection is enforced centrally by `backend/app/api/v1/router.py` through `backend/app/dependencies.py:require_authenticated_user`.
- Frontend auth persistence and route guards live in `frontend/src/components/AuthProvider.tsx` and `frontend/src/App.tsx`.

**Parsing Pipeline Discipline:**
- Always discover sheet/header/data-start via `backend/app/parsers/workbook_discovery.py` and `backend/app/parsers/header_extraction.py`; do not add region logic to routers or frontend code.
- Put social-security-specific alias rules in `backend/app/mappings/manual_field_aliases.py`.
- Put irreversible spreadsheet-output logic only in `backend/app/exporters/template_exporter.py`; keep export orchestration in `backend/app/services/batch_export_service.py`.

**Current Boundary Notes:**
- `backend/app/services/matching_service.py` and `backend/app/services/validation_service.py` hold pure matching/validation logic, while `backend/app/services/batch_runtime_service.py` owns batch-level persistence orchestration.
- `backend/app/matchers/` exists but is currently just a placeholder package; matching logic is implemented in `backend/app/services/matching_service.py`.

---

*Architecture analysis: 2026-03-25*
