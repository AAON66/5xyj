# Technology Stack

**Analysis Date:** 2026-03-27

## Languages

**Primary:**
- Python 3.x - Backend API, data processing, parsing, export (`backend/`)
- TypeScript 5.8 - Frontend SPA (`frontend/`)

**Secondary:**
- SQL (SQLite dialect) - Database schema and queries via SQLAlchemy ORM
- Bash - Deployment and startup scripts (`scripts/`, `deploy_fix.sh`, `server_deploy.sh`)
- PowerShell / Batch - Local dev startup (`start_backend_local.ps1`, `start_frontend_local.cmd`)

## Runtime

**Backend:**
- Python (no `.python-version` file; inferred 3.10+ from type hint syntax like `X | Y` and `list[str]`)
- Uvicorn ASGI server (uvicorn 0.32.0)

**Frontend:**
- Node.js (no `.nvmrc`; Vite 6.2 requires Node 18+)
- Vite 6.2.1 dev server on `127.0.0.1:5173`

**Package Managers:**
- pip (Python) - `backend/requirements.txt`, `backend/requirements.server.txt`
- npm (Node) - `frontend/package.json`
- Lockfile: `package-lock.json` not confirmed; no `yarn.lock` or `pnpm-lock.yaml` detected

## Frameworks

**Core:**
- FastAPI 0.115.0 - REST API framework (`backend/app/main.py`)
- React 18.3.1 - Frontend UI (`frontend/src/`)
- React Router DOM 6.30.0 - Client-side routing

**Data Processing:**
- pandas 2.2.3 - Tabular data manipulation, aggregation
- openpyxl 3.1.5 - Excel file reading and writing (`.xlsx`)

**ORM / Database:**
- SQLAlchemy 2.0.36 - ORM and database engine (`backend/app/core/database.py`)
- Alembic 1.14.0 - Database migrations (listed in requirements, migration files not confirmed)

**Testing:**
- pytest 8.3.4 - Backend test runner (listed in `requirements.txt`)
- No frontend test framework detected (no vitest, jest, or testing-library in `package.json`)

**Build/Dev:**
- Vite 6.2.1 - Frontend bundler and dev server (`frontend/vite.config.ts`)
- `@vitejs/plugin-react` 4.4.1 - React Fast Refresh support
- TypeScript 5.8.2 - Type checking (`frontend/tsconfig.json`)
- ESLint 9.23.0 - Frontend linting with `eslint-plugin-react-hooks` and `eslint-plugin-react-refresh`

## Key Dependencies

**Critical (Backend):**
- `fastapi` 0.115.0 - API framework; all endpoints defined under `backend/app/api/v1/`
- `pandas` 2.2.3 - Core data processing for social security record normalization
- `openpyxl` 3.1.5 - Excel I/O for both parsing uploads and writing export templates
- `sqlalchemy` 2.0.36 - All database access; models in `backend/app/models/`
- `pydantic` 2.10.3 + `pydantic-settings` 2.6.1 - Request/response validation and app configuration (`backend/app/core/config.py`)
- `httpx` 0.28.1 - Async/sync HTTP client for DeepSeek LLM API calls (`backend/app/services/llm_mapping_service.py`)

**Critical (Frontend):**
- `react` 18.3.1 + `react-dom` 18.3.1 - UI rendering
- `axios` 1.8.4 - HTTP client for backend API (`frontend/src/services/api.ts`)
- `react-router-dom` 6.30.0 - Page routing (`frontend/src/App.tsx`)

**Infrastructure (Backend):**
- `uvicorn[standard]` 0.32.0 - ASGI server
- `python-multipart` 0.0.12 - File upload handling in FastAPI
- `python-dotenv` 1.0.1 - `.env` file loading
- `loguru` 0.7.3 - Listed in requirements (logging module uses stdlib `logging`, loguru may be used elsewhere)
- `alembic` 1.14.0 - Database schema migrations

**Server Requirements (alternative):**
- `backend/requirements.server.txt` lists relaxed version pins (`>=` instead of `==`)
- Adds `python-jose[cryptography]` and `passlib[bcrypt]` for server auth (not in main requirements)

## Configuration

**Environment:**
- `.env` file at project root (exists, contents not shown)
- `.env.example` at project root - documents all expected variables
- `frontend/.env.production` - production API URL override
- Configuration loaded via `pydantic-settings` `BaseSettings` in `backend/app/core/config.py`

**Key Configuration Variables:**
- `DATABASE_URL` - Database connection string (default: `sqlite:///./data/app.db`)
- `DEEPSEEK_API_KEY` - LLM fallback API key (optional)
- `DEEPSEEK_API_BASE_URL` - LLM endpoint (default: `https://api.deepseek.com/v1`)
- `UPLOAD_DIR`, `SAMPLES_DIR`, `TEMPLATES_DIR`, `OUTPUTS_DIR` - File storage paths
- `SALARY_TEMPLATE_PATH`, `FINAL_TOOL_TEMPLATE_PATH` - Export template file paths
- `AUTH_ENABLED` - Toggle authentication (default: `true`)
- `AUTH_SECRET_KEY` - HMAC signing key for tokens
- `VITE_API_BASE_URL` - Frontend API target (default: `http://127.0.0.1:8000/api/v1`)
- `MAX_UPLOAD_SIZE_MB` - Upload size limit (default: 25 MB)

**Build:**
- `frontend/tsconfig.json` - TypeScript strict mode, ES2020 target, Bundler module resolution
- `frontend/vite.config.ts` - Vite with React plugin, dev server on `127.0.0.1:5173`
- No `Dockerfile` or `docker-compose.yml` detected

**Build Commands:**
```bash
# Backend
uvicorn backend.app.main:app --reload

# Frontend
npm run dev          # Vite dev server
npm run build        # tsc + vite build
npm run lint         # ESLint
```

## Platform Requirements

**Development:**
- Python 3.10+ (type syntax requirements)
- Node.js 18+ (Vite 6.x requirement)
- Windows development environment (`.cmd`, `.ps1` startup scripts present)
- SQLite (default, zero-config database)

**Production:**
- Uvicorn ASGI server
- SQLite or PostgreSQL (`.env.example` shows PostgreSQL connection string)
- File system access for uploads, templates, and export outputs
- Optional: DeepSeek API access for LLM header mapping fallback

---

*Stack analysis: 2026-03-27*
