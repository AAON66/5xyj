# Codebase Structure

**Analysis Date:** 2026-03-27

## Directory Layout

```
D:/execl_mix/
├── backend/                    # FastAPI backend (Python)
│   ├── alembic/                # Database migrations
│   │   ├── env.py
│   │   └── versions/           # Migration scripts (4 total)
│   ├── app/                    # Application package
│   │   ├── api/v1/             # API route handlers
│   │   ├── core/               # Framework config, DB, auth, logging
│   │   ├── exporters/          # Excel template output generation
│   │   ├── mappings/           # Manual field alias rules
│   │   ├── matchers/           # (empty package placeholder)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── parsers/            # Excel workbook parsing
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic and pipeline orchestration
│   │   └── validators/         # Row filtering and data quality
│   ├── tests/                  # Backend-specific test helpers
│   ├── run.py                  # Alternate entry point for uvicorn
│   └── requirements.server.txt # Production dependencies
├── frontend/                   # React SPA (TypeScript)
│   ├── src/
│   │   ├── components/         # Shared UI components
│   │   ├── config/             # Environment configuration
│   │   ├── hooks/              # React hooks (auth, aggregate session, feedback)
│   │   ├── pages/              # Route-level page components
│   │   ├── services/           # API client modules
│   │   └── utils/              # Formatting helpers
│   ├── dist/                   # Built output (generated)
│   ├── index.html              # SPA entry HTML
│   ├── vite.config.ts          # Vite build config
│   ├── tsconfig.json           # TypeScript config
│   └── package.json            # Node dependencies
├── data/                       # Runtime data (gitignored content)
│   ├── app.db                  # SQLite database
│   ├── uploads/                # Uploaded Excel files (per batch UUID)
│   ├── outputs/                # Generated export files (per batch/job UUID)
│   ├── samples/                # Sample input files
│   ├── templates/              # Excel template files for export
│   └── external/               # External reference data
├── tests/                      # Root-level test directory (currently empty of .py files)
├── scripts/
│   └── operations/             # Operational scripts
├── .claude/                    # Claude Code project config
├── .planning/                  # GSD planning documents
├── CLAUDE.md                   # Project instructions for Claude
├── task.json                   # Task tracking
├── progress.txt                # Agent progress log
└── architecture.md             # Legacy architecture doc
```

## Directory Purposes

**`backend/app/api/v1/`:**
- Purpose: HTTP endpoint definitions
- Contains: 8 router modules, shared response helpers
- Key files:
  - `router.py`: Central router that mounts all sub-routers with auth dependencies
  - `aggregate.py`: One-shot and streaming aggregate endpoints
  - `imports.py`: Full batch lifecycle CRUD (create, parse, validate, match, export, download, delete)
  - `employees.py`: Employee master CRUD and self-service query
  - `dashboard.py`: Overview statistics
  - `compare.py`: Cross-batch comparison and diff export
  - `mappings.py`: Header mapping audit
  - `auth.py`: Login endpoint
  - `system.py`: Health check and runtime info
  - `responses.py`: `success_response()` and `error_response()` envelope helpers

**`backend/app/core/`:**
- Purpose: Framework-level infrastructure
- Contains: Configuration, database engine, auth, logging, upload guard
- Key files:
  - `config.py`: `Settings` class (pydantic-settings), all env vars, path resolution
  - `database.py`: SQLAlchemy engine/session factory, SQLite WAL pragmas
  - `auth.py`: JWT token creation/verification, `AuthUser` model
  - `logging.py`: Structured logging setup (plain or JSON format)
  - `upload_guard.py`: ASGI middleware enforcing max upload size

