# Codebase Concerns

**Analysis Date:** 2026-03-27

## Tech Debt

### CRITICAL: Missing `xlrd` in requirements.txt

- Issue: `backend/app/parsers/workbook_loader.py` imports and uses `xlrd` for `.xls` file support, but `xlrd` is not listed in `backend/requirements.txt`. Deployment to a fresh environment will crash on any `.xls` upload.
- Files: `backend/app/parsers/workbook_loader.py`, `backend/requirements.txt`
- Impact: Any `.xls` file upload fails with `ModuleNotFoundError` in production.
- Fix approach: Add `xlrd>=2.0.0` to `backend/requirements.txt`.

### CRITICAL: Divergent `requirements.server.txt` with conflicting auth libraries

- Issue: `backend/requirements.server.txt` lists `python-jose[cryptography]` and `passlib[bcrypt]` which are not used anywhere in the codebase. The actual auth implementation in `backend/app/core/auth.py` uses a custom HMAC-SHA256 token scheme with `hashlib`/`hmac`. These phantom dependencies suggest an abandoned migration or copy-paste from a template.
- Files: `backend/requirements.server.txt`, `backend/app/core/auth.py`
- Impact: Confusion during deployment; installing unused cryptographic libraries increases attack surface.
- Fix approach: Remove `python-jose` and `passlib` from `requirements.server.txt`, or consolidate into a single requirements file.

### HIGH: Duplicated `REGION_LABELS` constant across 3+ modules

- Issue: The `REGION_LABELS` dictionary is copy-pasted in at least 4 locations: `backend/app/services/import_service.py` (line 68), `backend/app/exporters/template_exporter.py` (line 165), `backend/app/services/aggregate_service.py` (imports from region_detection_service), and the canonical source at `backend/app/services/region_detection_service.py` (line 20). Some modules import it, others define their own copy.
- Files:
  - `backend/app/services/region_detection_service.py` (canonical)
  - `backend/app/services/import_service.py` (duplicate)
  - `backend/app/exporters/template_exporter.py` (duplicate)
- Impact: Adding a new region requires finding and updating all copies. Drift between copies causes silent parsing/export failures.
- Fix approach: Consolidate into a single shared location (e.g., `backend/app/mappings/regions.py`) and import everywhere.

### HIGH: Duplicated `FILENAME_NOISE` and `DATE_PATTERN` across modules

- Issue: Both `backend/app/services/import_service.py` and `backend/app/services/aggregate_service.py` define identical `FILENAME_NOISE` tuples and `DATE_PATTERN` regex. The `_infer_company_name_from_filename` function also appears duplicated.
- Files: `backend/app/services/import_service.py` (lines 50-65, 49), `backend/app/services/aggregate_service.py` (lines 28-45)
- Impact: Bug fixes or new noise patterns must be applied in multiple places.
- Fix approach: Extract shared filename utilities into a common module.

### HIGH: `normalization_service.py` is 863 lines with region-specific logic hardcoded

- Issue: This single file contains Wuhan transactional merging logic, Changsha transaction-item mapping, and general normalization. Region-specific constants (`WUHAN_TRANSACTION_FILL_DOWN_HEADERS`, `CHANGSHA_TRANSACTION_ITEM_FIELD_MAP`, etc.) are embedded directly.
- Files: `backend/app/services/normalization_service.py`
- Impact: Adding new region-specific logic will keep bloating this file. Testing individual region behaviors requires wading through unrelated code. Risk of accidentally breaking one region when modifying another.
- Fix approach: Extract region-specific normalization strategies into separate modules under `backend/app/parsers/regions/` or `backend/app/services/region_normalizers/`.

### MEDIUM: `template_exporter.py` is 1160 lines

- Issue: The export module handles both template types (salary and final_tool), contains hardcoded header arrays (lines 174-186), burden calculation logic, row formatting, and cell-level operations in a single file.
- Files: `backend/app/exporters/template_exporter.py`
- Impact: Difficult to maintain; adding a third template type will further bloat the file.
- Fix approach: Split into separate modules per template type and a shared utility module for cell operations.

