# Supported Operations

This document is the canonical operator contract for this repository. It defines one supported local workflow and one supported deployment workflow without changing the existing runtime behavior.

## Supported Local Workflow

Use exactly one local entrypoint:

- `start_project_local.cmd`
- `start_project_local.ps1`

These wrappers open the backend and frontend local starter scripts in separate terminals. They are the supported way to run the system locally.

### What The Local Wrapper Does

The wrapper scripts orchestrate the current brownfield startup flow:

1. Backend migration and startup via `start_backend_local.cmd` or `start_backend_local.ps1`
2. Frontend Vite startup via `start_frontend_local.cmd` or `start_frontend_local.ps1`

The backend wrapper does this today:

```powershell
$env:DATABASE_URL = "sqlite:///./data/app.db"
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\.venv\Scripts\python.exe -m backend.run
```

The frontend wrapper does this today:

```powershell
Set-Location frontend
cmd /c npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

The runtime endpoints remain:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

`backend/run.py` is the current backend entrypoint and binds Uvicorn to `127.0.0.1:8000`. The supported local workflow documents that behavior rather than redefining it.

### Local Prerequisites

- Python virtual environment available at `.venv`
- Backend dependencies installed from `backend/requirements.txt`
- Frontend dependencies installed under `frontend/node_modules` or installable by the frontend wrapper
- Repository-root `.env` configured for local use when needed

### Unsupported Local Shortcuts

Do not use these as the normal local startup path:

- `deploy_all.sh`
- `start_service.py`
- server-specific deploy or restart helpers
- rescue or fix scripts in the repository root

Those files may exist for historical recovery work, but they are not the supported workflow for day-to-day operation.

## Supported Deployment Workflow

The only supported deployment workflow is the Linux virtualenv + frontend build + `systemd` path documented in [DEPLOYMENT.md](./DEPLOYMENT.md).

Use that checklist when you need to provision or redeploy a supported environment. It aligns with the current application entrypoint, Phase 1 credential hardening, and Phase 3 template-path hardening.

## Operator Handoff

For roadmap, plan, and status context, start in [.planning/README.md](./.planning/README.md). That file points future maintainers and agents to `ROADMAP.md`, `STATE.md`, and the active phase artifacts inside `.planning/`.
