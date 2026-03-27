# Phase 5: supported-deployment-guardrails - Research

**Researched:** 2026-03-27
**Domain:** deployment configuration contract and startup guardrail activation
**Confidence:** HIGH

<user_constraints>
## User Constraints

- No `*-CONTEXT.md` file exists for Phase 5.
- Locked scope from the request: repair the documented deployment env contract so the supported deployment workflow actually activates the non-local security guardrails implemented in Phase 1.
- This phase must address `SEC-01`, `SEC-02`, and `OPS-01`.
- Research must focus on:
  - the exact drift between operator docs and backend config/runtime guardrails
  - the minimal implementation slices needed to fix supported deployment docs and any code/config seams
  - a verification strategy strong enough to close the audit gap, not just patch docs
  - canonical file references the planner/executor must treat as source of truth
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SEC-01 | The supported deployment path must require the actual non-local admin and HR password settings contract so operators cannot reach production-like deployments with default credentials through the documented path. | Use the real `admin_login_password` / `hr_login_password` contract from `backend/app/core/config.py`, expose it in `.env.example` and `DEPLOYMENT.md`, and verify env-driven bootstrap rejection. |
| SEC-02 | The supported deployment path must require the actual non-local auth secret settings contract so operators cannot reach production-like deployments with a predictable signing secret through the documented path. | Keep `AUTH_SECRET_KEY` as the documented secret key, add `RUNTIME_ENVIRONMENT` to force non-local mode, and verify bootstrap fails when the secret is unsafe. |
| OPS-01 | The repository must document one canonical deployment path whose environment contract actually wires into the implemented non-local guardrails. | Treat `backend/app/core/config.py` + `backend/app/bootstrap.py` as executable truth, then align `.env.example`, `DEPLOYMENT.md`, and `OPERATIONS.md` to that contract with regression coverage. |
</phase_requirements>

## Summary

Phase 1 already implemented the real guardrails: non-local startup is blocked when `admin_login_password`, `hr_login_password`, or `auth_secret_key` remain unsafe, and that validation runs from both the app lifespan and `backend.run` startup path. The audit gap is not missing security logic. It is a broken deployment contract: the supported docs tell operators to set `ADMIN_PASSWORD` and `HR_PASSWORD`, but the app only reads `ADMIN_LOGIN_PASSWORD` and `HR_LOGIN_PASSWORD`, and the supported deployment path never requires `RUNTIME_ENVIRONMENT`, so the guardrail can stay in local mode.

The strongest minimal fix is not a new auth feature. It is contract alignment plus executable regression coverage. Update the operator-facing contract surfaces that people actually copy (`.env.example`, `DEPLOYMENT.md`, and the deployment pointer in `OPERATIONS.md`) so they use the same names as `Settings`, then add tests that prove the documented env keys activate the existing bootstrap guardrails. Current tests only prove Python-level startup behavior when `Settings(...)` is constructed directly; they do not prove that the supported env contract is wired correctly.

**Primary recommendation:** Keep the runtime guardrail code as-is, repair the documented env contract to the canonical setting names, require `RUNTIME_ENVIRONMENT` in the supported deployment path, and add env-contract regression tests so future doc drift fails automatically.

## Standard Stack

### Core

| Library / Surface | Version | Purpose | Why Standard |
|-------------------|---------|---------|--------------|
| FastAPI | 0.115.0 | App startup path and lifespan hook | The real app startup already runs through `create_lifespan()` and `backend.run`, so Phase 5 should verify that existing path instead of adding a parallel deploy bootstrap. |
| Pydantic | 2.10.3 | Settings model fields/defaults | The executable env contract lives in `Settings`; planner should treat field names here as canonical. |
| pydantic-settings | 2.6.1 | `.env` and process env loading | This is the existing mechanism that maps env vars into `Settings`; use it directly instead of custom parsing. |
| pytest | 8.3.4 | Regression coverage | Needed to prove env-driven startup behavior and catch future doc/config drift. |

### Supporting

