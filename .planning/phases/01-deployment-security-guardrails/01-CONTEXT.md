# Phase 1: Deployment Security Guardrails - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning
**Source:** Auto-created from roadmap, codebase map, and existing repo constraints

<domain>
## Phase Boundary

This phase is only about preventing unsafe authenticated deployments outside local development. It does not redesign authentication, change user roles, or expand product surface. The target outcome is startup/runtime guardrails that block default credentials and predictable signing secrets in non-local environments while keeping local development practical.

</domain>

<decisions>
## Implementation Decisions

### Locked Decisions

- Keep the current authentication model and role split (`admin`, `hr`) intact for this phase.
- Preserve the existing React + FastAPI architecture; this phase is backend/config hardening, not a stack change.
- Do not change the project rule that local development must stay usable for agents and developers.
- Non-local environments must fail fast when auth passwords or signing secrets are still default or obviously unsafe.
- The phase must be verified with automated tests, not only manual reasoning.
- `AGENTS.md` must remain unchanged during this phase.

### the agent's Discretion

- How to detect "local" versus "non-local" runtime, as long as the rule is explicit and testable.
- Whether the guardrail lives in config validation, bootstrap startup checks, or a small dedicated security validator module.
- Exact error messaging and exception types, as long as failure is actionable and deterministic.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Auth and runtime configuration
- `backend/app/core/config.py` - current auth defaults, runtime settings, and computed config behavior
- `backend/app/core/auth.py` - token issuance and password comparison behavior
- `backend/app/dependencies.py` - auth enable/disable behavior and default local-dev authenticated user
- `backend/app/main.py` - application startup and where fail-fast startup validation can be anchored
- `backend/app/bootstrap.py` - runtime bootstrap hook if startup validation belongs there

### Existing tests and API behavior
- `backend/tests/test_auth_api.py` - current login/auth expectations
- `backend/tests/test_app_initialization.py` - startup behavior coverage
- `backend/tests/test_runtime_config.py` - settings/config validation coverage

### Project constraints
- `.planning/PROJECT.md` - active scope and locked brownfield decisions
- `.planning/REQUIREMENTS.md` - `SEC-01`, `SEC-02`
- `.planning/ROADMAP.md` - phase goal and success criteria
- `.planning/codebase/CONCERNS.md` - rationale for prioritizing auth hardening first

</canonical_refs>

<specifics>
## Specific Ideas

- Current defaults in `backend/app/core/config.py` are `auth_secret_key = 'change-this-auth-secret'`, `admin_login_password = 'admin123'`, and `hr_login_password = 'hr123'`.
- The safest likely path is a startup validation guard that only tolerates these defaults in explicit local-development mode.
- Tests should prove both failure in non-local mode and continued operability in local mode.

</specifics>

<deferred>
## Deferred Ideas

- Session storage / XSS exposure on the frontend is deferred to a later security phase.
- Broader auth redesign, token rotation, or cookie-based auth is deferred.
- Upload hardening belongs to Phase 2, not this phase.

</deferred>

---
*Phase: 01-deployment-security-guardrails*
*Context gathered: 2026-03-26 via auto planning bootstrap*
