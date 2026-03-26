# Planning Guide

`.planning/` is the in-repo source of truth for project intent, roadmap state, active plans, and execution summaries.

Start here when you need to understand what is complete, what is in progress, and what the next supported GSD step should be.

## Primary Files

- [PROJECT.md](./PROJECT.md): project scope, constraints, active hardening work, and validated requirements
- [ROADMAP.md](./ROADMAP.md): phase list, plan counts, and milestone progress
- [STATE.md](./STATE.md): current focus, recent decisions, blockers, and the current handoff

## Phase Directories

Each directory under `.planning/phases/` contains the artifacts for one phase:

- `*-RESEARCH.md`: background, constraints, and recommended shape
- `*-PLAN.md`: the exact discuss -> plan -> execute contract for the current step
- `*-SUMMARY.md`: what was completed, how it was verified, and what changed

For the current operations hardening work, start in `phases/04-supported-operations-path/`.

## Standard Workflow

Future work should follow the same loop every time:

1. `discuss`: confirm the next requirement or gap from `STATE.md`, `PROJECT.md`, and the active phase context
2. `plan`: create or review the phase plan that owns the files you intend to change
3. `execute`: implement only the plan-owned work, verify it, and commit task-by-task
4. `verify`: confirm the plan outcome, update summary/state artifacts, and capture remaining risks

## Recommended Entry Sequence

1. Read `STATE.md` to see the current position and next recommended step.
2. Read `ROADMAP.md` to understand where the current phase sits in the milestone.
3. Read the active `*-PLAN.md` before making plan-owned changes.
4. Read the most recent `*-SUMMARY.md` so you do not redo completed work.

If the repo also exposes operator docs, use `OPERATIONS.md` for supported workflows and `OPERATIONS_RESCUE.md` only when intentionally inspecting rescue tooling.
