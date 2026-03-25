# Concerns

**Analysis Date:** 2026-03-25

## Highest-Risk Issues

**Default authentication secrets and passwords are production-dangerous.**
- `backend/app/core/config.py` ships with `auth_secret_key = 'change-this-auth-secret'`.
- The same file also ships default credentials for both roles: `admin_login_password = 'admin123'` and `hr_login_password = 'hr123'`.
- If `.env` is missing, incomplete, or ignored during deployment, the app still starts with valid login credentials and a predictable signing secret.
- `backend/app/core/auth.py` uses these values directly for HMAC token signing and password comparison, so weak defaults are not merely placeholders; they are active runtime behavior.

**Upload size enforcement is only header-based.**
- `backend/app/core/upload_guard.py` rejects large uploads only when the request includes a trustworthy `content-length`.
- `backend/app/services/import_service.py` streams file content in `_store_upload()` but does not stop writing once the accumulated size exceeds `settings.max_upload_size_bytes`.
- A client that omits or lies about `content-length` can bypass the middleware check and still send a large file.
- For a spreadsheet ingestion service, this is an avoidable resource-exhaustion risk.

**Browser session handling is simple but exposed to XSS impact.**
- `frontend/src/services/authSession.ts` stores the bearer token in `window.sessionStorage`.
- `frontend/src/services/api.ts` automatically attaches that token to every API request.
- This is operationally convenient, but any future XSS bug in `frontend/src/pages/*.tsx` or `frontend/src/components/*.tsx` exposes active credentials immediately.
- There is no evidence of a stricter cookie-based session mode or token rotation path.

## Functional Fragility

**The export module contains duplicate helper definitions.**
- `backend/app/exporters/template_exporter.py` defines `_has_explicit_housing_amount_key()` twice.
- The second definition overrides the first one silently at import time.
- This is not an immediate runtime crash, but it is a clear maintenance hazard because later edits can target the wrong implementation and produce confusing behavior changes.

**Exporter burden logic looks intentionally stubbed and should be treated as debt until proven otherwise.**
- `backend/app/exporters/template_exporter.py` computes `personal_social_burden` and `personal_housing_burden` through `_resolved_personal_social_burden()` and `_resolved_personal_housing_burden()`.
- Both helpers currently return `Decimal('0')` unconditionally.
- The surrounding code still builds source contexts and candidate baselines, which suggests the burden-calculation path was designed for richer behavior than what is currently enabled.
- Tests currently lock in the zero behavior, so this is probably deliberate for now, but it remains a high-confusion area for future changes.

**Employee matching is intentionally narrow and may create workflow bottlenecks on real-world dirty data.**
- `backend/app/services/matching_service.py` matches by exact normalized ID number first, then exact `person_name + company_name`, then exact `person_name`.
- There is no fuzzy company alias handling, typo tolerance, transliteration handling, or similarity scoring for near matches.
- That keeps false positives low, but it also means slightly messy employee master data can produce many `unmatched`, `duplicate`, or `low_confidence` outcomes that require manual cleanup.

**Import parsing partially persists work file by file.**
- `backend/app/services/import_service.py` parses source files concurrently with `ThreadPoolExecutor`.
- Parsed results are committed per file in `_persist_analyzed_source_file()`, then the batch status is advanced only after the full loop completes.
- If a later file fails, the batch ends as `failed`, but earlier source-file mappings and preview state may already be stored, which can make failure recovery and re-run logic harder to reason about.

## Testing and Verification Gaps

**Export regression tests depend on machine-local template locations.**
- `backend/tests/test_template_exporter.py` searches for templates under `Path.home() / 'Desktop' / '202602社保公积金台账' / '202602社保公积金汇总'`.
- The same file uses `pytest.skip(...)` when templates or sample files are missing.
- That means one of the most critical requirements in this project, dual-template export, can be absent in CI or on another developer machine without turning the suite red.

**Frontend has no project-level automated tests.**
- `frontend/package.json` exposes `build`, `lint`, and `preview`, but no test script.
- No app tests were found under `frontend/src/`; the only `*.test.*` or `*.spec.*` files detected were inside `frontend/node_modules/`, not project code.
- The UI surface is now large enough (`frontend/src/pages/*.tsx`, `frontend/src/components/*.tsx`, auth/session flows, aggregate workflow pages) that this is a meaningful regression risk.

**The codebase relies heavily on integration-style confidence and much less on static analysis.**
- Frontend linting exists in `frontend/eslint.config.js`.
- No backend formatter, lint, or type-check command was detected for `backend/app/`.
- The backend is non-trivial now: parsing, normalization, matching, exporting, and auth all live in Python modules, so the absence of a lightweight backend static gate raises the chance of logic drift and unused/dead helpers surviving unnoticed.

## Operational and Maintenance Concerns

**The repository root has accumulated many one-off deployment and recovery scripts.**
- Examples include `deploy_complete.py`, `final_deploy_clean.py`, `fix_nginx.py`, `upload_fixed.py`, `restart_clean.py`, and several similarly named helpers in the repo root.
- These scripts may be useful operationally, but the volume and naming overlap make it hard to tell which paths are canonical.
- New contributors will likely need extra guidance to distinguish supported workflows from ad hoc recovery tools.

**Live integration dependencies still sit partly outside the repository boundary.**
- Real export templates are expected from desktop paths or environment-configured absolute paths via `backend/app/core/config.py`.
- DeepSeek support is wired in `backend/app/services/llm_mapping_service.py`, but live behavior depends on an external API key and external network availability.
- The project is functional without DeepSeek, but some verification paths remain environment-specific rather than fully self-contained.

## What To Watch Next

**Short-term hardening priorities:**
- Replace default auth credentials/secrets with fail-fast startup validation in `backend/app/core/config.py`.
- Enforce upload size during streaming inside `_store_upload()` in `backend/app/services/import_service.py`, not only in middleware.
- Remove the duplicate `_has_explicit_housing_amount_key()` implementation in `backend/app/exporters/template_exporter.py`.
- Convert template-export verification from skip-based local checks to repo-controlled fixtures or an explicit CI contract.
- Add at least one frontend test harness around auth restoration and the aggregate/import/export happy path.
