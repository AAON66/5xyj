# External Integrations

**Analysis Date:** 2026-03-25

## APIs & External Services

**LLM Fallback:**
- DeepSeek Chat Completions API - fallback semantic mapping for header normalization and workbook region detection
  - SDK/Client: `httpx` in `backend/app/services/llm_mapping_service.py` and `backend/app/services/region_detection_service.py`
  - Auth: `DEEPSEEK_API_KEY`
  - Base URL and model config: `DEEPSEEK_API_BASE_URL`, `DEEPSEEK_MODEL` in `backend/app/core/config.py`
  - Runtime gate: `ENABLE_LLM_FALLBACK` in `backend/app/core/config.py`

**Frontend-to-Backend HTTP Boundary:**
- Internal REST API - React frontend talks to FastAPI backend over HTTP
  - Client: `axios` instance in `frontend/src/services/api.ts`
  - Streaming client: browser `fetch` for `/aggregate/stream` in `frontend/src/services/aggregate.ts`
  - Auth: bearer token added from browser session storage in `frontend/src/services/api.ts` and `frontend/src/services/aggregate.ts`
  - Base URL: `VITE_API_BASE_URL` resolved in `frontend/src/config/env.ts`

**Employee Master Input:**
- Uploaded employee roster spreadsheets - employee identity data is imported by users rather than synced from an HRIS
  - Parser: `pandas` in `backend/app/services/employee_service.py`
  - Auth: same backend bearer auth as the rest of the API

## Data Storage

**Databases:**
- SQLite
  - Connection: `DATABASE_URL` defaulting to `sqlite:///./data/app.db` in `backend/app/core/config.py`
  - Client: SQLAlchemy engine/session in `backend/app/core/database.py`
  - Migration layer: Alembic in `backend/alembic/`
- PostgreSQL
  - Connection: `DATABASE_URL` override documented in `.env.example` and `DEPLOYMENT.md`
  - Client: SQLAlchemy in `backend/app/core/database.py`
  - Driver packages: `psycopg2-binary` and `asyncpg` in `backend/requirements.txt`

**File Storage:**
- Local filesystem only
  - Upload intake: `data/uploads/` from `backend/app/core/config.py`
  - Sample inputs: `data/samples/` from `backend/app/core/config.py`
  - Export templates: `data/templates/` plus explicit `SALARY_TEMPLATE_PATH` and `FINAL_TOOL_TEMPLATE_PATH` in `backend/app/core/config.py`
  - Export outputs: `data/outputs/` from `backend/app/core/config.py`
  - Export implementation: `backend/app/exporters/template_exporter.py`

**Caching:**
- None detected
  - No Redis, Memcached, or in-process cache service imports were found in `backend/app/` or `frontend/src/`

## Authentication & Identity

**Auth Provider:**
- Custom in-app authentication
  - Implementation: username/password login plus HMAC-SHA256 signed bearer token issuance in `backend/app/core/auth.py`
  - API surface: `backend/app/api/v1/auth.py`
  - Request enforcement: `backend/app/dependencies.py` with `fastapi.security.HTTPBearer`
  - Frontend session persistence: browser `sessionStorage` in `frontend/src/services/authSession.ts`

## Monitoring & Observability

**Error Tracking:**
- None
  - No Sentry, Rollbar, Bugsnag, or similar integrations detected in `backend/app/` or `frontend/src/`

**Logs:**
- Standard library logging with optional JSON formatting
  - Backend formatter: `backend/app/core/logging.py`
  - Config knobs: `LOG_LEVEL` and `LOG_FORMAT` in `backend/app/core/config.py`
  - Runtime log files currently present under `data/` and root-level dev logs such as `backend-dev.log` and `frontend-dev.log`

## CI/CD & Deployment

**Hosting:**
- Local development
  - Backend: `start_backend_local.ps1` runs Alembic migrations and `python -m backend.run`
  - Frontend: `start_frontend_local.ps1` installs npm packages on demand and starts Vite
- Linux service deployment
  - Documented in `DEPLOYMENT.md`
  - Automated shell provisioning in `deploy_service.sh` creates a systemd service for `uvicorn backend.app.main:app`
- Reverse proxy
  - Nginx is documented in `DEPLOYMENT.md`
- Docker
  - Documented in `DEPLOYMENT.md`
  - Not checked in as runnable assets: `docker-compose.yml`, `Dockerfile.backend`, and `Dockerfile.frontend` are not present at the project root

**CI Pipeline:**
- None detected
  - No `.github/workflows/` directory or other checked-in CI pipeline definitions were found in the repository root

## Environment Configuration

**Required env vars:**
- Backend application: `APP_NAME`, `APP_VERSION`, `API_V1_PREFIX`, `BACKEND_CORS_ORIGINS`
- Database: `DATABASE_URL`, `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`
- Filesystem paths: `UPLOAD_DIR`, `SAMPLES_DIR`, `TEMPLATES_DIR`, `OUTPUTS_DIR`, `SALARY_TEMPLATE_PATH`, `FINAL_TOOL_TEMPLATE_PATH`
- LLM fallback: `DEEPSEEK_API_KEY`, `DEEPSEEK_API_BASE_URL`, `DEEPSEEK_MODEL`, `ENABLE_LLM_FALLBACK`
- Frontend runtime target: `VITE_API_BASE_URL`
- Backend auth, from actual code in `backend/app/core/config.py`: `AUTH_ENABLED`, `AUTH_SECRET_KEY`, `AUTH_TOKEN_EXPIRE_MINUTES`, `ADMIN_LOGIN_USERNAME`, `ADMIN_LOGIN_PASSWORD`, `HR_LOGIN_USERNAME`, `HR_LOGIN_PASSWORD`

**Secrets location:**
- Root `.env` file is loaded by `backend/app/core/config.py`
- Safe example values live in `.env.example`
- Frontend reads build-time environment via Vite in `frontend/src/config/env.ts`

## Webhooks & Callbacks

**Incoming:**
- None
  - Long-running work is streamed directly over HTTP from `POST /aggregate/stream` in `backend/app/api/v1/aggregate.py` to `frontend/src/services/aggregate.ts`; this is not a webhook callback model

**Outgoing:**
- DeepSeek HTTPS requests only
  - Header mapping fallback in `backend/app/services/llm_mapping_service.py`
  - Region detection fallback in `backend/app/services/region_detection_service.py`

---

*Integration audit: 2026-03-25*
