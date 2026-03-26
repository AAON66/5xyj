---
phase: 04-supported-operations-path
plan: 02
subsystem: infra
tags: [operations, docs, rescue, legacy, gsd]
requires:
  - phase: 04-supported-operations-path
    provides: canonical supported local and deployment workflows in OPERATIONS.md and DEPLOYMENT.md
provides:
  - rescue and legacy operations tooling moved out of the repo root into scripts/operations/rescue
  - server-specific deployment notes demoted behind the supported docs
  - explicit .planning handoff guidance for the discuss -> plan -> execute -> verify loop
affects: [operations, deployment, docs, planning]
tech-stack:
  added: []
  patterns:
    - relocate ad hoc operational helpers into a rescue-only filesystem surface instead of leaving them beside supported entrypoints
    - point future agents to .planning state and supported operator docs before any rescue tooling
key-files:
  created: [OPERATIONS_RESCUE.md, scripts/operations/rescue/README.md, .planning/phases/04-supported-operations-path/04-02-SUMMARY.md]
  modified: [DEPLOYMENT_SERVER.md, .planning/README.md, .planning/PROJECT.md, .planning/STATE.md, scripts/operations/rescue/]
key-decisions:
  - "Moved the full repo-root ad hoc operations script surface into scripts/operations/rescue so only start_*_local launchers remain at the root."
  - "Demoted DEPLOYMENT_SERVER.md to legacy server-specific notes that redirect normal operators back to OPERATIONS.md and DEPLOYMENT.md."
  - "Used .planning/README.md and STATE.md as the future-agent handoff surface instead of touching AGENTS.md."
patterns-established:
  - "Supported operator docs stay at the repo root; rescue and server-specific helpers live under scripts/operations/rescue."
  - "Future agents should orient from STATE.md, ROADMAP.md, and the active plan summary before reaching for rescue tooling."
requirements-completed: [OPS-02, OPS-03]
duration: 3 min
completed: 2026-03-26
---

# Phase 4 Plan 2: Supported Operations Path Summary

**Rescue and legacy operational scripts now live under `scripts/operations/rescue`, with server-specific deployment notes demoted and `.planning/` explicitly routing future work through the standard GSD loop**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T15:39:42+08:00
- **Completed:** 2026-03-26T15:42:07+08:00
- **Tasks:** 2
- **Files modified:** 49

## Accomplishments

- Moved every repo-root ad hoc deploy, restart, repair, upload, and server helper into `scripts/operations/rescue/`, leaving only `start_backend_local.*`, `start_frontend_local.*`, and `start_project_local.*` at the root.
- Added `OPERATIONS_RESCUE.md` and `scripts/operations/rescue/README.md` so the rescue surface is clearly labeled as non-canonical and points back to `OPERATIONS.md` and `DEPLOYMENT.md`.
- Updated `.planning/README.md`, `.planning/PROJECT.md`, and `.planning/STATE.md` so future agents can discover the roadmap/state files and follow discuss -> plan -> execute -> verify without touching `AGENTS.md`.

## Verification

- Passed: root launcher inventory check
  Command: `Get-ChildItem -Name *.py,*.sh,*.cmd,*.ps1 | Where-Object { ... }`
  Result: no rescue-pattern scripts remain at the repo root outside the six supported `start_*_local` launchers.
- Passed: rescue directory inventory check
  Command: `Get-ChildItem scripts/operations/rescue -Recurse -Name | Select-String -Pattern 'absolute_path_deploy|auto_deploy|check_service|clean_cache_deploy|clean_deploy|clean_env_start|deploy|final|fix_|force_rebuild|kill_and_restart|manual_start|rebuild_venv|redeploy|restart_clean|setup_nginx|simple_start|start_service|upload_'`
  Result: relocated rescue helpers are present under `scripts/operations/rescue/`.
- Passed: rescue/server-note terminology check
  Command: `Select-String -Path OPERATIONS_RESCUE.md,DEPLOYMENT_SERVER.md -Pattern 'legacy|server-specific|OPERATIONS.md|deploy_all.sh|start_service.py'`
  Result: both docs explicitly mark the old path as legacy or server-specific and redirect operators to `OPERATIONS.md`.
- Passed: `.planning/` handoff terminology check
  Command: `Select-String -Path .planning/README.md,.planning/PROJECT.md,.planning/STATE.md -Pattern 'PROJECT.md|ROADMAP.md|STATE.md|discuss|plan|execute|verify|OPERATIONS.md|OPERATIONS_RESCUE.md|rescue'`
  Result: the planning entrypoint, project scope, and state handoff all reference the supported docs and the standard workflow loop.
- Passed: `AGENTS.md` untouched
  Command: `git diff --name-only HEAD~2..HEAD -- AGENTS.md`
  Result: no output.

## Task Commits

Each task was committed atomically:

1. **Task 1: Classify rescue and legacy operational tooling** - `9e2b37a` (`chore`)
2. **Task 2: Add explicit .planning handoff guidance for future agents** - `fa800f9` (`docs`)

## Files Created/Modified

- `OPERATIONS_RESCUE.md` - Inventory of rescue, legacy, and server-specific operational helpers.
- `DEPLOYMENT_SERVER.md` - Demoted server-specific note that points normal operators back to the canonical docs.
- `scripts/operations/rescue/README.md` - On-disk warning banner for the relocated rescue tooling surface.
- `scripts/operations/rescue/` - New location for root-level ad hoc deploy, restart, repair, upload, and environment helpers.
- `.planning/README.md` - Discoverable planning entrypoint for roadmap, state, and workflow usage.
- `.planning/PROJECT.md` - Active hardening scope now references `OPERATIONS.md` and `OPERATIONS_RESCUE.md`.
- `.planning/STATE.md` - Resume notes steer future agents toward supported docs and the standard GSD loop.

## Decisions Made

- Moved the whole rescue-class script surface rather than only the explicitly named subset so the repo root no longer presents ambiguous operational entrypoints.
- Kept rescue scripts intact apart from relocation so provenance and old investigation paths remain available.
- Left `AGENTS.md` unchanged and made `.planning/` the discoverable handoff surface instead.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `rg` is not available in this PowerShell environment, so equivalent `Select-String` checks were used for verification.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Operators now have an obvious split between supported workflows and rescue-only tooling.
- Future agents can continue from `.planning/README.md`, `STATE.md`, and the active phase summaries without editing `AGENTS.md`.

## Self-Check: PASSED

- Found `.planning/phases/04-supported-operations-path/04-02-SUMMARY.md`
- Found commit `9e2b37a`
- Found commit `fa800f9`
