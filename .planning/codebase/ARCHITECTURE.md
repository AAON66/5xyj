# Architecture

**Analysis Date:** 2026-03-27

## Pattern Overview

**Overall:** Monolithic two-tier application (React SPA + FastAPI backend) with a pipeline-oriented data processing core.

**Key Characteristics:**
- Frontend is a React SPA communicating via REST/NDJSON streaming to a FastAPI backend
- Backend follows a layered service architecture: API routes -> services -> parsers/validators/exporters -> models
- Data processing is a sequential pipeline: Upload -> Parse -> Normalize -> Validate -> Match -> Export
- SQLite database with SQLAlchemy ORM (WAL mode enabled)
- Batch-oriented processing: all operations are scoped to an `ImportBatch`

## Layers

**API Layer (Routes):**
- Purpose: HTTP request handling, input validation, response formatting
- Location: `backend/app/api/v1/`
- Contains: FastAPI routers for each domain (aggregate, imports, employees, dashboard, compare, mappings, auth, system)
- Depends on: Services, Schemas, Dependencies
- Used by: Frontend via HTTP

**Service Layer:**
- Purpose: Business logic orchestration, pipeline coordination
- Location: `backend/app/services/`
- Contains: Aggregate orchestrator, import service, normalization, validation, matching, export, dashboard, compare, employee management
- Depends on: Models, Parsers, Validators, Exporters, Mappings
- Used by: API layer

**Parser Layer:**
- Purpose: Excel workbook discovery, header extraction, structure analysis
- Location: `backend/app/parsers/`
- Contains: Workbook discovery (`workbook_discovery.py`), header extraction (`header_extraction.py`), workbook loading (`workbook_loader.py`)
- Depends on: openpyxl
- Used by: Import service, normalization service

**Mapping Layer:**
- Purpose: Raw header-to-canonical-field resolution (rule-based + LLM fallback)
- Location: `backend/app/mappings/` and `backend/app/services/header_normalizer.py`
- Contains: Manual alias rules (`manual_field_aliases.py`), header normalizer, LLM mapping service
- Depends on: DeepSeek API (optional), manual alias rules
- Used by: Import service, normalization service

**Validator Layer:**
- Purpose: Row filtering (non-detail rows) and data quality checks
- Location: `backend/app/validators/`
- Contains: Non-detail row filter (`non_detail_row_filter.py`)
- Depends on: None (pure logic)
- Used by: Normalization service

**Exporter Layer:**
- Purpose: Dual-template Excel output generation
- Location: `backend/app/exporters/`
- Contains: Template exporter (`template_exporter.py`) that fills two fixed Excel templates
- Depends on: openpyxl, NormalizedRecord models, template files
- Used by: Batch export service

**Model Layer:**
- Purpose: Database schema definition and ORM mappings
- Location: `backend/app/models/`
- Contains: 10 SQLAlchemy models representing the full data lifecycle
- Depends on: SQLAlchemy
- Used by: All backend layers

**Schema Layer:**
- Purpose: Pydantic request/response schemas for API serialization
- Location: `backend/app/schemas/`
- Contains: Per-domain schema modules (aggregate, imports, dashboard, employees, compare, mappings, auth)
- Depends on: Pydantic
- Used by: API layer, service layer

**Frontend Layer:**
- Purpose: User interface for upload, monitoring, and download
- Location: `frontend/src/`
- Contains: Pages, components, services (API clients), hooks, utils
- Depends on: React, React Router, Axios
- Used by: End users via browser

## Data Flow

**Primary Pipeline (Simple Aggregate):**

1. User uploads social security + optional housing fund + optional employee master files via `POST /api/v1/aggregate/stream`
2. `aggregate_service.run_simple_aggregate()` orchestrates the full pipeline with progress callbacks
3. `import_service.create_import_batch()` saves files to disk, creates `ImportBatch` + `SourceFile` DB records, detects regions
4. `import_service.parse_import_batch()` runs in parallel (up to 5 workers via `ThreadPoolExecutor`):
   - `workbook_discovery.discover_workbook()` finds the valid sheet and data region
   - `header_extraction.extract_header_structure()` identifies multi-row headers
   - `header_normalizer.normalize_header_extraction()` maps raw headers to canonical fields (rules first, LLM fallback)
   - `normalization_service.standardize_workbook()` converts rows to `NormalizedRecord` models
   - `non_detail_row_filter.classify_row()` filters summary/group rows
5. `validation_service.validate_standardized_result()` checks required fields, ID formats, amount consistency, duplicates
6. `matching_service.match_preview_records()` matches records to `EmployeeMaster` by ID number, name, or social security number
7. `batch_export_service.export_batch()` calls `export_dual_templates()` to generate both output Excel files
8. NDJSON progress events stream back to frontend throughout

**State Management:**
- Backend: SQLAlchemy session per request via `get_db_session()` dependency injection. Batch status progresses through `BatchStatus` enum: UPLOADED -> PARSING -> NORMALIZED -> VALIDATED -> MATCHED -> EXPORTED
- Frontend: `useSyncExternalStore`-based aggregate session store (`aggregateSessionStore.ts`) persists across page navigations. Auth state via React context (`AuthProvider`). API feedback via context (`ApiFeedbackProvider`).