**`backend/app/services/`:**
- Purpose: All business logic lives here
- Contains: 12 service modules covering the entire pipeline
- Key files:
  - `aggregate_service.py`: Top-level orchestrator for the full pipeline with progress streaming
  - `import_service.py`: Batch creation, file saving, parallel parsing, region detection
  - `normalization_service.py`: Workbook standardization, row-to-canonical-field mapping, Changsha/Wuhan special handling
  - `header_normalizer.py`: Rule-based header mapping with LLM fallback decision logic
  - `llm_mapping_service.py`: DeepSeek API integration for header disambiguation
  - `region_detection_service.py`: Region identification from filename keywords and workbook content patterns
  - `matching_service.py`: Employee ID matching by ID number, name, SSN
  - `validation_service.py`: Required field checks, ID format validation, amount consistency, duplicate detection
  - `batch_export_service.py`: Export orchestration, output directory management
  - `batch_runtime_service.py`: Step-by-step batch pipeline (validate -> match)
  - `employee_service.py`: Employee master import/CRUD
  - `dashboard_service.py`: Aggregate statistics queries
  - `compare_service.py`: Cross-batch record comparison
  - `housing_fund_service.py`: Housing fund workbook analysis
  - `mapping_service.py`: Mapping review/update operations

**`backend/app/parsers/`:**
- Purpose: Excel file structure analysis
- Contains: 3 parser modules
- Key files:
  - `workbook_discovery.py`: Finds valid worksheets, determines data start row, detects multi-row headers
  - `header_extraction.py`: Builds header tree from multi-row headers, flattens to column list with signatures
  - `workbook_loader.py`: openpyxl workbook loading with compatibility handling

**`backend/app/mappings/`:**
- Purpose: Static field alias configuration
- Contains: Manual alias rules
- Key files:
  - `manual_field_aliases.py`: `MANUAL_ALIAS_RULES` list of `AliasRule` objects mapping raw Chinese header patterns to canonical field names

**`backend/app/validators/`:**
- Purpose: Data quality filtering
- Contains: Non-detail row classifier
- Key files:
  - `non_detail_row_filter.py`: `classify_row()` function detecting summary rows (合计, 小计), group headers (在职人员, 退休人员), placeholder rows, and header echo rows

**`backend/app/exporters/`:**
- Purpose: Output Excel generation
- Contains: Template-based exporter
- Key files:
  - `template_exporter.py`: `export_dual_templates()` fills salary template and final tool template from NormalizedRecord data

**`backend/app/models/`:**
- Purpose: Database schema
- Contains: 10 ORM models + base mixins + enums
- Key files:
  - `base.py`: `Base` declarative base, `UUIDPrimaryKeyMixin`, `TimestampMixin`, `CreatedAtMixin`
  - `import_batch.py`: `ImportBatch` - root entity with status lifecycle
  - `source_file.py`: `SourceFile` - uploaded file metadata, region, company
  - `normalized_record.py`: `NormalizedRecord` - ~30 canonical fields + raw_payload JSON
  - `header_mapping.py`: `HeaderMapping` - persisted mapping decisions
  - `validation_issue.py`: `ValidationIssue` - data quality findings
  - `match_result.py`: `MatchResult` - employee matching outcome
  - `employee_master.py`: `EmployeeMaster` - reference employee data
  - `employee_master_audit.py`: `EmployeeMasterAudit` - change tracking
  - `export_job.py`: `ExportJob` - export execution record
  - `export_artifact.py`: `ExportArtifact` - generated file reference
  - `enums.py`: `BatchStatus`, `MappingSource`, `MatchStatus`, `TemplateType`, `SourceFileKind`, `EmployeeAuditAction`

**`backend/app/schemas/`:**
- Purpose: API serialization contracts
- Contains: Per-domain Pydantic models
- Key files:
  - `aggregate.py`: `AggregateRunRead`, `AggregateSourceFileRead`, `AggregateEmployeeImportRead`
  - `imports.py`: Batch detail, preview, validation, match, export read schemas
  - `dashboard.py`: `DashboardOverviewRead`, totals, recent batches
  - `employees.py`: Employee CRUD schemas
  - `compare.py`: Cross-batch comparison schemas
  - `mappings.py`: Mapping review schemas
  - `auth.py`: Login request/response