| Library / Surface | Version | Purpose | When to Use |
|-------------------|---------|---------|-------------|
| `systemd` service env file | host-managed | Loads `/opt/execl_mix/.env` for the supported deploy path | Use as the documented deployment carrier for the canonical env contract; no repo-side alternative should be promoted. |
| `.env.example` | repo template | Copy source for supported deployments | Treat as the operator-facing template that must mirror `Settings`; if it drifts, supported deployment drifts. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fix docs/template + add tests | Add backwards-compat aliases for `ADMIN_PASSWORD` / `HR_PASSWORD` | Alias support may reduce immediate operator pain, but it preserves two contracts. Use only if active deployments already rely on the broken names. |
| Use `Settings` + `bootstrap_application()` as canonical contract | Add a custom deploy-time validation script | A second validation path will drift again; the app already has the correct enforcement point. |

**Installation:**

```bash
pip install -r backend/requirements.txt
```

**Version verification:** Verified from the local virtualenv on 2026-03-27: `fastapi=0.115.0`, `pydantic=2.10.3`, `pydantic-settings=2.6.1`, `pytest=8.3.4`.

## Architecture Patterns

### Recommended Project Structure

```text
repo root
+-- .env.example                    # operator-facing env template
+-- DEPLOYMENT.md                   # canonical deployment checklist
+-- OPERATIONS.md                   # canonical operator handoff to deployment
+-- backend/app/core/config.py      # executable settings contract
+-- backend/app/bootstrap.py        # executable non-local guardrail enforcement
+-- backend/app/main.py             # lifespan startup path
+-- backend/run.py                  # backend entrypoint used by deployment docs
`-- backend/tests/                  # contract and startup regressions
```

### Pattern 1: Executable Settings Contract First

**What:** Treat `backend/app/core/config.py` as the only canonical source for env variable names, defaults, and runtime mode semantics.

**When to use:** For every operator-facing env variable, deployment checklist entry, `.env.example` key, and test assertion in this phase.

**Example:**

```python
# Source: backend/app/core/config.py
class Settings(BaseSettings):
    runtime_environment: str = 'local'
    auth_secret_key: str = DEFAULT_AUTH_SECRET_KEY
    admin_login_password: str = DEFAULT_ADMIN_LOGIN_PASSWORD
    hr_login_password: str = DEFAULT_HR_LOGIN_PASSWORD
```

### Pattern 2: Single Startup Enforcement Path

**What:** Keep guardrail enforcement in `bootstrap_application()` and verify the supported deployment path enters through that function.

**When to use:** When deciding whether Phase 5 needs runtime code changes. The current call path already exists; the gap is contract wiring and regression coverage.

**Example:**

```python
# Source: backend/app/bootstrap.py and backend/run.py
def bootstrap_application(settings: Optional[Settings] = None) -> Settings:
    runtime_settings = settings or get_settings()
    validate_auth_runtime_guardrails(runtime_settings)
    configure_logging(runtime_settings)
    ensure_runtime_directories(runtime_settings)
    return runtime_settings

def main() -> None:
    settings = bootstrap_application()
```

### Pattern 3: Env-Contract Regression Tests, Not Just Helper Tests

**What:** Add tests that load values through environment variables and assert the supported contract activates the existing guardrails.

**When to use:** To close the audit gap. Current tests construct `Settings(...)` directly and therefore cannot detect doc/template drift.

**Example:**

```python
# Recommended Phase 5 test pattern
def test_canonical_deployment_env_activates_non_local_guardrails(monkeypatch):
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_LOGIN_PASSWORD", "admin-pass")
    monkeypatch.setenv("HR_LOGIN_PASSWORD", "hr-pass")
    monkeypatch.setenv("AUTH_SECRET_KEY", "strong-secret")

    settings = Settings(_env_file=None)
    validated = validate_auth_runtime_guardrails(settings)

    assert validated.normalized_runtime_environment == "production"
