# Coding Conventions

**Analysis Date:** 2026-03-25

## Naming Patterns

**Files:**
- Backend Python files use `snake_case` by responsibility and mostly end in `_service.py`, `_api.py`, `_loader.py`, `_exporter.py`, or `_filter.py`. Examples: `backend/app/services/import_service.py`, `backend/app/api/v1/imports.py`, `backend/app/parsers/workbook_loader.py`, `backend/app/validators/non_detail_row_filter.py`.
- Frontend React files use `PascalCase.tsx` for pages/components and `camelCase.ts` for hooks/services/utilities. Examples: `frontend/src/pages/Imports.tsx`, `frontend/src/components/AuthProvider.tsx`, `frontend/src/hooks/useAggregateSession.ts`, `frontend/src/services/authSession.ts`.
- Barrel files are short `index.ts` or `__init__.py` re-export modules. Examples: `frontend/src/pages/index.ts`, `frontend/src/components/index.ts`, `backend/app/services/__init__.py`, `backend/app/parsers/__init__.py`.

**Functions:**
- Backend functions use `snake_case` and stay module-level rather than class methods. Examples: `create_import_batch()` in `backend/app/services/import_service.py`, `extract_header_structure()` in `backend/app/parsers/header_extraction.py`, `validate_standardized_result()` in `backend/app/services/validation_service.py`.
- FastAPI route handlers use `*_endpoint` suffix in `backend/app/api/v1/*.py`. Examples: `create_import_batch_endpoint()`, `preview_import_batch_endpoint()` in `backend/app/api/v1/imports.py`.
- Frontend functions use `camelCase`. Event handlers are almost always `handleX`. Examples: `handleCreateBatch()` and `handleBulkDelete()` in `frontend/src/pages/Imports.tsx`, `loginWithPassword()` in `frontend/src/services/auth.ts`.

**Variables:**
- Frontend local state uses `[value, setValue]` React naming. Examples in `frontend/src/pages/Imports.tsx`: `selectedBatchId`, `setSelectedBatchId`, `pageLoading`, `setPageLoading`.
- Backend constants are uppercase module globals. Examples: `ALLOWED_EXTENSIONS` and `MAX_PARSE_WORKERS` in `backend/app/services/import_service.py`, `NON_DETAIL_TOKENS` in `backend/app/validators/non_detail_row_filter.py`, `DEFAULT_LLM_TIMEOUT` in `backend/app/services/llm_mapping_service.py`.
- Runtime settings and injected dependencies use explicit names like `settings`, `runtime_settings`, `db`, `request`, and `context`.

**Types:**
- Backend DTO-like temporary objects use `@dataclass(slots=True)` or `@dataclass(frozen=True, slots=True)`. Examples: `HeaderMappingDecision` in `backend/app/services/header_normalizer.py`, `ValidationPreviewIssue` in `backend/app/services/validation_service.py`, `RegionRegressionCase` in `backend/tests/test_region_sample_regression.py`.
- Persistence models use SQLAlchemy 2 typed `Mapped[...]` fields. Examples: `backend/app/models/import_batch.py`, `backend/app/models/source_file.py`.
- API schemas use Pydantic `BaseModel` with `*Read` / `*Input` / `*Request` suffixes. Examples: `ImportBatchDetailRead` and `DeleteImportBatchesInput` in `backend/app/schemas/imports.py`, `HeaderMappingUpdateRequest` in `backend/app/schemas/mappings.py`.
- Frontend service payloads use TypeScript `interface` declarations. Examples: `ImportBatchPreview` in `frontend/src/services/imports.ts`, `AggregateRunResult` in `frontend/src/services/aggregate.ts`.

## Code Style

**Formatting:**
- Frontend is the only area with an enforced formatter/linter toolchain. `frontend/eslint.config.js` applies ESLint 9 plus `typescript-eslint`, `react-hooks`, and `react-refresh`.
- Backend has no Black, Ruff, isort, or mypy config detected at repo root, `backend/`, or `backend/tests/`.
- Style is still consistent: explicit imports, blank-line separation by concern, single-purpose helpers, and type annotations on public functions.
- Quote style is not consistent across the repo. `frontend/src/App.tsx` prefers single quotes, while `frontend/src/services/api.ts` and `frontend/src/main.tsx` use double quotes. Match the file you edit instead of normalizing unrelated files.