**`frontend/src/pages/`:**
- Purpose: Route-level views
- Contains: 13 page components
- Key files:
  - `SimpleAggregate.tsx`: Primary user workflow - file upload, progress monitoring, download
  - `Workspace.tsx`: Role-based workspace (admin vs hr views, exported as `AdminWorkspacePage` and `HrWorkspacePage`)
  - `Dashboard.tsx`: System overview stats
  - `Imports.tsx`: Batch list view
  - `ImportBatchDetail.tsx`: Single batch detail with parse/validate/match/export steps
  - `Employees.tsx`: Employee master management
  - `EmployeeCreate.tsx`: Add new employee
  - `EmployeeSelfService.tsx`: Public employee query (no auth required)
  - `Results.tsx`: Export results view
  - `Exports.tsx`: Export history
  - `Mappings.tsx`: Header mapping review
  - `Compare.tsx`: Cross-batch comparison
  - `Login.tsx`: Authentication
  - `Portal.tsx`: (referenced but likely merged into workspace)
  - `NotFound.tsx`: 404 page

**`frontend/src/services/`:**
- Purpose: Backend API client modules
- Contains: 10 service modules
- Key files:
  - `api.ts`: Axios client setup, error normalization, auth interceptors, response types
  - `aggregate.ts`: Aggregate API calls, NDJSON stream parsing, artifact download
  - `aggregateSessionStore.ts`: External store for aggregate session state (persists across navigation)
  - `auth.ts`: Login API call
  - `authSession.ts`: localStorage-based auth token persistence
  - `imports.ts`: Batch CRUD, parse, validate, match, export API calls
  - `employees.ts`: Employee master API calls
  - `dashboard.ts`: Dashboard stats API call
  - `compare.ts`: Comparison API calls
  - `mappings.ts`: Mapping review API calls
  - `system.ts`: Health check API call
  - `runtime.ts`: Runtime info API call

**`frontend/src/components/`:**
- Purpose: Shared UI building blocks
- Contains: 7 component files
- Key files:
  - `AppShell.tsx`: Main layout with navigation sidebar
  - `AuthProvider.tsx`: React context provider for auth state
  - `ApiFeedbackProvider.tsx`: Global API feedback/toast system
  - `GlobalFeedback.tsx`: Toast notification renderer
  - `PageContainer.tsx`: Page layout wrapper
  - `SectionState.tsx`: Loading/empty/error state display
  - `SurfaceNotice.tsx`: Inline notice component
  - `index.ts`: Barrel export

**`frontend/src/hooks/`:**
- Purpose: Custom React hooks
- Contains: 5 hook files
- Key files:
  - `useAggregateSession.ts`: Subscribes to aggregate session external store
  - `useAuth.ts`: Auth context consumer hook
  - `useApiFeedback.ts`: API feedback context consumer hook
  - `authContext.ts`: Auth context definition
  - `apiFeedbackContext.ts`: Feedback context definition
  - `index.ts`: Barrel export

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app creation and startup
- `backend/run.py`: Alternate uvicorn runner
- `frontend/src/main.tsx`: React app mount
- `frontend/index.html`: SPA HTML shell

**Configuration:**
- `backend/app/core/config.py`: All backend settings (reads `.env`)
- `frontend/src/config/env.ts`: API base URL from Vite env
- `frontend/vite.config.ts`: Vite build configuration
- `frontend/tsconfig.json`: TypeScript compiler options
- `frontend/eslint.config.js`: ESLint configuration
- `backend/alembic/env.py`: Alembic migration config

**Core Logic (Pipeline):**
- `backend/app/services/aggregate_service.py`: Full pipeline orchestrator
- `backend/app/services/import_service.py`: File intake and parallel parsing
- `backend/app/services/normalization_service.py`: Row standardization
- `backend/app/services/header_normalizer.py`: Header-to-field mapping
- `backend/app/mappings/manual_field_aliases.py`: Alias rule definitions
- `backend/app/validators/non_detail_row_filter.py`: Summary row filtering
- `backend/app/services/matching_service.py`: Employee ID matching
- `backend/app/exporters/template_exporter.py`: Dual template export

**Database:**
- `data/app.db`: SQLite database file
- `backend/app/core/database.py`: Engine and session factory
- `backend/app/models/`: All ORM model definitions
- `backend/alembic/versions/`: Migration scripts

