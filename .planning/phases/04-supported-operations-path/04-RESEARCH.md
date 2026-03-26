# Phase 4: Supported Operations Path - Research

**Researched:** 2026-03-26
**Domain:** Supported local/deployment workflow definition and rescue-tool separation for a React + FastAPI brownfield repo
**Confidence:** MEDIUM

## User Constraints

### Locked Inputs

- No `04-CONTEXT.md` exists for this phase. Planning must use `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and the repo's current docs/scripts as the source of truth.
- Treat the application as already functional enough for local import-to-export work; this phase is about operational clarity, not rewriting the app lifecycle.
- Preserve the current local startup behavior that already exists in `start_backend_local.*`, `start_frontend_local.*`, `start_project_local.*`, and `backend/run.py`.
- Preserve the current deployment hardening from Phase 1 and the export verification hardening from Phase 3.
- Phase goal: operators and future agents must be able to identify one supported local workflow and one supported deployment workflow without mistaking ad hoc scripts for the canonical path.
- Phase requirements: `OPS-01`, `OPS-02`, `OPS-03`.
- Success criteria:
  1. The repository documents one canonical local run path for the supported system workflow.
  2. The repository documents one canonical deployment path for the supported system workflow.
  3. One-off repair and deployment scripts are clearly marked or separated so operators can distinguish them from supported workflows.
  4. In-repo GSD planning state exists and points future work toward discuss, plan, execute, and verify flows.

### Claude's Discretion

- Choose whether the supported deployment path is the documented manual Linux/systemd flow or a different single path, as long as exactly one canonical deployment workflow is promoted.
- Choose whether rescue tooling is separated by directory move, explicit prefix, manifest, README, or a combination of those mechanisms.
- Choose whether Phase 4 should update `README.md`, `DEPLOYMENT.md`, `DEPLOYMENT_SERVER.md`, `progress.txt`, `.planning/STATE.md`, and/or add a new operator-facing doc, provided the supported path becomes unambiguous.

### Deferred Ideas

- Converting all deployment automation into a new packaging system is out of scope.
- Docker-first production standardization is out of scope unless the repo already clearly supports it as the single chosen path.
- Refactoring application startup internals is out of scope unless needed to make the documented supported workflow accurate.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPS-01 | The repository documents one canonical local run path and one canonical deployment path for the supported system workflow | Consolidate README + deployment docs around one local path and one Linux deployment path |
| OPS-02 | Ad hoc repair or one-off deployment scripts are clearly separated from supported operator workflows | Inventory and demote `deploy_*`, `final_*`, `fix_*`, `restart_*`, and credentialed remote scripts |
| OPS-03 | GSD planning state exists in-repo so future work can route cleanly into discuss, plan, execute, and verify phases | Keep `.planning/` authoritative and add clear operator/agent signposts into roadmap/state docs or README |

## Summary

The repo already contains a plausible supported local workflow, but it is buried among many one-off scripts and mixed deployment instructions. The strongest local path today is:

1. backend: `.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head` then `.\.venv\Scripts\python.exe -m backend.run`
2. frontend: `cd frontend && npm run dev -- --host 127.0.0.1 --port 5173`
3. convenience wrapper: `start_project_local.cmd` or `start_project_local.ps1`

Those entrypoints are consistent with `backend/run.py` and the current local helper scripts, so the phase should likely promote them rather than inventing a new local launcher.

Deployment is less clear. `DEPLOYMENT.md` documents several modes at once: Windows local development, Linux server deployment, Docker deployment, and Nginx setup. `DEPLOYMENT_SERVER.md` and multiple root-level shell/Python deploy helpers introduce a second, server-specific workflow oriented around `10.0.0.60`. Some of those helpers embed credentials or server assumptions directly in the repo, including:

- `deploy_all.sh` with hard-coded host/user/password variables
- `start_service.py` with hard-coded SSH credentials and restart commands

There are also many repair/recovery scripts in the repo root, including `final_deploy.py`, `final_fix.py`, `fix_*`, `restart_clean.py`, `kill_and_restart.py`, `upload_and_start.py`, and similar variants. Today, an operator or future agent has no reliable way to distinguish "supported workflow" from "historical rescue script".

**Primary recommendation:** make one documented local path and one documented Linux/systemd deployment path the only supported workflows, then explicitly demote the remaining ad hoc scripts into a clearly marked rescue/legacy surface.

## Evidence From Current Repo

### Supported Local Candidates

- `start_project_local.cmd` and `start_project_local.ps1` launch the backend and frontend local starter scripts in separate terminals.
- `start_backend_local.cmd` / `.ps1` set `DATABASE_URL=sqlite:///./data/app.db`, run Alembic migrations, and start `python -m backend.run`.
- `start_frontend_local.cmd` / `.ps1` install frontend dependencies if needed and run Vite on `127.0.0.1:5173`.
- `backend/run.py` binds the backend to `127.0.0.1:8000`, which aligns with a local-only supported path.

### Deployment Surface

