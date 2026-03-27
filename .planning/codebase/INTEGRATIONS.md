# External Integrations

**Analysis Date:** 2026-03-27

## APIs Exposed

**REST API (FastAPI):**
- Base prefix: `/api/v1` (configurable via `API_V1_PREFIX`)
- Health check: `GET /health`
- Entry point: `backend/app/main.py` -> `backend/app/api/v1/router.py`

**API Route Groups:**
| Route Module | File | Auth Required |
|---|---|---|
| Auth (login/token) | `backend/app/api/v1/auth.py` | No |
| System | `backend/app/api/v1/system.py` | No |
| Imports (file upload) | `backend/app/api/v1/imports.py` | Yes |
| Dashboard | `backend/app/api/v1/dashboard.py` | Yes |
| Mappings | `backend/app/api/v1/mappings.py` | Yes |
| Aggregate | `backend/app/api/v1/aggregate.py` | Yes |
| Compare | `backend/app/api/v1/compare.py` | Yes |
| Employees | `backend/app/api/v1/employees.py` | No |

**Response Format:**
- Standardized via `backend/app/api/v1/responses.py`
- Success: `{ success: true, message: string, data: T }`
- Error: `{ success: false, error: { code: string, message: string, details?: any } }`

## APIs Consumed

**DeepSeek LLM API:**
- Purpose: Fallback header-to-canonical-field mapping when rule-based matching fails
- Client: `httpx` (both async and sync)
- Implementation: `backend/app/services/llm_mapping_service.py`
- Endpoint: `{DEEPSEEK_API_BASE_URL}/chat/completions` (default: `https://api.deepseek.com/v1/chat/completions`)
- Auth: Bearer token via `DEEPSEEK_API_KEY` env var
- Model: configurable via `DEEPSEEK_MODEL` (default: `deepseek-chat`)
- Timeout: 45 seconds
- Degradation: Graceful - returns `skipped_no_api_key` or `disabled` status when key is missing or feature is toggled off
- Toggle: `ENABLE_LLM_FALLBACK` env var (default: `true`)

**LLM Request Schema:**
```json
{
  "model": "deepseek-chat",
  "temperature": 0.0,
  "response_format": { "type": "json_object" },
  "messages": [
    { "role": "system", "content": "Chinese social security header normalization prompt" },
    { "role": "user", "content": "{ region, raw_header_signature, canonical_fields }" }
  ]
}
```

**LLM Response Handling:**
- Parses JSON from response content (handles markdown fenced blocks)
- Validates `canonical_field` against known `CANONICAL_FIELDS` set
- Coerces confidence values (numeric, percentage, text labels like "high"/"medium")
- Returns structured `LLMMappingResult` dataclass

## Data Storage

**Primary Database:**
- Engine: SQLite (default) or PostgreSQL (production)
- Default path: `data/app.db` (SQLite WAL mode enabled)
- Connection: `DATABASE_URL` env var
- ORM: SQLAlchemy 2.0 with synchronous sessions
- Session factory: `backend/app/core/database.py`
- SQLite pragmas: WAL journal, 120s busy timeout, foreign keys ON, synchronous NORMAL

**Database Models:**
| Model | File | Purpose |
|---|---|---|
| ImportBatch | `backend/app/models/import_batch.py` | Upload batch tracking |
| SourceFile | `backend/app/models/source_file.py` | Individual uploaded files |
| HeaderMapping | `backend/app/models/header_mapping.py` | Header-to-field mappings |
| NormalizedRecord | `backend/app/models/normalized_record.py` | Standardized data rows |
| EmployeeMaster | `backend/app/models/employee_master.py` | Employee reference data |
| EmployeeMasterAudit | `backend/app/models/employee_master_audit.py` | Employee data change log |
| MatchResult | `backend/app/models/match_result.py` | Employee ID matching results |
| ValidationIssue | `backend/app/models/validation_issue.py` | Data quality issues |
| ExportJob | `backend/app/models/export_job.py` | Export task tracking |
| ExportArtifact | `backend/app/models/export_artifact.py` | Generated export files |

**File Storage (Local Filesystem):**
| Directory | Config Key | Purpose |
|---|---|---|
| `data/uploads/` | `UPLOAD_DIR` | Uploaded Excel files (organized by batch UUID) |
| `data/samples/` | `SAMPLES_DIR` | Reference sample files for testing |
| `data/templates/` | `TEMPLATES_DIR` | Export template files |
| `data/outputs/` | `OUTPUTS_DIR` | Generated export files |
| `data/external/` | N/A | External reference data (roster, housing fund, allin) |

**External Data Sources (File-based):**
- `data/external/roster/` - Employee roster/master data
- `data/external/housing_fund/` - Housing fund reference data
- `data/external/allin/` - Additional reference data

**Caching:**
- None detected (no Redis, memcached, or in-memory cache beyond `lru_cache` on Settings)

## File I/O Patterns

**Upload Flow:**
- Frontend sends multipart form data via `axios`
- Backend receives via `python-multipart` + FastAPI `UploadFile`
- Files stored to `data/uploads/{batch_uuid}/` on disk
- Upload size guard: `UploadGuardMiddleware` in `backend/app/core/upload_guard.py` (default 25 MB)