**Startup Scripts:**
- `start_project_local.cmd` / `start_project_local.ps1`: Launch both frontend and backend
- `start_backend_local.cmd` / `start_backend_local.ps1`: Launch backend only
- `start_frontend_local.cmd` / `start_frontend_local.ps1`: Launch frontend only

## Naming Conventions

**Files:**
- Backend Python: `snake_case.py` (e.g., `import_service.py`, `normalized_record.py`)
- Frontend TypeScript: `PascalCase.tsx` for pages/components (e.g., `SimpleAggregate.tsx`), `camelCase.ts` for services/hooks (e.g., `aggregateSessionStore.ts`)
- Config files: Standard tool conventions (`vite.config.ts`, `tsconfig.json`)

**Directories:**
- Backend: `snake_case` plural nouns (e.g., `services/`, `models/`, `parsers/`, `exporters/`)
- Frontend: `camelCase` or lowercase (e.g., `components/`, `pages/`, `services/`, `hooks/`)

**Models:**
- SQLAlchemy: `PascalCase` class names, `snake_case` table names with plural (e.g., `ImportBatch` -> `import_batches`)
- Pydantic schemas: `PascalCase` with `Read`/`Input`/`Request` suffix (e.g., `ImportBatchDetailRead`, `CompareExportRequest`)

## Where to Add New Code

**New API Endpoint:**
- Route handler: `backend/app/api/v1/{domain}.py` (new file or add to existing router)
- Register in: `backend/app/api/v1/router.py`
- Request/response schemas: `backend/app/schemas/{domain}.py`
- Business logic: `backend/app/services/{domain}_service.py`

**New Region Parser:**
- Region keywords: `backend/app/services/region_detection_service.py` -> `REGION_KEYWORDS` and `REGION_CONTENT_PATTERNS` dicts
- Header aliases: `backend/app/mappings/manual_field_aliases.py` -> add `AliasRule` entries
- Special normalization logic: `backend/app/services/normalization_service.py` (see Changsha/Wuhan patterns)
- Region label: Add to `REGION_LABELS` dict in `backend/app/services/region_detection_service.py`

**New Canonical Field:**
- Model column: `backend/app/models/normalized_record.py`
- Amount field set: `backend/app/services/normalization_service.py` -> `AMOUNT_FIELDS`
- Export mapping: `backend/app/exporters/template_exporter.py` -> `EXPORT_AMOUNT_FIELDS`
- Migration: New file in `backend/alembic/versions/`

**New Frontend Page:**
- Page component: `frontend/src/pages/{PageName}.tsx`
- Export from: `frontend/src/pages/index.ts`
- Route: `frontend/src/App.tsx`
- API service (if needed): `frontend/src/services/{domain}.ts`

**New Shared Component:**
- Component: `frontend/src/components/{ComponentName}.tsx`
- Export from: `frontend/src/components/index.ts`

**New Database Model:**
- Model: `backend/app/models/{model_name}.py`
- Register in: `backend/app/models/__init__.py`
- Migration: `backend/alembic/versions/{date}_{sequence}_{description}.py`

**Utilities:**
- Backend shared helpers: Add to relevant service or create new module in `backend/app/services/`
- Frontend shared helpers: `frontend/src/utils/`

## Special Directories

**`data/`:**
- Purpose: All runtime data - database, uploads, outputs, templates, samples
- Generated: Yes (created by `bootstrap.py` on startup)
- Committed: Only directory structure; actual data files are gitignored

**`backend/alembic/versions/`:**
- Purpose: Database migration scripts
- Generated: Via `alembic revision`
- Committed: Yes

**`frontend/dist/`:**
- Purpose: Vite production build output
- Generated: Yes (`npm run build`)
- Committed: Yes (for deployment convenience)

**`.test_artifacts/`:**
- Purpose: Test output files created during integration tests
- Generated: Yes
- Committed: No

**`backend/tests/support/`:**
- Purpose: Test fixtures and helpers
- Contains: `export_fixtures.py`
- Committed: Yes

---

*Structure analysis: 2026-03-27*