- `DEPLOYMENT.md` already contains a Linux manual deployment sequence with virtualenv setup, dependency install, frontend build, and `systemd` service configuration.
- `DEPLOYMENT_SERVER.md` describes direct deployment to `10.0.0.60` and reads like environment-specific operational notes rather than a reusable supported path.
- `deploy.sh` / `deploy_service.sh` / `deploy_all.sh` appear to target a specific server workflow rather than a portable operator contract.

### Rescue / Legacy Surface

The repo root contains a large set of ad hoc scripts whose names strongly imply one-off or repair usage:

- `deploy_complete.py`, `deploy_auto.py`, `auto_deploy.py`, `auto_deploy.sh`, `final_deploy.py`, `final_deploy_clean.py`
- `fix_deploy.py`, `fix_nginx.py`, `fix_nginx_default.py`, `fix_server_files.py`, `fix_on_server.py`
- `restart_clean.py`, `kill_and_restart.py`, `manual_start.py`, `simple_start.py`, `upload_fixed.py`, `upload_and_start.py`
- `start_service.py`, which remotely restarts a service on a fixed host with embedded credentials

This script sprawl is the core OPS-02 problem. The phase should not pretend these scripts do not exist; it should separate or label them so they are visibly unsupported for standard operation.

## Recommended Structure

```text
README.md
DEPLOYMENT.md
DEPLOYMENT_SERVER.md            # optional legacy/server-specific notes, clearly demoted
scripts/
`-- operations/
    |-- supported/              # only canonical local/deploy entrypoints, if scripts are moved
    `-- rescue/                 # clearly marked one-off or server-specific tooling
.planning/
|-- ROADMAP.md
|-- STATE.md
`-- phases/04-supported-operations-path/
    |-- 04-RESEARCH.md
    |-- 04-01-PLAN.md
    `-- 04-02-PLAN.md
```

The exact directory move is discretionary. The important contract is that supported operator entrypoints are grouped and documented separately from rescue tooling.

## Architecture Patterns

### Pattern 1: One Canonical Local Path

**What:** Pick one local development flow and state it first everywhere.

**Recommended choice:** `start_project_local.*` as the convenience entrypoint, with direct backend/frontend commands documented beneath it.

**Why:** These scripts already line up with the actual backend/frontend runtime and avoid inventing a new wrapper.

### Pattern 2: One Canonical Deployment Path

**What:** Pick one production-like deployment flow and remove other modes from the "supported" lane.

**Recommended choice:** the manual Linux + virtualenv + frontend build + `systemd` path already described in `DEPLOYMENT.md`.

**Why:** It is the least environment-specific path in the repo and does not depend on baked-in server credentials.

### Pattern 3: Rescue Tools Are Visible but Demoted

**What:** Keep emergency scripts available, but force operators to see that they are legacy/rescue-only.

**Ways to implement:**

- move them under a `rescue/` or `legacy/` directory
- add a root-level manifest/README that classifies each script
- rename or wrap them so supported scripts and rescue scripts cannot be confused

### Pattern 4: `.planning/` Remains the Source of Truth for Future Agents

**What:** Ensure Phase 4 documentation points future work back into `.planning/ROADMAP.md`, `.planning/STATE.md`, and the discuss/plan/execute/verify flow.

**Why:** OPS-03 is mostly about discoverability now that the planning system already exists in-repo.

## Anti-Patterns To Avoid

- Promoting multiple deployment modes as equally supported.
- Leaving credentialed remote scripts in the same "quick start" lane as supported operator workflows.
- Deleting rescue scripts without replacing them with classification or provenance, because future operators may still need them for investigation.
- Creating a canonical workflow that does not match the actual startup commands in `backend/run.py` and the local starter scripts.
- Solving OPS-03 only inside `.planning/` while leaving top-level docs unaware of the in-repo planning flow.

## Common Pitfalls

### Pitfall 1: Documentation Cleanup Without Script Classification

**What goes wrong:** The docs become cleaner, but root-level script sprawl still misleads operators.

**How to avoid:** Pair doc cleanup with a concrete script inventory/classification step.

### Pitfall 2: "Supported Deployment" Still Depends on One Server

**What goes wrong:** The repo keeps pointing operators at `10.0.0.60`-specific helpers instead of a portable deployment contract.

**How to avoid:** Demote `DEPLOYMENT_SERVER.md` and any hard-coded remote scripts to rescue/server-specific notes.

### Pitfall 3: Future Agents Ignore `.planning/`

**What goes wrong:** The planning state exists, but nothing outside GSD points people to it.

**How to avoid:** Add one obvious handoff reference from top-level docs to `.planning/STATE.md` and the current phase flow.

## Plan Shape Recommendation

Phase 4 splits cleanly into two plans:

1. `04-01`: define and document the canonical supported local/deployment workflow, update README/deployment docs, and align startup entrypoint references with reality.
2. `04-02`: inventory and separate rescue/legacy scripts, add explicit unsupported labeling, and tighten `.planning/` / operator handoff guidance so future work routes into discuss/plan/execute/verify instead of ad hoc scripts.

That split keeps the user-facing supported path independent from the mechanical cleanup/classification of legacy operational tooling.
