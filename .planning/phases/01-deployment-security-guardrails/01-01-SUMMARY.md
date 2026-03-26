# 01-01 Summary

## Outcome
- Added an explicit `runtime_environment` setting with a local default so startup security behavior is deterministic and testable.
- Added fail-fast auth startup guardrails in `bootstrap_application()` for non-local runtimes when default admin or HR passwords remain configured.
- Added fail-fast auth startup guardrails in `bootstrap_application()` for non-local runtimes when `auth_secret_key` is still the shipped default or another blocked unsafe placeholder.
- Preserved the current local-development behavior: `runtime_environment='local'` still allows the existing default credentials so developer and agent loops remain bootable.
- Preserved the supported authenticated login flow with explicit safe credentials in non-local test settings.

## Files Changed
- `backend/app/core/config.py`
- `backend/app/bootstrap.py`
- `backend/tests/test_runtime_config.py`
- `backend/tests/test_app_initialization.py`
- `backend/tests/test_auth_api.py`

## Verification
- Passed: `.\\.venv\\Scripts\\python.exe -m pytest backend/tests/test_runtime_config.py backend/tests/test_app_initialization.py backend/tests/test_auth_api.py -x`
- Passed: `cmd /c npm.cmd run build` in `frontend/`
- Lint status: `cmd /c npm.cmd run lint` in `frontend/` completed with one pre-existing warning in `frontend/src/pages/SimpleAggregate.tsx:396`

## Requirements Covered
- `SEC-01`: Non-local startup now rejects shipped default admin and HR passwords.
- `SEC-02`: Non-local startup now rejects the shipped default signing secret and explicitly blocked unsafe placeholders.

## Notes
- `main.py` did not require code changes because the existing lifespan path already calls `bootstrap_application()` before serving requests.
- Next recommended step: plan and execute Phase 2 (`Safe Upload Intake`).