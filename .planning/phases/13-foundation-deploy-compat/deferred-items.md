## Phase 13 Plan 01 deferred items

- `backend/tests/test_auth_api.py::test_login_endpoint_returns_bearer_token_for_admin` fails with 401 because the seeded admin has an existing DB password that doesn't match `admin-pass`. Pre-existing failure (verified by stashing Plan 13-01 changes and reproducing). Out of scope for slots=True cleanup.

## Phase 13 Plan 03 deferred items

- Same pre-existing login-related test failures re-confirmed under Plan 13-03 (verified by `git stash && pytest` reproducing 401). Additionally affects `test_login_endpoint_rejects_invalid_credentials` and `test_me_endpoint_returns_authenticated_user_profile` because they all hit the same seeded admin DB. Fix requires resetting `.test_artifacts/auth_api/` between runs or changing the admin-seed strategy so `admin_login_password` is the source of truth.