```

### Anti-Patterns to Avoid

- **Docs-only fix:** Updating `DEPLOYMENT.md` without updating `.env.example` leaves the copy-first workflow broken.
- **Keyword-only verification:** Tests that pass safe values via `Settings(...)` kwargs do not prove the deployment env contract.
- **Two supported env contracts:** Supporting both `ADMIN_PASSWORD` and `ADMIN_LOGIN_PASSWORD` as first-class names weakens the canonical operator path unless there is explicit migration/deprecation handling.
- **Forgetting runtime mode:** Correct passwords and secret still do not trigger Phase 1 protection if `runtime_environment` stays `local`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Env contract parsing | Custom shell parsing or a second config reader | `Settings` in `backend/app/core/config.py` | The repo already has one config system; duplicating it guarantees drift. |
| Startup guardrail entrypoint | A new deploy-only preflight script | `bootstrap_application()` | Deployment already runs through `backend.run` and app lifespan bootstrap. |
| Doc drift detection | Manual checklist review only | `pytest` text assertions on `.env.example` and `DEPLOYMENT.md` | The current audit gap happened because prose drifted silently. |

**Key insight:** This phase should harden the contract boundary between docs, `.env`, and existing startup code. It should not redesign auth.

## Common Pitfalls

### Pitfall 1: Repairing `DEPLOYMENT.md` But Not `.env.example`

**What goes wrong:** Operators still copy an incomplete template that omits auth guardrail keys and `RUNTIME_ENVIRONMENT`.
**Why it happens:** The workflow begins with `cp .env.example .env`, but the audit focused on `DEPLOYMENT.md`.
**How to avoid:** Treat `.env.example` as a required part of the supported deployment contract and verify its keys in tests.
**Warning signs:** `DEPLOYMENT.md` mentions `ADMIN_LOGIN_PASSWORD` but `.env.example` still has no auth keys.

### Pitfall 2: Fixing Key Names But Leaving `runtime_environment` In Local Mode

**What goes wrong:** Startup succeeds with local semantics even though the environment looks production-like.
**Why it happens:** `runtime_environment` defaults to `local` in `Settings`, and the guardrail returns early for local runtime.
**How to avoid:** Require `RUNTIME_ENVIRONMENT=<non-local>` in the deployment contract and verify it in env-driven tests.
**Warning signs:** Bootstrap does not raise even when using default credentials because the runtime is still `local`.

### Pitfall 3: Proving The Wrong Thing In Tests

**What goes wrong:** The suite stays green while the deployment docs are still wrong.
**Why it happens:** Existing tests inject `Settings(...)` directly, bypassing env-name resolution.
**How to avoid:** Add at least one regression that reads from environment variables and one doc/template contract regression.
**Warning signs:** Test coverage mentions startup rejection, but no test sets `ADMIN_LOGIN_PASSWORD`, `HR_LOGIN_PASSWORD`, or `RUNTIME_ENVIRONMENT` via env.

### Pitfall 4: Expanding Scope Into Auth Or Deployment Redesign

**What goes wrong:** Phase 5 turns into a role/auth overhaul or a new deployment architecture project.
**Why it happens:** The broken contract is easy to misread as missing security features.
**How to avoid:** Keep the change surface limited to env contract alignment, minimal doc handoff updates, and regressions.
**Warning signs:** Plan tasks mention token model changes, reverse-proxy changes, or alternate deploy modes.

## Code Examples

Verified patterns from repository sources:

### Startup Guardrail Enforcement

```python
# Source: backend/app/bootstrap.py
def validate_auth_runtime_guardrails(settings: Optional[Settings] = None) -> Settings:
    runtime_settings = settings or get_settings()
    if not runtime_settings.auth_enabled or runtime_settings.is_local_runtime:
        return runtime_settings

    issues: list[str] = []
    if runtime_settings.uses_default_admin_password:
        issues.append('`admin_login_password` is still using the shipped default.')
    if runtime_settings.uses_default_hr_password:
        issues.append('`hr_login_password` is still using the shipped default.')
    if runtime_settings.uses_unsafe_auth_secret_key:
        issues.append('`auth_secret_key` is still using a default or blocked unsafe placeholder.')
```

### Supported Startup Call Path

```python
# Source: backend/app/main.py and backend/run.py
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = bootstrap_application(runtime_settings)
    app.state.settings = settings
    yield

def main() -> None:
    settings = bootstrap_application()
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
```

### Recommended Doc-Contract Regression

```python
# Recommended Phase 5 test pattern
def test_supported_deployment_docs_use_canonical_guardrail_env_names():
    deployment_doc = Path("DEPLOYMENT.md").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    for required in [
        "RUNTIME_ENVIRONMENT",
        "ADMIN_LOGIN_PASSWORD",
        "HR_LOGIN_PASSWORD",
        "AUTH_SECRET_KEY",
    ]:
        assert required in deployment_doc
        assert required in env_example

    for deprecated in ["ADMIN_PASSWORD", "HR_PASSWORD"]:
        assert deprecated not in deployment_doc