**Linting:**
- Frontend lint command is `npm run lint` from `frontend/package.json`.
- `frontend/tsconfig.json` enables `strict`, `noEmit`, `isolatedModules`, and `moduleResolution: "Bundler"`.
- ESLint ignores only `dist` and `node_modules`, so new generated files inside `src/` will be linted unless excluded explicitly.
- No backend lint command is configured in `backend/requirements.txt` or root config files. Backend correctness is enforced by tests rather than a static checker.

## Import Organization

**Order:**
1. Standard library imports.
2. Third-party imports.
3. Internal `backend.app...` or relative frontend imports.
4. Type-only imports are used in TypeScript when helpful, usually adjacent to runtime imports.

**Examples:**
- `backend/app/services/import_service.py` imports `hashlib`, `inspect`, `shutil`, `ThreadPoolExecutor`, then FastAPI/SQLAlchemy, then `backend.app...` modules.
- `frontend/src/pages/Imports.tsx` imports React hooks, router utilities, local components, local API helpers, then local types.

**Path Aliases:**
- No TS path aliases are configured in `frontend/tsconfig.json`.
- Frontend uses relative imports such as `../services/imports` and `./components`.
- Backend uses absolute package imports rooted at `backend.app...`.

## Error Handling

**Patterns:**
- Backend service layers raise narrow custom exceptions such as `InvalidUploadError`, `BatchNotFoundError`, `HeaderMappingNotFoundError`, and `ExportBlockedError`. See `backend/app/services/import_service.py`, `backend/app/services/mapping_service.py`, and `backend/app/services/batch_export_service.py`.
- API layers translate service exceptions to HTTP errors close to the route boundary. Example: `backend/app/api/v1/imports.py` catches `BatchNotFoundError` and raises `HTTPException(404, ...)`.
- Application-wide error envelopes are centralized in `backend/app/api/v1/responses.py` and registered in `backend/app/main.py` through `register_exception_handlers()`. New endpoints should return `success_response()` / `error_response()` shapes instead of ad hoc JSON.
- Frontend normalizes request failures through `normalizeApiError()` in `frontend/src/services/api.ts`, then surfaces user-friendly messages in page state or the feedback context.
- Long-running frontend calls explicitly extend timeouts or use streaming. Examples: `LONG_RUNNING_REQUEST_TIMEOUT_MS` in `frontend/src/services/api.ts`, `runSimpleAggregateWithProgress()` in `frontend/src/services/aggregate.ts`.

## Logging

**Framework:** settings-driven plain/json logging, but logging calls are sparse in the current code.

**Patterns:**
- Logging configuration lives in `backend/app/core/config.py` via `log_level` and `log_format`.
- Runtime behavior is more often exposed through persisted state and progress callbacks than through direct logger usage. Example: `ImportProgressCallback` and `_notify_progress()` flow in `backend/app/services/import_service.py`.
- Frontend does not use a dedicated logger. User-visible status is held in state and rendered in components like `frontend/src/components/GlobalFeedback.tsx` and page-level notices.

## Comments

**When to Comment:**
- Comments are rare. The codebase prefers descriptive helper names and focused functions over inline explanation.
- Add comments only around non-obvious business rules or safety constraints, such as path validation, workbook heuristics, or LLM downgrade logic.

**JSDoc/TSDoc:**
- Not used as a normal convention in `frontend/src/` or `backend/app/`.

## Function Design

**Size:**
- Small utility modules stay concise and pure. Examples: `backend/app/validators/non_detail_row_filter.py`, `backend/app/services/validation_service.py`, `frontend/src/hooks/useAggregateSession.ts`.
- Large orchestration modules are acceptable when they own a workflow, but they are still broken into many private helpers. The clearest example is `backend/app/services/import_service.py`.

**Parameters:**
- Keyword-only parameters are used in backend service functions when the call site benefits from clarity. Examples: `list_header_mappings(..., batch_id=None, source_file_id=None)` in `backend/app/services/mapping_service.py`, `build_validation_issue_models(..., batch_id=..., normalized_record_ids=...)` in `backend/app/services/validation_service.py`.
- Frontend service functions take a single input object when the parameter set is likely to grow. Examples: `createImportBatch(input)` in `frontend/src/services/imports.ts`, `runSimpleAggregate(input)` in `frontend/src/services/aggregate.ts`.