**Excel Parsing Pipeline:**
- Workbook discovery: `backend/app/parsers/workbook_discovery.py` - identifies valid sheets
- Workbook loading: `backend/app/parsers/workbook_loader.py` - loads Excel via openpyxl
- Header extraction: `backend/app/parsers/header_extraction.py` - locates header rows in multi-row headers
- Uses `openpyxl` for all Excel read operations

**Excel Export Pipeline:**
- Template-based export: `backend/app/exporters/template_exporter.py`
- Uses `openpyxl` to load template workbooks and fill data
- Two fixed output templates (salary template + tool table template)
- Template paths configured via `SALARY_TEMPLATE_PATH` and `FINAL_TOOL_TEMPLATE_PATH`

**Sample Data:**
- Social security files from 6+ regions: Guangzhou, Hangzhou, Xiamen, Shenzhen, Wuhan, Changsha
- Housing fund files from matching regions in `data/samples/公积金/`
- Various Excel structures: single-row headers, multi-row headers, pivot-style layouts

## Authentication & Authorization

**Auth Provider:** Custom HMAC-based token system (no external auth service)

**Implementation:** `backend/app/core/auth.py`
- Two roles: `admin` and `hr` (`AuthRole` literal type)
- Username/password pairs configured via env vars (`ADMIN_LOGIN_USERNAME`, `ADMIN_LOGIN_PASSWORD`, `HR_LOGIN_USERNAME`, `HR_LOGIN_PASSWORD`)
- Password comparison uses `hmac.compare_digest` for timing-safe comparison

**Token System:**
- Custom JWT-like tokens (base64-encoded JSON payload + HMAC-SHA256 signature)
- Not using standard JWT libraries in main requirements (no `python-jose` in `requirements.txt`)
- Token expiry: configurable via `AUTH_TOKEN_EXPIRE_MINUTES` (default: 480 minutes / 8 hours)
- Signing key: `AUTH_SECRET_KEY` env var

**Frontend Auth:**
- Token stored in browser session (`frontend/src/services/authSession.ts`)
- Axios interceptor attaches `Authorization: Bearer {token}` header (`frontend/src/services/api.ts`)
- Auto-clears session on 401 response
- Auth context via React Context (`frontend/src/hooks/authContext.ts`, `frontend/src/components/AuthProvider.tsx`)

**Auth Toggle:**
- `AUTH_ENABLED` env var (default: `true`)
- When disabled, uses `default_authenticated_user()` returning `local-dev` admin user
- Security warnings for unsafe default passwords and secret keys (`backend/app/core/config.py`)

**Route Protection:**
- `require_authenticated_user` dependency applied at router level (`backend/app/api/v1/router.py`)
- Auth and System routes are unprotected
- Employees route is unprotected (for self-service)

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, or similar)

**Logging:**
- Backend: stdlib `logging` with custom JSON formatter (`backend/app/core/logging.py`)
- Two formats: `json` (default) and `plain`
- Log level configurable via `LOG_LEVEL` env var
- Runtime logs written to `data/backend_runtime.log` and `data/backend_runtime.err.log`
- Frontend logs written to `data/frontend_runtime.log` and `data/frontend_runtime.err.log`
- `loguru` 0.7.3 in requirements but primary logging uses stdlib

## CI/CD & Deployment

**Hosting:**
- No cloud platform configuration detected
- Deployment scripts suggest manual server deployment (`server_deploy.sh`, `deploy_guide.bat`, `deploy_fix.sh`)
- Documentation in `DEPLOYMENT.md`, `DEPLOYMENT_SERVER.md`, `DEPLOY_FIX.md`

**CI Pipeline:**
- None detected (no `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`)

**Startup Scripts:**
- Local Windows: `start_project_local.cmd` / `start_project_local.ps1` (starts both backend and frontend)
- Server: `server_deploy.sh`

## Environment Configuration

**Required env vars (minimum to run):**
- None strictly required - all have defaults in `Settings` class
- SQLite is default database, no external services needed

**Recommended for production:**
- `DATABASE_URL` - PostgreSQL connection string
- `AUTH_SECRET_KEY` - Strong random secret (not the default)
- `ADMIN_LOGIN_PASSWORD` - Non-default admin password
- `HR_LOGIN_PASSWORD` - Non-default HR password
- `SALARY_TEMPLATE_PATH` - Path to salary export template
- `FINAL_TOOL_TEMPLATE_PATH` - Path to tool table export template

**Optional:**
- `DEEPSEEK_API_KEY` - Enables LLM fallback for header mapping
- `VITE_API_BASE_URL` - Frontend API target for production builds

**Secrets Location:**
- `.env` file at project root (gitignored)
- `.env.example` documents all variables with safe defaults

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None

## CORS Configuration

- Configured in `backend/app/main.py` via FastAPI `CORSMiddleware`
- Default origins: `http://localhost:5173`, `http://127.0.0.1:5173`
- Configurable via `BACKEND_CORS_ORIGINS` env var (JSON array)
- All methods and headers allowed, credentials enabled

---

*Integration audit: 2026-03-27*
