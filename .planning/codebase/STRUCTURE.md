# Codebase Structure

**Analysis Date:** 2026-03-25

## Directory Layout

```text
project-root/
+-- AGENTS.md                     # Agent workflow and domain rules for this repo
+-- architecture.md              # High-level intended architecture document
+-- task.json                    # GSD-style task tracker
+-- progress.txt                 # Work log used by agents
+-- backend/                     # FastAPI app, SQLAlchemy models, Excel pipeline, tests, migrations
+-- frontend/                    # React + Vite SPA
+-- data/                        # Runtime DB, uploads, outputs, templates, sample/reference files
+-- tests/                       # Top-level notes only (`README.md`), not the main automated suite
+-- .planning/codebase/          # Generated codebase reference docs for future agents
`-- .test_artifacts/             # Persisted test fixture outputs and scenario workdirs
```

## Directory Purposes

**`backend/app/`:**
- Purpose: Main backend application package.
- Contains: API routers, core config/auth/database code, SQLAlchemy models, parsers, services, validators, mappings, exporters.
- Key files: `backend/app/main.py`, `backend/app/api/v1/router.py`, `backend/app/services/import_service.py`, `backend/app/services/aggregate_service.py`

**`backend/app/api/v1/`:**
- Purpose: Versioned HTTP endpoints.
- Contains: One module per API domain.
- Key files: `backend/app/api/v1/imports.py`, `backend/app/api/v1/aggregate.py`, `backend/app/api/v1/employees.py`, `backend/app/api/v1/mappings.py`

**`backend/app/core/`:**
- Purpose: App-wide infrastructure concerns.
- Contains: settings, auth, DB engine/session wiring, logging, upload protection middleware.
- Key files: `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/auth.py`

**`backend/app/models/`:**
- Purpose: Persistent domain model definitions.
- Contains: SQLAlchemy tables and enums for batches, files, normalized rows, employee master, issues, matches, and exports.
- Key files: `backend/app/models/import_batch.py`, `backend/app/models/source_file.py`, `backend/app/models/normalized_record.py`, `backend/app/models/enums.py`

**`backend/app/parsers/`:**
- Purpose: Workbook-structure detection before normalization.
- Contains: workbook discovery, header extraction, workbook loader compatibility helpers.
- Key files: `backend/app/parsers/workbook_discovery.py`, `backend/app/parsers/header_extraction.py`, `backend/app/parsers/workbook_loader.py`

**`backend/app/services/`:**
- Purpose: Backend business logic and orchestration.
- Contains: import, aggregate, employee, mapping, validation, matching, compare, dashboard, export, region-detection, housing-fund services.
- Key files: `backend/app/services/import_service.py`, `backend/app/services/batch_runtime_service.py`, `backend/app/services/batch_export_service.py`, `backend/app/services/normalization_service.py`

**`backend/app/mappings/`:**
- Purpose: Canonical field definitions and manual alias rules.
- Contains: alias rule tables consumed by header normalization.
- Key files: `backend/app/mappings/manual_field_aliases.py`

**`backend/app/validators/`:**
- Purpose: Row-level filter helpers.
- Contains: non-detail-row detection used during normalization.
- Key files: `backend/app/validators/non_detail_row_filter.py`

**`backend/app/exporters/`:**
- Purpose: Final Excel template rewriting.
- Contains: low-level openpyxl export logic for salary and final-tool templates.
- Key files: `backend/app/exporters/template_exporter.py`

**`backend/tests/`:**
- Purpose: Actual automated backend test suite.
- Contains: service, parser, exporter, API, and regression tests.
- Key files: `backend/tests/test_import_batches_api.py`, `backend/tests/test_region_sample_regression.py`, `backend/tests/test_template_exporter_regression.py`

**`backend/alembic/`:**
- Purpose: Database migration scaffolding.
- Contains: Alembic config and version files.
- Key files: `backend/alembic.ini`, `backend/alembic/versions/*`

**`frontend/src/`:**
- Purpose: Entire SPA source tree.
- Contains: route tree, pages, shared components, hooks, config, API service wrappers, utilities, global CSS.
- Key files: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/styles.css`

**`frontend/src/pages/`:**
- Purpose: Page-level route components.
- Contains: one page per route or workspace landing surface.
- Key files: `frontend/src/pages/SimpleAggregate.tsx`, `frontend/src/pages/Imports.tsx`, `frontend/src/pages/ImportBatchDetail.tsx`, `frontend/src/pages/Mappings.tsx`

**`frontend/src/components/`:**
- Purpose: Shared layout and feedback primitives.
- Contains: auth provider, app shell, page wrapper, notices, loading/empty states.
- Key files: `frontend/src/components/AppShell.tsx`, `frontend/src/components/AuthProvider.tsx`, `frontend/src/components/ApiFeedbackProvider.tsx`

**`frontend/src/services/`:**
- Purpose: Browser-side API adapters and client persistence.
- Contains: Axios setup, domain-specific request modules, auth session storage, aggregate session persistence.
- Key files: `frontend/src/services/api.ts`, `frontend/src/services/imports.ts`, `frontend/src/services/aggregate.ts`, `frontend/src/services/aggregateSessionStore.ts`

**`frontend/src/hooks/`:**
- Purpose: Shared React context hooks.
- Contains: auth hook, API feedback hook, aggregate session hook.
- Key files: `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/useAggregateSession.ts`

**`data/`:**
- Purpose: Runtime state and local reference files.
- Contains:
  - `data/app.db` and SQLite sidecar files
  - `data/uploads/` for saved batch uploads
  - `data/outputs/` for exported workbooks
  - `data/samples/` and `data/external/` for sample/reference spreadsheets
  - `data/templates/` for export templates
- Key files: `data/app.db`

**`tests/`:**
- Purpose: Top-level documentation only.
- Contains: `tests/README.md`
- Key files: `tests/README.md`

## Key File Locations

**Entry Points:**
- `backend/run.py`: local Python entry that bootstraps settings and starts uvicorn.
- `backend/app/main.py`: FastAPI application factory and `/health` endpoint.
- `frontend/src/main.tsx`: React root render.
- `frontend/src/App.tsx`: SPA route tree and auth gating.

**Configuration:**
- `backend/app/core/config.py`: backend settings model and path resolution.
- `backend/requirements.txt`: backend Python dependencies.
- `frontend/package.json`: frontend dependencies and scripts.
- `frontend/vite.config.ts`: Vite build/dev config.
- `frontend/eslint.config.js`: frontend lint rules.
- `backend/alembic.ini`: migration config.

**Core Logic:**
- `backend/app/services/import_service.py`: upload persistence and parse orchestration.
- `backend/app/services/aggregate_service.py`: end-to-end aggregate workflow and progress streaming.
- `backend/app/services/batch_runtime_service.py`: validation and matching orchestration.
- `backend/app/services/batch_export_service.py`: dual-template export orchestration.
- `backend/app/exporters/template_exporter.py`: template cell rewrite logic.
- `backend/app/services/employee_service.py`: employee master import, CRUD, self-service lookup.

**Testing:**
- `backend/tests/test_import_batches_api.py`: import workflow API coverage.
- `backend/tests/test_aggregate_api.py`: quick aggregate API coverage.
- `backend/tests/test_region_sample_regression.py`: real sample regression coverage.
- `backend/tests/test_template_exporter_regression.py`: export regression coverage.

## Naming Conventions

**Files:**
- Backend modules use `snake_case.py`: `backend/app/services/import_service.py`
- Frontend pages/components use `PascalCase.tsx`: `frontend/src/pages/SimpleAggregate.tsx`
- Frontend service and utility modules use `camel-ish` lowercase filenames with separators only when needed: `frontend/src/services/aggregateSessionStore.ts`, `frontend/src/utils/format.ts`
- Tests follow `test_<subject>.py`: `backend/tests/test_workbook_discovery.py`

**Directories:**
- Backend layers are plural nouns grouped by responsibility: `backend/app/services/`, `backend/app/parsers/`, `backend/app/models/`
- Frontend uses responsibility-based folders under `frontend/src/`: `pages/`, `components/`, `services/`, `hooks/`, `utils/`
- Runtime data directories are purpose-driven and stateful: `data/uploads/`, `data/outputs/`, `data/templates/`, `data/samples/`

## Where to Add New Code

**New Backend API Endpoint:**
- Router: add a module or endpoint in `backend/app/api/v1/`
- Schema: define request/response models in the matching file under `backend/app/schemas/`
- Logic: put domain behavior in `backend/app/services/`
- Rule: keep routers thin; do not place workbook parsing or export logic directly in router modules.

**New Spreadsheet Parsing Rule:**
- Sheet/header discovery changes: `backend/app/parsers/workbook_discovery.py` or `backend/app/parsers/header_extraction.py`
- Header alias rules: `backend/app/mappings/manual_field_aliases.py`
- Canonical coercion or row shaping: `backend/app/services/normalization_service.py`
- Housing-fund-only parsing: `backend/app/services/housing_fund_service.py`
- Row filtering: `backend/app/validators/non_detail_row_filter.py`

**New Batch Workflow Step:**
- Orchestration between stages: `backend/app/services/aggregate_service.py` or `backend/app/services/batch_runtime_service.py`
- Persisted entities for the new stage: `backend/app/models/`
- API exposure for the step: `backend/app/api/v1/imports.py` or a new router module in `backend/app/api/v1/`

**New Export Variant:**
- Orchestration and job persistence: `backend/app/services/batch_export_service.py`
- Workbook-writing logic: `backend/app/exporters/template_exporter.py`
- Enum update: `backend/app/models/enums.py`
- Avoid adding template-specific code to routers or frontend services.

**New Frontend Page:**
- Route component: `frontend/src/pages/`
- Route registration: `frontend/src/App.tsx`
- Shared API calls: `frontend/src/services/`
- Shared layout or reusable UI: `frontend/src/components/`

**New Frontend API Client Function:**
- Add the typed request wrapper to the matching file in `frontend/src/services/`
- Keep generic Axios behavior in `frontend/src/services/api.ts`
- Keep page-specific state and request sequencing inside the page component, not inside `api.ts`

**New Database Model:**
- Add the SQLAlchemy model in `backend/app/models/`
- Export it from `backend/app/models/__init__.py`
- Add enum values to `backend/app/models/enums.py` if needed
- Add migration files in `backend/alembic/versions/`

**New Tests:**
- Backend automated tests go in `backend/tests/`
- Use the existing subject-oriented naming style, for example `backend/tests/test_<feature>.py`
- Top-level `tests/` is not the main suite location in the current repo

## Special Directories

**`data/uploads/`:**
- Purpose: Saved raw uploads grouped by batch id
- Generated: Yes
- Committed: Yes, in the current repository state

**`data/outputs/`:**
- Purpose: Generated export workbooks grouped by batch id and export job id
- Generated: Yes
- Committed: Yes, in the current repository state

**`data/templates/`:**
- Purpose: Excel template inputs used by export logic
- Generated: No
- Committed: Yes

**`data/samples/`:**
- Purpose: Curated region sample files used for manual testing and regression coverage
- Generated: No
- Committed: Yes

**`data/external/`:**
- Purpose: Extra reference inputs such as all-in social security files, housing fund examples, and roster files
- Generated: No
- Committed: Yes

**`frontend/dist/`:**
- Purpose: Built frontend assets
- Generated: Yes
- Committed: Yes, in the current repository state

**`frontend/node_modules/`:**
- Purpose: Installed frontend dependencies
- Generated: Yes
- Committed: Yes, in the current repository state

**`backend/__pycache__/` and `backend/app/**/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: Yes, in the current repository state