**Return Values:**
- Backend parsing and validation helpers return structured dataclasses rather than tuples. Examples: `HeaderExtraction`, `HeaderNormalizationResult`, `ValidationResult`.
- API-facing backend functions return Pydantic read models. Examples: `ImportBatchPreviewRead` in `backend/app/services/import_service.py`.
- Frontend data services unwrap `ApiSuccessResponse<T>` and return only `data`. Keep that convention in new service modules.

## Module Design

**Exports:**
- Backend modules export many symbols through `backend/app/services/__init__.py` and `backend/app/parsers/__init__.py`. New shared service APIs should be added there if other modules or route files will import them through the package.
- Frontend uses barrel exports for page/component directories but not for all services. Examples: `frontend/src/pages/index.ts`, `frontend/src/components/index.ts`.

**Barrel Files:**
- Use barrel files for UI directories with many siblings.
- Do not add barrel files for every backend folder by default; follow the existing `services` and `parsers` pattern only where package-level importing is already established.

## Backend-Specific Conventions

**Service / Parser / Validator split:**
- `backend/app/parsers/` is for workbook discovery and header extraction mechanics. Keep it focused on reading spreadsheet structure. Examples: `backend/app/parsers/workbook_discovery.py`, `backend/app/parsers/header_extraction.py`.
- `backend/app/services/` is for business workflow, normalization, matching, export orchestration, and external calls. Examples: `backend/app/services/import_service.py`, `backend/app/services/llm_mapping_service.py`, `backend/app/services/matching_service.py`.
- `backend/app/validators/` is reserved for reusable row/content validation filters, not HTTP validation. Current example: `backend/app/validators/non_detail_row_filter.py`.
- `backend/app/api/v1/` should stay thin and delegate to services.

**Typing and persistence:**
- Use SQLAlchemy 2 typed models with `Mapped[...]`, `mapped_column()`, and explicit relationships. See `backend/app/models/base.py` and `backend/app/models/import_batch.py`.
- Use `ConfigDict(from_attributes=True)` in read schemas that are built from ORM instances. Example: `SourceFileRead` in `backend/app/schemas/imports.py`.
- Use enums from `backend/app/models/enums.py` instead of string literals when touching persisted status fields.

## Frontend-Specific Conventions

**Page composition:**
- Pages are stateful and domain-heavy; shared layout primitives live in `frontend/src/components/`. Examples: `PageContainer`, `SectionState`, `SurfaceNotice`.
- Route wiring is centralized in `frontend/src/App.tsx`. Add new pages there and re-export them from `frontend/src/pages/index.ts`.

**State and side effects:**
- Data fetching inside pages typically uses `useEffect()` with an `active` or `isActive` flag for race-safe cleanup. Examples: `frontend/src/pages/Imports.tsx`, `frontend/src/components/AuthProvider.tsx`.
- Expensive derived view data uses `useMemo()`. Example: `selectedSourceFile` and `previewColumns` in `frontend/src/pages/Imports.tsx`.
- Shared cross-page state uses either React context (`frontend/src/components/AuthProvider.tsx`, `frontend/src/components/ApiFeedbackProvider.tsx`) or `useSyncExternalStore()` (`frontend/src/hooks/useAggregateSession.ts`).

**API access:**
- All HTTP traffic should go through `frontend/src/services/api.ts` and a service module in `frontend/src/services/`.
- Preserve the existing typed-response pattern: `apiClient.get<ApiSuccessResponse<T>>()` then return `response.data.data`.
- Streaming endpoints may bypass Axios and use `fetch()` directly when incremental progress is required. Example: `runSimpleAggregateWithProgress()` in `frontend/src/services/aggregate.ts`.

## Practical Guidance

- Match the file’s existing quote style and import grouping; do not run broad style rewrites.
- Put spreadsheet structure inference in `backend/app/parsers/`, business normalization in `backend/app/services/`, and row exclusion rules in `backend/app/validators/`.
- Add new backend exceptions near the service that owns the failure mode, then translate them in the route module.
- Preserve the standard API envelope from `backend/app/api/v1/responses.py`.
- Keep frontend service types colocated with the service that fetches them unless they are reused broadly enough to justify promotion.
- Reuse existing sample-aware patterns and provenance-heavy DTOs instead of returning raw dictionaries from new backend logic.

---

*Convention analysis: 2026-03-25*