### MEDIUM: Duplicate `ID_NUMBER_PATTERN` and `NON_MAINLAND_ID_NUMBER_PATTERN` regex

- Issue: These regex patterns are defined identically in both `backend/app/services/matching_service.py` (line 23-24) and `backend/app/exporters/template_exporter.py` (line 37-38).
- Files: `backend/app/services/matching_service.py`, `backend/app/exporters/template_exporter.py`
- Impact: Inconsistent ID validation if one copy is updated but not the other.
- Fix approach: Move to a shared validators/constants module.

---

## Security Considerations

### HIGH: Self-service endpoint lacks authentication

- Risk: The `/employees/self-service/query` endpoint at `backend/app/api/v1/employees.py` line 77 does NOT have `require_authenticated_user` as a dependency. While the `employees` router is included in `backend/app/api/v1/router.py` line 21 without a router-level auth dependency (unlike all other protected routers), individual endpoints DO apply auth via `_user=Depends(require_authenticated_user)` -- except the self-service query endpoint.
- Files: `backend/app/api/v1/employees.py` (line 77-86), `backend/app/api/v1/router.py` (line 21)
- Current mitigation: The endpoint only returns limited employee data, but it still exposes PII (name, ID number match results) without authentication.
- Recommendations: Either add `_user=Depends(require_authenticated_user)` to the endpoint or document it as intentionally public with rate limiting.

### HIGH: Default credentials hardcoded in source

- Risk: `backend/app/core/config.py` hardcodes `admin123` and `hr123` as default passwords (lines 13-14). While `backend/app/bootstrap.py` blocks unsafe defaults in non-local environments, the `runtime_environment` defaults to `'local'` which bypasses all guardrails. If deployed without setting `runtime_environment`, default credentials are active.
- Files: `backend/app/core/config.py` (lines 12-14, 65-70), `backend/app/bootstrap.py`
- Current mitigation: `validate_auth_runtime_guardrails()` in bootstrap blocks non-local runtimes with defaults.
- Recommendations: Log a warning even in local mode when defaults are active. Consider requiring explicit opt-in for default credentials.

### MEDIUM: Custom token implementation instead of standard JWT

- Risk: `backend/app/core/auth.py` implements a custom base64+HMAC token scheme instead of using a standard JWT library. Custom crypto code is harder to audit and may have subtle issues (e.g., no `iss`/`aud` claims, no token revocation, no refresh tokens).
- Files: `backend/app/core/auth.py`
- Current mitigation: The implementation uses `hmac.compare_digest` for timing-safe comparison and validates expiry.
- Recommendations: Consider migrating to `python-jose` or `PyJWT` for standard JWT support with broader claim validation.

### MEDIUM: CORS allows credentials with configurable origins

- Risk: `backend/app/main.py` line 69-73 sets `allow_credentials=True` with `allow_methods=["*"]` and `allow_headers=["*"]`. While origins are configurable, the default includes only localhost. If deployed with a wildcard origin, this would be a credential-stealing vulnerability.
- Files: `backend/app/main.py` (lines 67-73), `backend/app/core/config.py` (line 44)
- Recommendations: Validate that `backend_cors_origins` never contains `*` when `allow_credentials=True`.

### LOW: Upload guard only checks Content-Length header

- Risk: `backend/app/core/upload_guard.py` relies on the `Content-Length` header to reject oversized uploads. A malicious client can omit this header or lie about the size. The actual size check in `_store_upload` (import_service.py line 938) is the real safeguard.
- Files: `backend/app/core/upload_guard.py`, `backend/app/services/import_service.py` (line 938)
- Current mitigation: The streaming upload handler in `_store_upload` enforces the size limit by counting bytes as they arrive.
- Recommendations: Document that `UploadGuardMiddleware` is a fast-reject optimization, not a security boundary.

---

## Performance Bottlenecks

### HIGH: Entire workbook loaded into memory for parsing