## Key Abstractions

**ImportBatch:**
- Purpose: Root entity grouping a single aggregation run
- Examples: `backend/app/models/import_batch.py`
- Pattern: Parent of SourceFile, NormalizedRecord, ValidationIssue, MatchResult, ExportJob via cascading relationships

**NormalizedRecord:**
- Purpose: A single employee record normalized to canonical fields from any region's format
- Examples: `backend/app/models/normalized_record.py`
- Pattern: Wide table with ~30 canonical fields (identity, amounts, metadata) plus `raw_payload` JSON for provenance

**HeaderMappingDecision:**
- Purpose: Traceable decision record for each raw header -> canonical field mapping
- Examples: `backend/app/services/header_normalizer.py`
- Pattern: Dataclass capturing raw header, canonical field, mapping source (rule/LLM/manual), confidence, candidates

**NormalizedPreviewRecord:**
- Purpose: In-memory record representation used during processing before DB persistence
- Examples: `backend/app/services/normalization_service.py`
- Pattern: Lightweight dataclass with `values`, `unmapped_values`, `raw_values` dicts

**RowFilterDecision:**
- Purpose: Decision record for whether a row is a detail record or summary/group row
- Examples: `backend/app/validators/non_detail_row_filter.py`
- Pattern: Dataclass with keep/reject flag and reason

## Entry Points

**Backend Application:**
- Location: `backend/app/main.py` -> `create_app()` -> `app`
- Triggers: `uvicorn backend.app.main:app --reload`
- Responsibilities: FastAPI app factory, middleware registration (CORS, upload guard), exception handlers, router mounting

**Backend Bootstrap:**
- Location: `backend/app/bootstrap.py` -> `bootstrap_application()`
- Triggers: App lifespan startup
- Responsibilities: Auth guardrail validation, logging configuration, runtime directory creation

**Frontend Application:**
- Location: `frontend/src/main.tsx` -> renders `<App />`
- Triggers: Browser loads `index.html`
- Responsibilities: React root mount with BrowserRouter, AuthProvider, ApiFeedbackProvider

**Database Migrations:**
- Location: `backend/alembic/`
- Triggers: `alembic upgrade head`
- Responsibilities: Schema versioning (4 migrations: initial, file size, audit, housing fund)

## API Design

**Response Envelope:**
All responses use a consistent envelope defined in `backend/app/api/v1/responses.py`:
- Success: `{ "success": true, "message": "...", "data": {...} }`
- Error: `{ "success": false, "error": { "code": "...", "message": "...", "details": ... } }`

**Streaming Endpoint:**
`POST /api/v1/aggregate/stream` returns `application/x-ndjson` with progress events (`{ "event": "progress", "stage": "...", "percent": N }`) and a final result event (`{ "event": "result", "data": {...} }`).

**Authentication:**
- JWT Bearer tokens via `backend/app/core/auth.py`
- Two roles: `admin` and `hr`
- Protected routes require `require_authenticated_user` dependency
- Auth can be disabled via `auth_enabled=False` setting

**Route Prefixes:**
- All API routes under `/api/v1/` (configurable via `Settings.api_v1_prefix`)
- `/api/v1/aggregate` - one-shot and streaming aggregate
- `/api/v1/imports` - batch CRUD, parse, validate, match, export
- `/api/v1/employees` - employee master CRUD and self-service
- `/api/v1/dashboard` - overview stats
- `/api/v1/compare` - cross-batch comparison
- `/api/v1/mappings` - header mapping review
- `/api/v1/auth` - login
- `/api/v1/system` - health and runtime info

## Error Handling

**Strategy:** Typed exceptions at service layer, caught and mapped to HTTP errors at API layer.

**Patterns:**
- Custom exception classes: `InvalidUploadError`, `UploadTooLargeError`, `BatchNotFoundError`, `SourceFileNotFoundError`, `ExportBlockedError`, `EmployeeImportError`
- Global exception handlers in `main.py` for `HTTPException`, `RequestValidationError`, and unhandled `Exception`
- Frontend: `ApiClientError` class wraps Axios errors with `statusCode`, `code`, `details` fields; global interceptor clears auth on 401

## Cross-Cutting Concerns

**Logging:** Structured JSON logging configured via `backend/app/core/logging.py`, level controlled by `Settings.log_level`

**Validation:** Two levels:
1. Request validation via Pydantic schemas (automatic 422 responses)
2. Business validation via `validation_service.py` (required fields, ID format, amount consistency, duplicates)

**Authentication:** JWT-based with role-based route guards. Bootstrap validates auth config is not using defaults in non-local environments (`backend/app/bootstrap.py`).

**Upload Safety:** `UploadGuardMiddleware` in `backend/app/core/upload_guard.py` enforces max upload size at middleware level before request body is fully read.

**Configuration:** Centralized in `backend/app/core/config.py` via pydantic-settings `BaseSettings` class, reading from `.env` file and environment variables.

---

*Architecture analysis: 2026-03-27*