**`.test_artifacts/`:**
- Purpose: Persisted workdirs and outputs from backend tests and repro scenarios
- Generated: Yes
- Committed: Yes, in the current repository state

**`.planning/codebase/`:**
- Purpose: Generated reference docs consumed by later GSD commands
- Generated: Yes
- Committed: Yes, intended workflow output

## Placement Guidance

**If you need to change spreadsheet behavior, start in the backend, not the frontend.**
- Frontend files such as `frontend/src/pages/SimpleAggregate.tsx` and `frontend/src/pages/Imports.tsx` only drive upload, preview, and download UX.
- Region-specific parsing rules belong in `backend/app/parsers/`, `backend/app/services/normalization_service.py`, `backend/app/services/housing_fund_service.py`, or `backend/app/mappings/manual_field_aliases.py`.

**If you need to expose new backend data to the UI, follow the existing path:**
- Add or extend schema in `backend/app/schemas/`
- Add service logic in `backend/app/services/`
- Add router response in `backend/app/api/v1/`
- Add client wrapper in `frontend/src/services/`
- Consume it from a page in `frontend/src/pages/`

**If you need route-protected UI, keep the guard in `frontend/src/App.tsx`.**
- Do not duplicate auth checks inside every page.
- Use `frontend/src/components/AppShell.tsx` for shared authenticated layout and `frontend/src/components/AuthProvider.tsx` for auth state.

**If you need shared page UI, promote it into `frontend/src/components/`.**
- Keep page-specific tables/forms inside the page until reuse is clear.
- Promote cross-page notices, wrappers, and shells to `frontend/src/components/`.

---

*Structure analysis: 2026-03-25*