- Issue: `normalization_service.py` line 441-452 opens workbooks in `read_only=True` mode but immediately materializes all rows into a Python list via `list(sheet.iter_rows(...))`. For large files (10,000+ rows), this consumes significant memory.
- Files: `backend/app/services/normalization_service.py` (lines 441-452)
- Cause: `list()` call forces full materialization. The subsequent loop could process rows lazily.
- Improvement path: Process rows in a streaming fashion using the iterator directly instead of `list()`.

### HIGH: Employee matching is O(n*m) per batch

- Issue: `backend/app/services/matching_service.py` line 98 iterates over ALL active employees for EACH record to find ID number matches. For a batch with 500 records and 5,000 employees, this is 2.5M comparisons.
- Files: `backend/app/services/matching_service.py` (lines 89-145)
- Cause: Linear scan instead of indexed lookup.
- Improvement path: Build a `dict[str, EmployeeMaster]` keyed by normalized `id_number` and `person_name` before matching. This reduces lookup to O(1) per record.

### MEDIUM: Streaming endpoint reads all files into memory before processing

- Issue: `backend/app/api/v1/aggregate.py` lines 72-94 reads ALL uploaded file contents into memory (`await upload.read()`) before starting the streaming response. This defeats the purpose of streaming for large batches.
- Files: `backend/app/api/v1/aggregate.py` (lines 72-94)
- Cause: Files must be fully read before the response generator starts because `UploadFile` objects cannot be read after the request body is consumed.
- Improvement path: Stream files to disk first, then process from disk in the background task.

### MEDIUM: ThreadPoolExecutor for parallel parsing

- Issue: `backend/app/services/import_service.py` uses `ThreadPoolExecutor` with `MAX_PARSE_WORKERS = 5` for parallel file parsing. Python's GIL limits true parallelism for CPU-bound openpyxl parsing.
- Files: `backend/app/services/import_service.py` (line 48)
- Cause: openpyxl is CPU-bound Python code; threads don't bypass GIL.
- Improvement path: Use `ProcessPoolExecutor` for genuine parallelism, or accept the I/O-bound benefit of threads for disk reads.

---

## Scalability Limits

### HIGH: SQLite as production database

- Issue: The default database is SQLite (`sqlite:///./data/app.db`). While PostgreSQL connection settings exist in config, the actual deployment uses SQLite with WAL mode. SQLite has single-writer concurrency, which will bottleneck under concurrent batch imports.
- Files: `backend/app/core/config.py` (line 46), `backend/app/core/database.py`
- Current capacity: Single concurrent writer; reads are concurrent with WAL.
- Limit: Multiple simultaneous batch imports will queue behind `PRAGMA busy_timeout=120000` (2 minutes).
- Scaling path: Migrate to PostgreSQL for production use (connection pool settings already exist in config).

### MEDIUM: File storage on local filesystem

- Issue: Uploaded files are stored at `./data/uploads/` with no cloud storage option. The `data/` directory includes the SQLite database, uploads, and outputs.
- Files: `backend/app/core/config.py` (lines 50-53)
- Limit: Single-server deployment; no horizontal scaling possible.
- Scaling path: Add S3/MinIO integration for file storage.

---

## Fragile Areas

### HIGH: Export template header matching is position-dependent

- Issue: `backend/app/exporters/template_exporter.py` hardcodes expected header arrays (`SALARY_HEADERS`, `TOOL_HEADERS`) at specific row positions (`SALARY_HEADER_ROW = 1`, `TOOL_HEADER_ROW = 6`). If the template Excel files are modified (columns reordered, headers renamed), exports silently produce wrong data.
- Files: `backend/app/exporters/template_exporter.py` (lines 21-24, 174-186)
- Why fragile: Template files are external and can be modified by users without code changes.
- Safe modification: Any template change requires updating the corresponding header constants and row offsets in code.
- Test coverage: `backend/tests/test_template_exporter.py` (1183 lines) covers regression scenarios well.

### HIGH: Wuhan transactional merge strategy

