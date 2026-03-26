---
phase: 04-supported-operations-path
plan: 01
subsystem: infra
tags: [operations, docs, systemd, uvicorn, vite]
requires:
  - phase: 03-reproducible-export-verification
    provides: repo-controlled template paths and explicit export configuration expectations
provides:
  - canonical supported local workflow documentation centered on start_project_local
  - canonical supported Linux/systemd deployment checklist
  - top-level handoff into .planning for future maintainers and agents
affects: [operations, deployment, docs, planning]
tech-stack:
  added: []
  patterns:
    - document one supported local entrypoint before listing helper details
    - document one supported deployment path and demote rescue tooling to historical references
key-files:
  created: [OPERATIONS.md, .planning/README.md]
  modified: [README.md, DEPLOYMENT.md]
key-decisions:
  - "Promoted start_project_local.cmd and start_project_local.ps1 as the single supported local entrypoint because they already match the current backend/frontend runtime behavior."
  - "Promoted the Linux virtualenv plus frontend build plus systemd flow as the only supported deployment path and demoted rescue/server-specific materials to historical references."
patterns-established:
  - "Operator docs now point to OPERATIONS.md first, then to DEPLOYMENT.md for supported deployment details."
  - "Top-level docs now point maintainers into .planning/README.md for roadmap, state, and phase handoff."
requirements-completed: [OPS-01]
duration: 3 min
completed: 2026-03-26
---

# Phase 4 Plan 1: Supported Operations Path Summary

**Canonical local startup now centers on start_project_local wrappers, and supported deployment is narrowed to one Linux systemd checklist with explicit auth and template-path requirements**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T07:29:03Z
- **Completed:** 2026-03-26T07:32:25Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `OPERATIONS.md` as the single supported operator contract for local and deployment workflows.
- Rewrote `README.md` so quick start points to `OPERATIONS.md`, names `start_project_local.*` as the supported local entrypoint, and stops presenting rescue scripts as normal startup choices.
- Added `.planning/README.md` so top-level docs now expose the roadmap and planning handoff surface.
- Rewrote `DEPLOYMENT.md` around one Linux virtualenv plus frontend build plus `systemd` deployment checklist with explicit `AUTH_SECRET_KEY`, `ADMIN_PASSWORD`, `HR_PASSWORD`, `SALARY_TEMPLATE_PATH`, and `FINAL_TOOL_TEMPLATE_PATH` guidance.

## Verification

- Passed: `Select-String -Path README.md,OPERATIONS.md -Pattern 'start_project_local|127.0.0.1:8000|127.0.0.1:5173'`
- Passed: `Select-String -Path DEPLOYMENT.md,OPERATIONS.md -Pattern 'systemd|AUTH_SECRET_KEY|SALARY_TEMPLATE_PATH|FINAL_TOOL_TEMPLATE_PATH'`
- Passed: `Select-String -Path README.md,OPERATIONS.md,DEPLOYMENT.md -Pattern 'deploy_all.sh|start_service.py|10.0.0.60'`
  Result: all matched occurrences are explicitly demoted as unsupported or historical references, not presented as the supported path.

## Task Commits

Each task was committed atomically:

1. **Task 1: Publish the canonical supported local workflow** - `07d02c4` (`docs`)
2. **Task 2: Narrow deployment guidance to one supported workflow** - `53f8255` (`docs`)

## Files Created/Modified

- `OPERATIONS.md` - Canonical supported local/deployment operations contract.
- `README.md` - Quick-start handoff that points operators to `OPERATIONS.md`.
- `.planning/README.md` - Discoverable roadmap/state entrypoint for future maintainers and agents.
- `DEPLOYMENT.md` - Single supported Linux/systemd deployment checklist aligned with current runtime behavior.

## Decisions Made

- Chose `start_project_local.cmd` and `start_project_local.ps1` as the only supported local entrypoint because they already orchestrate the real backend and frontend local startup flow.
- Chose the Linux virtualenv plus frontend build plus `systemd` deployment flow as the single supported deployment workflow because it matches the current brownfield entrypoint without depending on workstation-only or server-specific helpers.
- Kept rescue and server-specific materials out of the supported lane by documenting them only as unsupported or historical references in this plan.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `rg` was not available in this PowerShell environment, so verification used `Select-String` with the same pattern checks.

## User Setup Required

None - no external service configuration required beyond the supported deployment environment variables already documented in `DEPLOYMENT.md`.

## Known Stubs

None.

## Next Phase Readiness

- The repository now has one explicit supported local path and one explicit supported deployment path for operators to follow.
- Phase `04-02` can build on this by classifying rescue and legacy scripts without having to redefine the canonical workflow again.

## Self-Check: PASSED

- Found `.planning/phases/04-supported-operations-path/04-01-SUMMARY.md`
- Found commit `07d02c4`
- Found commit `53f8255`

---
*Phase: 04-supported-operations-path*
*Completed: 2026-03-26*
