# Phase 5: Repair Supported Deployment Guardrails - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning
**Source:** Auto-created from roadmap, v1.0 audit findings, and current supported deployment/auth files

<domain>
## Phase Boundary

This phase is about repairing the supported deployment contract so the documented non-local path actually triggers the Phase 1 startup guardrails already implemented in code. It is not an auth redesign, not a new deployment architecture, and not a general docs cleanup pass. The target outcome is a supported deployment path whose documented environment variables, runtime mode, and verification steps line up with the actual guardrail implementation and are proven by regression coverage.

</domain>

<decisions>
## Implementation Decisions

### Locked Decisions

- Keep the current React + FastAPI brownfield runtime and the existing Linux virtualenv + frontend build + `systemd` deployment path.
- Treat `backend/app/core/config.py` and `backend/app/bootstrap.py` as the source of truth for the guardrail contract, not the older env names written into operator docs.
- Phase 5 must close `SEC-01`, `SEC-02`, and `OPS-01` together; a docs-only fix that does not verify the supported runtime contract is insufficient.
- The supported deployment path must explicitly leave `runtime_environment='local'` and enter a non-local mode so guardrails are guaranteed to run.
- The plan must include automated verification for the supported contract, not only prose edits.
- `AGENTS.md` must remain unchanged during this phase.

### the agent's Discretion

- Whether to solve the env-name drift by changing docs only, expanding config aliases for backward compatibility, tightening `.env.example`, or a combination, as long as the supported contract is unambiguous and testable.
- Whether deployment verification lives in runtime-config tests, startup tests, a dedicated deployment-contract test, or a focused combination of those.
- Exact wording of operator docs and failure messages, as long as the documented path is concrete and maps to the implemented settings contract.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Guardrail source of truth
- `backend/app/core/config.py` - defines `runtime_environment`, `auth_secret_key`, `admin_login_password`, and `hr_login_password`
- `backend/app/bootstrap.py` - applies `validate_auth_runtime_guardrails()` during startup
- `backend/run.py` - canonical backend entrypoint used by the supported deployment path

### Operator contract and environment surface
- `DEPLOYMENT.md` - current supported deployment checklist containing the miswired env names
- `OPERATIONS.md` - top-level operator contract that points at the supported deployment path
- `.env.example` - repo-controlled environment contract that currently omits the Phase 1 auth guardrail fields

### Existing guardrail verification
- `backend/tests/test_runtime_config.py` - unit-level config and guardrail coverage
- `backend/tests/test_app_initialization.py` - startup-level coverage for non-local rejection and local allowance
- `backend/tests/test_auth_api.py` - successful authenticated behavior with safe non-local credentials

### Prior phase intent and audit evidence
- `.planning/v1.0-MILESTONE-AUDIT.md` - concrete evidence for why `SEC-01`, `SEC-02`, and `OPS-01` remain unsatisfied
- `.planning/phases/01-deployment-security-guardrails/01-01-PLAN.md` - original Phase 1 implementation contract
- `.planning/phases/01-deployment-security-guardrails/01-01-SUMMARY.md` - what Phase 1 actually shipped
- `.planning/phases/04-supported-operations-path/04-01-PLAN.md` - original supported deployment documentation contract
- `.planning/phases/04-supported-operations-path/04-01-SUMMARY.md` - what Phase 4 documented

### Milestone planning state
- `.planning/PROJECT.md` - current milestone intent and brownfield constraints
- `.planning/ROADMAP.md` - Phase 5 goal and dependencies
- `.planning/REQUIREMENTS.md` - active v1.1 requirement definitions and traceability
- `.planning/STATE.md` - current position and blocker summary

</canonical_refs>

<specifics>
## Specific Ideas

- `DEPLOYMENT.md` still instructs operators to set `ADMIN_PASSWORD` and `HR_PASSWORD`, but the shipped guardrail reads `admin_login_password` and `hr_login_password`.
- `DEPLOYMENT.md` currently documents `AUTH_SECRET_KEY`, which does match code, but it does not require `runtime_environment` to be non-local, so the guardrails can still be bypassed through the supported path.
- `.env.example` currently exposes `VITE_API_BASE_URL` and other runtime settings but does not surface `runtime_environment`, `admin_login_password`, `hr_login_password`, or `auth_secret_key`.
- Current tests already prove the guardrail logic in code; the missing piece is a supported deployment contract and verification that cover the exact documented path.

</specifics>

<deferred>
## Deferred Ideas

- Quick aggregate streaming fixes belong to Phase 6, not this phase.
- Backfilling Phase 1 and Phase 2 formal verification artifacts belongs to Phase 7.
- Broader auth redesign, credential rotation workflows, Docker deployment, and server-specific rescue tooling remain out of scope for Phase 5.

</deferred>

---
*Phase: 05-supported-deployment-guardrails*
*Context gathered: 2026-03-27 via audit-derived planning bootstrap*