- Issue: The Wuhan region uses a unique "transactional" format where each insurance type is a separate row that must be collapsed into a single person record. This merge logic (`_collapse_wuhan_transactional_records`, lines 626-662) depends on exact header signatures and carry-forward fill-down behavior.
- Files: `backend/app/services/normalization_service.py` (lines 588-740)
- Why fragile: Any change in Wuhan's export format (new insurance types, renamed columns) silently breaks merging. The Unicode escape sequences for header names make the code hard to read and verify.
- Safe modification: Always test with real Wuhan sample files. Add new insurance types to `WUHAN_TRANSACTION_ITEM_FIELD_MAP`.

### MEDIUM: Region detection is heuristic-based

- Issue: `backend/app/services/region_detection_service.py` (428 lines) uses filename keywords and workbook content heuristics to detect regions. Misdetection causes wrong normalization rules to apply.
- Files: `backend/app/services/region_detection_service.py`
- Why fragile: New region names or company names not in the keyword list will fail to detect.
- Test coverage: `backend/tests/test_region_detection_service.py` exists but coverage of edge cases is unclear.

---

## Dependencies at Risk

### MEDIUM: `psycopg2-binary` and `asyncpg` unused

- Risk: `backend/requirements.txt` includes `psycopg2-binary==2.9.10` and `asyncpg==0.30.0` but the application only uses SQLite. These add installation complexity (psycopg2 requires libpq on some platforms) without benefit.
- Impact: Slower installs, potential build failures on systems without PostgreSQL development libraries.
- Migration plan: Remove until PostgreSQL support is actually needed, or make them optional dependencies.

### LOW: `loguru` imported but structured logging uses stdlib

- Risk: `backend/requirements.txt` includes `loguru==0.7.3`, but `backend/app/core/logging.py` and API modules use `logging` (stdlib). Unused dependency.
- Files: `backend/requirements.txt`, `backend/app/core/logging.py`
- Impact: Minor bloat.
- Migration plan: Remove `loguru` from requirements or migrate logging to use it consistently.

---

## Missing Critical Features

### Employee self-service has no rate limiting

- Problem: The unauthenticated `/employees/self-service/query` endpoint allows unlimited queries by ID number, enabling enumeration of employee data.
- Files: `backend/app/api/v1/employees.py` (line 77)
- Blocks: Safe public deployment.

### No database migration strategy for production

- Problem: Alembic migrations exist (`backend/alembic/`) but there is no documented migration workflow or CI integration. The SQLite database at `data/app.db` is committed to version control (appears in git status as modified).
- Files: `backend/alembic/`, `data/app.db`
- Blocks: Reliable production deployments.

### No backup or data retention policy

- Problem: Uploaded Excel files accumulate in `data/uploads/` with no automatic cleanup. Exported files accumulate in `data/outputs/`. No TTL or archival mechanism exists.
- Files: `backend/app/core/config.py` (lines 50-53)
- Blocks: Long-running deployments without manual intervention.

---

## Test Coverage Gaps

### No integration tests with real sample files

- What's not tested: The full pipeline from upload through parsing, normalization, matching, and export using actual region sample files (Guangzhou, Hangzhou, Xiamen, Shenzhen, Wuhan, Changsha).
- Files: `backend/tests/test_region_sample_regression.py` exists but its scope is unclear without reading it.
- Risk: Parsing regressions for specific regions go unnoticed.
- Priority: High

### Export template regression tests use synthetic templates

- What's not tested: `backend/tests/test_template_exporter.py` and `backend/tests/test_template_exporter_regression.py` use test fixtures from `backend/tests/support/export_fixtures.py` with synthetic templates, not the actual production templates referenced in `CLAUDE.md`.
- Files: `backend/tests/support/export_fixtures.py`, `data/templates/regression/`
- Risk: Production template format changes (header positions, column counts) are not caught by tests.
- Priority: High

### No frontend tests

- What's not tested: The entire React frontend has zero test files. No unit tests, no component tests, no E2E tests.
- Files: `frontend/src/` (all 47 source files)
- Risk: UI regressions, broken API integrations, and state management bugs go unnoticed.
- Priority: Medium

### No load/concurrency tests

- What's not tested: Concurrent batch imports, parallel file parsing, SQLite write contention under load.
- Risk: Production failures under concurrent usage, especially with SQLite's single-writer limitation.
- Priority: Medium

---

*Concerns audit: 2026-03-27*