```

## State Of The Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Treat deployment prose as sufficient evidence | Make docs mirror executable settings and test the contract | Recommended for Phase 5 | Prevents another audit gap caused by silent doc drift |
| Validate startup only with direct `Settings(...)` kwargs | Validate both env loading and startup rejection | Recommended for Phase 5 | Proves the supported operator path, not just Python helper behavior |
| Omit runtime mode from deployment contract | Require non-local `RUNTIME_ENVIRONMENT` | Needed because Phase 1 uses local-mode bypass | Ensures Phase 1 guardrails actually engage on supported deployments |

**Deprecated/outdated:**

- `ADMIN_PASSWORD` and `HR_PASSWORD` as supported deployment env keys.
- Any supported deployment checklist that omits `RUNTIME_ENVIRONMENT`.

## Open Questions

1. **Do any live supported deployments already rely on the broken `ADMIN_PASSWORD` / `HR_PASSWORD` names?**
   - What we know: direct runtime verification on 2026-03-27 showed `ADMIN_PASSWORD` and `HR_PASSWORD` do not populate `Settings`, while `ADMIN_LOGIN_PASSWORD` and `HR_LOGIN_PASSWORD` do.
   - What's unclear: whether an existing operator copied the old docs into a real `.env`.
   - Recommendation: plan for docs/template correction first; add temporary alias support only if operator inventory confirms an active deployment depends on the broken names.

2. **Should `.env.example` keep its PostgreSQL example or match the deployment doc's SQLite example?**
   - What we know: `.env.example` currently uses a PostgreSQL `DATABASE_URL`, while `DEPLOYMENT.md` shows SQLite for the supported deploy path.
   - What's unclear: which storage example the team wants as the canonical supported deployment baseline.
   - Recommendation: make one explicit choice while editing `.env.example`, but do not let this expand the phase beyond the guardrail contract unless the inconsistency blocks operator clarity.

## Sources

### Primary (HIGH confidence)

- Repository source: `backend/app/core/config.py` - verified canonical setting names, defaults, and local-mode default.
- Repository source: `backend/app/bootstrap.py` - verified non-local guardrail enforcement and actionable failure message.
- Repository source: `backend/app/main.py` - verified app lifespan startup calls `bootstrap_application()`.
- Repository source: `backend/run.py` - verified supported deployment entrypoint also calls `bootstrap_application()`.
- Repository source: `DEPLOYMENT.md` - verified supported deployment currently documents `ADMIN_PASSWORD` / `HR_PASSWORD` and omits `RUNTIME_ENVIRONMENT`.
- Repository source: `OPERATIONS.md` - verified this is the canonical operator handoff to `DEPLOYMENT.md`.
- Repository source: `.env.example` - verified the copy-first env template omits auth guardrail keys and `RUNTIME_ENVIRONMENT`.
- Repository source: `backend/tests/test_runtime_config.py`, `backend/tests/test_app_initialization.py`, `backend/tests/test_auth_api.py` - verified current regression coverage does not test the supported env contract.
- Local runtime experiment on 2026-03-27 via `.venv\Scripts\python.exe` - verified `ADMIN_PASSWORD` / `HR_PASSWORD` do not bind to `Settings`, while `AUTH_SECRET_KEY`, `RUNTIME_ENVIRONMENT`, `ADMIN_LOGIN_PASSWORD`, and `HR_LOGIN_PASSWORD` do.
- Local test run on 2026-03-27: `.venv\Scripts\python.exe -m pytest backend/tests/test_runtime_config.py backend/tests/test_app_initialization.py backend/tests/test_auth_api.py -x` - passed 25 tests, confirming current startup guardrails work when settings are supplied correctly.

### Secondary (MEDIUM confidence)

- `.planning/v1.0-MILESTONE-AUDIT.md` - verified the audit's requirement and integration findings match the current repo state.
- `.planning/phases/01-deployment-security-guardrails/01-01-PLAN.md` and `01-01-SUMMARY.md` - verified Phase 1 intended executable startup enforcement, not documentation-only hardening.
- `.planning/phases/04-supported-operations-path/04-01-PLAN.md` and `04-01-SUMMARY.md` - verified Phase 4 promoted the supported deployment path but carried the wrong env names into docs.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - based on the active local environment and current repo dependency manifests.
- Architecture: HIGH - based on direct inspection of executable startup code and supported operator docs.
- Pitfalls: HIGH - based on the exact audit finding, direct env-loading verification, and current test coverage gaps.

**Research date:** 2026-03-27
**Valid until:** 2026-04-26
