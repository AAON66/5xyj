# Social Security Spreadsheet Aggregation Tool

This repository contains the brownfield React + FastAPI application used to ingest regional social security and housing fund workbooks, normalize them into canonical fields, validate and match records, and export both required downstream templates.

## Quick Start

Read [OPERATIONS.md](./OPERATIONS.md) first. It is the single supported operator guide for this repository.

- Supported local entrypoint: `start_project_local.cmd` or `start_project_local.ps1`
- Supported deployment path: the Linux `systemd` workflow documented in [DEPLOYMENT.md](./DEPLOYMENT.md)
- Planning and handoff docs for future agents and maintainers live in [.planning/README.md](./.planning/README.md)

Do not treat `deploy_all.sh`, `start_service.py`, or other historical deploy/fix scripts as normal startup instructions. They are not the supported local workflow.

## Supported Product Scope

The application already supports:

- Batch import of heterogeneous Excel workbooks from multiple regions
- Rules-first sheet discovery, header recognition, and canonical field mapping
- Non-detail-row filtering, validation, and employee matching
- Dual-template export that must produce both required output workbooks together
- Dashboard and review pages for import, validation, match, and export status

## Local Services

The canonical local launcher opens the same two services the app uses today:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

`OPERATIONS.md` documents the wrapper scripts and the exact backend/frontend commands they run so operators do not need to guess between helper scripts and direct commands.

## Additional Context

- Architecture reference: [architecture.md](./architecture.md)
- Supported deployment checklist: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Current phase planning state: [.planning/README.md](./.planning/README.md)
