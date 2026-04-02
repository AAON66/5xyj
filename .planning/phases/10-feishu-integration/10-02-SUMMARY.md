---
phase: 10-feishu-integration
plan: 02
subsystem: api
tags: [feishu, oauth, csrf, fastapi, ndjson, streaming, rbac]

# Dependency graph
requires:
  - phase: 10-feishu-integration plan 01
    provides: FeishuClient, SyncConfig/SyncJob models, sync service, schemas
provides:
  - Feishu sync API endpoints (push/pull with NDJSON streaming)
  - SyncConfig CRUD endpoints with admin RBAC
  - OAuth callback with CSRF state validation via signed cookies
  - Feature flags endpoint for frontend conditional rendering
  - FeishuOAuthService for code exchange and user binding
affects: [10-03, 10-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [HMAC-signed cookie CSRF for OAuth state, safe DI fallback for optional external clients, JSONResponse cookie manipulation]

key-files:
  created:
    - backend/app/api/v1/feishu_sync.py
    - backend/app/api/v1/feishu_settings.py
    - backend/app/api/v1/feishu_auth.py
    - backend/app/services/feishu_oauth_service.py
    - tests/test_feishu_auth.py
  modified:
    - backend/app/api/v1/router.py
    - backend/app/api/v1/system.py
    - backend/app/schemas/feishu.py

key-decisions:
  - "Used request.app.state.settings instead of Depends(get_settings) to honor test-injected Settings"
  - "Safe DI wrapper _get_client_safe() catches ValueError when Feishu credentials not configured"
  - "Cookie set directly on JSONResponse object (not Response parameter) for proper cookie propagation"
  - "SyncConfigRead/SyncJobRead accept Union[str, datetime] for cross-environment compatibility"

patterns-established:
  - "OAuth CSRF: HMAC-signed state in httpOnly cookie, verified on callback before code exchange"
  - "Feature flag guard: _check_sync_enabled() returns 404 error_response or None"
  - "Safe DI: _get_client_safe() wraps get_feishu_client() to return None instead of raising"

requirements-completed: [FEISHU-01, FEISHU-02, FEISHU-03, FEISHU-04, FEISHU-05]

# Metrics
duration: 10min
completed: 2026-04-02
---

# Phase 10 Plan 02: Feishu API Endpoints Summary

**Feishu sync/settings/OAuth API endpoints with NDJSON streaming, CSRF-protected OAuth state validation, and 18 comprehensive tests**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-01T23:48:19Z
- **Completed:** 2026-04-01T23:58:19Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- 3 new route modules: feishu_sync (push/pull/history/retry), feishu_settings (CRUD/credentials/flags), feishu_auth (OAuth with CSRF)
- OAuth callback validates state via HMAC-signed httpOnly cookie before code exchange (H2 security)
- All endpoints return 404 when feature flags disabled; credentials are env-var only (M3)
- 18 new tests covering OAuth state, user creation, CRUD, pagination, RBAC, and feature flags

## Task Commits

Each task was committed atomically:

1. **Task 1: API route modules for sync, settings, and OAuth** - `d3d8304` (feat)
2. **Task 2: OAuth, feature flag, and endpoint tests** - `8bf9d33` (test)

## Files Created/Modified
- `backend/app/api/v1/feishu_sync.py` - Push/pull/history/retry endpoints with NDJSON streaming
- `backend/app/api/v1/feishu_settings.py` - SyncConfig CRUD, credentials validation, feature flags
- `backend/app/api/v1/feishu_auth.py` - OAuth authorize-url + callback with CSRF state cookie
- `backend/app/services/feishu_oauth_service.py` - Async code exchange, user find-or-create, JWT issuance
- `backend/app/api/v1/router.py` - Registered 3 Feishu routers with RBAC guards
- `backend/app/api/v1/system.py` - Added /features endpoint for system-wide feature flags
- `backend/app/schemas/feishu.py` - Fixed datetime serialization for Read schemas
- `tests/test_feishu_auth.py` - 18 tests covering all endpoint categories

## Decisions Made
- Used `request.app.state.settings` instead of `Depends(get_settings)` to ensure test-injected Settings are honored (lru_cache bypass)
- Created `_get_client_safe()` DI wrapper that returns None instead of raising ValueError when Feishu credentials not configured -- prevents 500 errors when feature is disabled
- Set cookies directly on JSONResponse objects rather than using Response parameter, since returning a different response type discards the injected Response cookies
- Changed SyncConfigRead/SyncJobRead to accept `Union[str, datetime]` for created_at/updated_at fields

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Settings injection using request.app.state.settings**
- **Found during:** Task 2 (test_feature_flags_endpoint_returns_flags)
- **Issue:** `Depends(get_settings)` returns lru_cached singleton, ignoring test-injected Settings with feishu_sync_enabled=True
- **Fix:** Changed all Feishu endpoints to use `request.app.state.settings` pattern consistent with existing system endpoints
- **Files modified:** feishu_auth.py, feishu_settings.py, system.py
- **Committed in:** 8bf9d33

**2. [Rule 1 - Bug] Fixed FeishuClient DI failure when feature disabled**
- **Found during:** Task 2 (test_sync_endpoints_return_404_when_disabled)
- **Issue:** `Depends(get_feishu_client)` raises ValueError when credentials not configured, causing 500 before endpoint body runs feature flag check
- **Fix:** Created `_get_client_safe()` wrapper returning Optional[FeishuClient] that catches ValueError
- **Files modified:** feishu_sync.py, feishu_settings.py
- **Committed in:** 8bf9d33

**3. [Rule 1 - Bug] Fixed JSONResponse cookie propagation**
- **Found during:** Task 2 (test_oauth_authorize_url_sets_state_cookie)
- **Issue:** `response.set_cookie()` on injected Response parameter is discarded when endpoint returns a different JSONResponse
- **Fix:** Set cookie directly on the returned JSONResponse object
- **Files modified:** feishu_auth.py
- **Committed in:** 8bf9d33

**4. [Rule 1 - Bug] Fixed SyncConfigRead datetime serialization**
- **Found during:** Task 2 (test_sync_config_crud)
- **Issue:** SyncConfigRead expects `created_at: str` but ORM returns `datetime` objects
- **Fix:** Changed to `Union[str, datetime]` type annotation
- **Files modified:** backend/app/schemas/feishu.py
- **Committed in:** 8bf9d33

---

**Total deviations:** 4 auto-fixed (4 bugs)
**Impact on plan:** All fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed bugs above.

## Known Stubs
None -- all endpoints are fully wired to service layer from Plan 01.

## Next Phase Readiness
- All Feishu API endpoints ready for frontend integration (Plan 03)
- OAuth flow complete: authorize-url -> cookie -> callback -> JWT
- Feature flags endpoint available at /api/v1/system/features for conditional UI rendering
- 151 total tests passing (133 existing + 18 new, 0 regressions)

## Self-Check: PASSED

All 5 created files verified present. Both task commit hashes (d3d8304, 8bf9d33) confirmed in git log.

---
*Phase: 10-feishu-integration*
*Completed: 2026-04-02*
