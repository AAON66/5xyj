# Technology Stack

**Analysis Date:** 2026-03-25

## Languages

**Primary:**
- Python 3.11+ target runtime - backend API, parsing, normalization, exporting, and persistence in `backend/app/`; current workspace also contains CPython 3.13 bytecode artifacts in `backend/app/__pycache__/` and `backend/tests/__pycache__/`
- TypeScript 5.8.x - frontend SPA code in `frontend/src/`, compiled with `frontend/tsconfig.json`

**Secondary:**
- PowerShell - local developer startup and Windows automation in `start_backend_local.ps1`, `start_frontend_local.ps1`, and `start_project_local.ps1`
- Bash - Linux deployment helpers in `deploy.sh`, `deploy_service.sh`, and `auto_deploy.sh`
- SQL migrations - schema evolution via Alembic scripts in `backend/alembic/versions/`

## Runtime

**Environment:**
- Backend ASGI runtime: Uvicorn serving `backend.app.main:app` from `backend/run.py`
- Frontend dev runtime: Vite server on `127.0.0.1:5173` configured in `frontend/vite.config.ts`
- Documented runtime requirements: Python 3.11+, Node.js 18+, npm 9+, SQLite 3.35+ in `DEPLOYMENT.md`

**Package Manager:**
- Python: `pip` from `backend/requirements.txt`
- Python lockfile: missing
- Node: `npm` from `frontend/package.json`
- Lockfile: present at `frontend/package-lock.json`

## Frameworks

**Core:**
- FastAPI 0.115.0 - backend HTTP API, validation, multipart handling, and middleware in `backend/app/main.py` and `backend/app/api/v1/`
- React 18.3.1 - frontend application shell and pages in `frontend/src/App.tsx` and `frontend/src/pages/`
- React Router DOM 6.30.0 - client-side routing in `frontend/src/App.tsx`
- SQLAlchemy 2.0.36 - ORM models and sessions in `backend/app/models/` and `backend/app/core/database.py`

**Testing:**
- pytest 8.3.4 - backend test suite in `backend/tests/`
- FastAPI TestClient - API-level tests in files such as `backend/tests/test_auth_api.py` and `backend/tests/test_import_batches_api.py`
- No dedicated frontend test runner detected in `frontend/package.json`

**Build/Dev:**
- Vite 6.2.1 - frontend dev server and production bundling in `frontend/package.json` and `frontend/vite.config.ts`
- TypeScript 5.8.2 - strict type checking during frontend build in `frontend/package.json` and `frontend/tsconfig.json`
- ESLint 9.23.0 + `typescript-eslint` - frontend linting in `frontend/eslint.config.js`
- Alembic 1.14.0 - database migrations in `backend/alembic/` and `backend/alembic.ini`
- Uvicorn 0.32.0 - backend application server in `backend/run.py`

## Key Dependencies

**Critical:**
- `openpyxl` 3.1.5 - Excel workbook reading and template rewriting in `backend/app/parsers/workbook_loader.py`, `backend/app/exporters/template_exporter.py`, and `backend/app/services/compare_service.py`
- `pandas` 2.2.3 - employee master spreadsheet import in `backend/app/services/employee_service.py`
- `httpx` 0.28.1 - DeepSeek fallback requests in `backend/app/services/llm_mapping_service.py` and `backend/app/services/region_detection_service.py`
- `axios` 1.8.4 - frontend API client in `frontend/src/services/api.ts`
- `python-multipart` 0.0.12 - FastAPI `UploadFile` request parsing for endpoints in `backend/app/api/v1/imports.py`, `backend/app/api/v1/employees.py`, and `backend/app/api/v1/aggregate.py`

**Infrastructure:**
- `pydantic` 2.10.3 + `pydantic-settings` 2.6.1 - runtime settings and response schemas in `backend/app/core/config.py` and `backend/app/schemas/`
- `psycopg2-binary` 2.9.10 + `asyncpg` 0.30.0 - PostgreSQL support declared in `backend/requirements.txt`, though live code defaults to SQLite in `backend/app/core/config.py`
- `xlrd` - legacy `.xls` parsing is implemented in `backend/app/parsers/workbook_loader.py`, but this package is not declared in `backend/requirements.txt`; helper installation scripts such as `install_xlrd.py` indicate a manual runtime dependency
- `loguru` 0.7.3 - declared in `backend/requirements.txt`, but current logging code uses the standard library `logging` module in `backend/app/core/logging.py`

## Configuration

**Environment:**
- Backend settings load from the project-root `.env` file via `backend/app/core/config.py`
- Safe template values live in `.env.example`
- Frontend backend endpoint selection comes from `VITE_API_BASE_URL` in `frontend/src/config/env.ts`
- Runtime bootstrap ensures `data/uploads`, `data/samples`, `data/templates`, and `data/outputs` exist in `backend/app/bootstrap.py`

**Build:**
- Frontend build config: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/eslint.config.js`
- Backend runtime and migration config: `backend/run.py`, `backend/app/main.py`, `backend/alembic.ini`, `backend/alembic/env.py`
- Local startup scripts: `start_backend_local.ps1`, `start_frontend_local.ps1`, `start_project_local.ps1`

## Platform Requirements

**Development:**
- Python virtual environment expected at `.venv/` by `start_backend_local.ps1`
- Node dependencies expected under `frontend/node_modules/` by `start_frontend_local.ps1`
- Default local database is SQLite at `data/app.db`, with WAL files `data/app.db-wal` and `data/app.db-shm`
- Excel samples and export templates are expected under `data/samples/` and `data/templates/`

**Production:**
- Documented deployment target is Linux with Uvicorn + systemd + optional Nginx reverse proxy in `DEPLOYMENT.md`
- `deploy_service.sh` provisions a systemd unit that starts `uvicorn backend.app.main:app`
- Docker deployment is documented in `DEPLOYMENT.md`, but checked-in Docker assets such as `docker-compose.yml`, `Dockerfile.backend`, and `Dockerfile.frontend` are not present in the repository root

---

*Stack analysis: 2026-03-25*
