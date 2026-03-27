# Architecture Patterns

**Domain:** Social Insurance & Housing Fund Management System (v2 milestone)
**Researched:** 2026-03-27
**Focus:** Auth, Employee Portal, Feishu Integration, External API Layer

## Current Architecture Snapshot

The system is a monolithic two-tier application: React SPA (frontend) communicating over REST/NDJSON to a FastAPI backend, with SQLite (WAL mode) as the database. The backend is layered: API routes -> services -> parsers/validators/exporters -> models. The core data pipeline is sequential: Upload -> Parse -> Normalize -> Validate -> Match -> Export.

**What already exists and must not break:**
- Full data processing pipeline (upload through dual-template export)
- JWT auth with two roles (`admin`, `hr`) using custom HMAC-signed tokens
- Employee self-service endpoint (`POST /employees/self-service/query`) that is already unauthenticated
- `AuthProvider` in React managing session via localStorage
- `require_authenticated_user` FastAPI dependency for route protection
- Auth toggle via `auth_enabled` setting

## Recommended Architecture for v2

### High-Level Component Map

```
+---------------------------------------------------+
|                    BROWSER                         |
|  +---------------------------------------------+  |
|  |              React SPA (Vite)                |  |
|  |                                              |  |
|  |  +----------+  +----------+  +------------+ |  |
|  |  | Admin    |  | HR       |  | Employee   | |  |
|  |  | Console  |  | Console  |  | Portal     | |  |
|  |  +----------+  +----------+  +------------+ |  |
|  |         |            |             |         |  |
|  |  +------+------------+-------------+------+  |  |
|  |  |         AuthProvider (extended)        |  |  |
|  |  |  - JWT session (admin/hr)              |  |  |
|  |  |  - Employee token (limited scope)      |  |  |
|  |  |  - Feishu OAuth callback handler       |  |  |
|  |  +----------------------------------------+  |  |
|  +---------------------------------------------+  |
+---------------------------------------------------+
              |  REST / NDJSON
              v
+---------------------------------------------------+
|              FastAPI Backend                        |
|                                                    |
|  +----------------------------------------------+ |
|  |               API Layer (/api/v1/)            | |
|  |                                               | |
|  |  /auth       - login, feishu-callback, me     | |
|  |  /portal     - employee self-service (NEW)    | |
|  |  /aggregate  - pipeline operations            | |
|  |  /imports    - batch lifecycle                 | |
|  |  /employees  - master CRUD                    | |
|  |  /dashboard  - stats                          | |
|  |  /compare    - cross-batch diff               | |
|  |  /mappings   - header mapping audit           | |
|  |  /feishu     - sync triggers, webhook (NEW)   | |
|  |  /system     - health, runtime                | |
|  +----------------------------------------------+ |
|                      |                             |
|  +----------------------------------------------+ |
|  |          Auth & Permission Layer              | |
|  |                                               | |
|  |  require_role('admin')                        | |
|  |  require_role('hr')                           | |
|  |  require_role('admin', 'hr')                  | |
|  |  require_employee_token()     (NEW)           | |
|  |  optional_feishu_identity()   (NEW)           | |
|  +----------------------------------------------+ |
|                      |                             |
|  +----------------------------------------------+ |
|  |            Service Layer                      | |
|  |                                               | |
|  |  [existing services unchanged]                | |
|  |  + feishu_sync_service.py     (NEW)           | |
|  |  + feishu_auth_service.py     (NEW)           | |
|  |  + portal_service.py          (NEW)           | |
|  |  + api_key_service.py         (NEW, optional) | |
|  +----------------------------------------------+ |
|                      |                             |
|  +------+    +-------+-------+    +-----------+   |
|  |SQLite|    |  Feishu API   |    | DeepSeek  |   |
|  | (WAL)|    | (lark-oapi)   |    |  (LLM)    |   |
|  +------+    +---------------+    +-----------+   |
+---------------------------------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Auth Required |
|-----------|---------------|-------------------|---------------|
| **Admin Console** (frontend) | System config, user management, all data access | Backend via JWT (admin role) | admin JWT |
| **HR Console** (frontend) | Data management, import/export, employee ops | Backend via JWT (hr role) | hr JWT |
| **Employee Portal** (frontend) | Personal social insurance lookup, read-only | Backend via employee token | employee token |
| **Auth Module** (backend) | JWT issuance, Feishu OAuth exchange, employee verification | SQLite, Feishu OAuth API | None (login endpoints) |
| **Portal Service** (backend) | Employee-scoped data queries, personal record view | SQLite (NormalizedRecord, EmployeeMaster) | employee token |
| **Feishu Sync Service** (backend) | Bidirectional sync with Feishu bitable | Feishu Bitable API via lark-oapi | tenant_access_token (machine) |
| **Feishu Auth Service** (backend) | OAuth code exchange, user identity resolution | Feishu OAuth API | None (callback) |
| **External API** (backend) | Programmatic access for third-party tools | Existing service layer | API key or JWT |
| **Existing Pipeline** (backend) | Upload -> Parse -> Normalize -> Validate -> Match -> Export | SQLite, DeepSeek | admin/hr JWT |

## Detailed Architecture by Feature

### 1. Auth System Evolution

**Current state:** Two hardcoded users (admin/hr) with passwords in env vars. Custom HMAC-SHA256 token format. Works but not extensible.

**Recommended evolution:** Keep the existing auth module structure but extend it to support three authentication paths:

```
Authentication Paths:

  1. Password Login (existing)
     POST /auth/login  { username, password, role }
     -> JWT { sub, role: admin|hr, exp }

  2. Employee Verification (NEW)
     POST /portal/verify  { employee_id, id_number, name }
     -> EmployeeToken { sub: employee_id, scope: portal, exp }

  3. Feishu OAuth (NEW, optional)
     GET  /auth/feishu/authorize  -> redirect to Feishu
     GET  /auth/feishu/callback?code=xxx
     -> JWT { sub, role, feishu_user_id, exp }
```

**Key decisions:**

- **Do NOT replace the custom token format with a full JWT library (like python-jose).** The current HMAC-signed token works fine for a single-company internal tool. Adding PyJWT or python-jose adds a dependency for zero practical benefit here. The existing format is essentially a simplified JWT.

- **Employee tokens are a separate token type.** They carry `scope: portal` and only grant access to `/portal/*` endpoints. They should have a shorter expiry (e.g., 60 minutes) since employees don't need persistent sessions.

- **Feishu OAuth is additive, not replacing.** Password login remains primary. Feishu OAuth is a convenience for users already logged into Feishu. Map Feishu user_id to an internal role via a `feishu_user_mappings` table or config.

**Backend changes:**

```python
# backend/app/core/auth.py - extend AuthRole
AuthRole = Literal['admin', 'hr', 'employee']

# backend/app/dependencies.py - add role-based guards
def require_role(*allowed_roles: AuthRole):
    def dependency(user: AuthUser = Depends(require_authenticated_user)):
        if user.role not in allowed_roles:
            raise HTTPException(403, 'Insufficient permissions')
        return user
    return Depends(dependency)

# Usage in router.py:
api_router.include_router(imports_router, dependencies=[require_role('admin', 'hr')])
api_router.include_router(portal_router, dependencies=[require_role('employee')])
```

**Frontend changes:**

- Extend `AuthProvider` to handle employee token type alongside admin/hr JWT
- Add route guards: `<RequireRole roles={['admin', 'hr']}>` wrapper component
- Employee portal gets its own login page (verify by employee_id + id_number + name)

### 2. Employee Portal

**Purpose:** Employees look up their own social insurance and housing fund records. Read-only. No access to other employees' data.

**Data flow:**

```
Employee opens /portal
  -> enters employee_id + id_number + name
  -> POST /portal/verify
  -> backend checks EmployeeMaster table
  -> returns EmployeeToken (scoped, short-lived)
  -> frontend stores token, redirects to /portal/dashboard

Employee views records
  -> GET /portal/my-records?period=202602
  -> backend decodes EmployeeToken, extracts employee_id
  -> queries NormalizedRecord WHERE matched employee_id = token.sub
  -> returns personal records only

Employee views summary
  -> GET /portal/my-summary
  -> backend aggregates across periods for this employee
  -> returns summary (total contributions by type, trend)
```

**New backend module: `backend/app/services/portal_service.py`**

Responsibilities:
- Verify employee identity against `EmployeeMaster` table
- Query `NormalizedRecord` + `MatchResult` scoped to single employee
- Aggregate personal totals across billing periods
- Return read-only data (no mutations)

**New API router: `backend/app/api/v1/portal.py`**

```
POST /portal/verify          -> employee token
GET  /portal/my-records      -> list of personal NormalizedRecords
GET  /portal/my-summary      -> aggregated personal summary
```

**Security boundary:** The portal service MUST only return records where `MatchResult.employee_master_id` matches the authenticated employee. Never accept employee_id as a query parameter -- always derive from token.

### 3. Feishu Bitable Sync

**Purpose:** Bidirectional sync between the system's SQLite data and a Feishu bitable (multi-dimensional table). HR can view/edit data in Feishu; changes flow back to the system.

**Architecture pattern: Hub-and-spoke with system as hub.**

```
System (SQLite) <-----> Feishu Sync Service <-----> Feishu Bitable API
                             |
                        lark-oapi SDK
                   (tenant_access_token)
```

**Sync directions:**

| Direction | Trigger | What Syncs |
|-----------|---------|------------|
| System -> Feishu | After successful export, or manual trigger | NormalizedRecords for a billing period |
| Feishu -> System | Manual trigger or webhook | Records edited in Feishu bitable |

**Key design decisions:**

- **Use `tenant_access_token` (not user_access_token) for sync.** This is a machine-to-machine integration. The Feishu app acts on behalf of the organization, not a specific user. Simplifies auth -- no per-user OAuth needed for sync.

- **Use `lark-oapi` Python SDK (v1.5.3).** Official Larksuite SDK, supports all bitable endpoints, handles token refresh automatically. Install: `pip install lark-oapi`.

- **Batch operations with 500-record pages.** Feishu bitable supports up to 1000 records per batch request, but 500 is safer for reliability. Implement pagination for both reads and writes.

- **Conflict resolution: system wins.** For system->Feishu pushes, system data overwrites Feishu. For Feishu->system pulls, present diffs for HR review before committing. Never auto-merge Feishu edits into system.

- **Sync is NOT real-time.** It is triggered (manually or after export). Do not build a polling loop or webhook listener initially -- add webhooks in a later phase if needed.

**New backend module: `backend/app/services/feishu_sync_service.py`**

```python
class FeishuSyncService:
    def __init__(self, settings: Settings):
        self.client = lark.Client.builder()
            .app_id(settings.feishu_app_id)
            .app_secret(settings.feishu_app_secret)
            .build()

    async def push_records_to_bitable(self, period: str, records: list[NormalizedRecord]):
        """Push normalized records to Feishu bitable for a billing period."""
        # 1. Map NormalizedRecord fields to bitable field names
        # 2. Batch upsert (match on id_number + period)
        # 3. Return sync result (created, updated, failed counts)

    async def pull_records_from_bitable(self, period: str):
        """Pull records from Feishu bitable and return diffs."""
        # 1. Fetch all records for period from bitable
        # 2. Compare with system NormalizedRecords
        # 3. Return diff list for HR review (NOT auto-apply)
```

**New config entries in `Settings`:**

```python
feishu_app_id: str = ''
feishu_app_secret: str = ''
feishu_bitable_app_token: str = ''      # The bitable document ID
feishu_bitable_table_id: str = ''        # The specific table within the bitable
feishu_sync_enabled: bool = False        # Feature flag, off by default
```

**New API router: `backend/app/api/v1/feishu.py`**

```
POST /feishu/sync/push    { period }     -> push to Feishu bitable
POST /feishu/sync/pull    { period }     -> pull from Feishu, return diffs
POST /feishu/sync/apply   { diff_ids }   -> apply approved diffs
GET  /feishu/sync/status                 -> last sync status
```

**Rate limit awareness:** Feishu recommends only one concurrent write API call per bitable. The sync service must serialize write operations and implement retry with backoff.

### 4. Feishu OAuth Login (Optional)

**Purpose:** Allow admin/HR users to log in via Feishu SSO instead of username/password.

**Flow:**

```
1. User clicks "Login with Feishu" on frontend
2. Frontend redirects to:
   https://open.feishu.cn/open-apis/authen/v1/authorize
     ?app_id={feishu_app_id}
     &redirect_uri={backend_url}/api/v1/auth/feishu/callback
     &state={csrf_token}
3. User authorizes in Feishu
4. Feishu redirects to callback with ?code=xxx
5. Backend exchanges code for user_access_token via:
   POST https://open.feishu.cn/open-apis/authen/v2/oauth/token
6. Backend fetches user info (name, email, employee_id)
7. Backend looks up role mapping (feishu_user_id -> admin|hr)
8. Backend issues internal JWT with role
9. Redirect to frontend with JWT in URL fragment or set cookie
```

**New backend module: `backend/app/services/feishu_auth_service.py`**

Responsibilities:
- Exchange OAuth code for Feishu user_access_token
- Fetch user identity from Feishu
- Map Feishu user to internal role (via config or DB table)
- Issue internal JWT

**New model (optional): `FeishuUserMapping`**

```python
class FeishuUserMapping(Base):
    feishu_user_id: str       # From Feishu OAuth
    feishu_name: str          # Display name
    internal_role: AuthRole   # admin | hr
    is_active: bool
```

This can also be a simple JSON config file if the number of Feishu-mapped users is small (< 20).

### 5. External API Layer

**Purpose:** Allow external tools/scripts to programmatically access system data.

**Recommendation: Reuse existing API structure with API key authentication.**

The current `/api/v1/` routes already form a reasonable REST API. The "external API" does not need a separate set of endpoints. Instead:

1. **Add API key authentication as an alternative to JWT.** External tools send `X-API-Key` header instead of Bearer token.
2. **API keys are scoped to a role** (admin or hr), so existing permission checks work unchanged.
3. **API keys are stored in the database** with hashed values, created/revoked by admins.

**New model: `ApiKey`**

```python
class ApiKey(Base):
    id: UUID
    name: str                # Human-readable label ("HR automation script")
    key_hash: str            # SHA-256 of the actual key
    role: AuthRole           # Permission scope
    is_active: bool
    created_by: str          # Admin who created it
    last_used_at: datetime
    expires_at: datetime | None
```

**Extend `require_authenticated_user` dependency:**

```python
def require_authenticated_user(request, credentials, x_api_key):
    # 1. Check Bearer token first (existing flow)
    # 2. If no Bearer, check X-API-Key header
    # 3. If API key found, look up in DB, verify hash, return AuthUser with key's role
    # 4. If neither, raise 401
```

This approach means zero new endpoints needed for external API access. External tools call the same `/api/v1/imports`, `/api/v1/employees`, etc. endpoints.

**New API router: `backend/app/api/v1/api_keys.py`**

```
POST   /api-keys            -> create API key (admin only, returns key once)
GET    /api-keys             -> list API keys (admin only, no key values)
DELETE /api-keys/{key_id}    -> revoke API key (admin only)
```

## Data Flow Summary

```
                    INBOUND DATA
                    ============

Excel Upload ──────────> Pipeline ──────> SQLite (NormalizedRecords)
                                              |
Feishu Bitable Pull ──> Diff Review ──> Apply to SQLite (manual)
                                              |
                    OUTBOUND DATA             |
                    =============             |
                                              v
Admin/HR Console <──── REST API <──── Service Layer <── SQLite
Employee Portal  <──── Portal API <── Portal Service <── SQLite (scoped)
External Tools   <──── REST API   <── Service Layer  <── SQLite
Feishu Bitable   <──── Sync Push  <── Sync Service   <── SQLite
Dual Templates   <──── Export     <── Export Service  <── SQLite
```

## Component Dependency Graph (Build Order)

Build order follows dependency arrows. Items at the same level can be built in parallel.

```
Level 0 (foundation - no dependencies):
  [A] Auth role extension (add 'employee' role, require_role() helper)
  [B] Settings extension (feishu config entries, api key config)

Level 1 (depends on Level 0):
  [C] Employee Portal backend (depends on A: employee token)
  [D] API Key model + auth extension (depends on A: role-based keys)
  [E] Feishu Sync Service skeleton (depends on B: feishu config)

Level 2 (depends on Level 1):
  [F] Employee Portal frontend (depends on C: portal API)
  [G] Feishu OAuth login (depends on E: feishu client setup)
  [H] API Key management UI (depends on D: api key CRUD)
  [I] Feishu push/pull implementation (depends on E: sync skeleton)

Level 3 (depends on Level 2):
  [J] Frontend redesign (depends on F, G, H: all new pages exist)
  [K] Feishu webhook listener (depends on I: sync is working)
```

**Suggested phase mapping:**

| Phase | Components | Rationale |
|-------|-----------|-----------|
| Phase 1 | A, B, C, D | Auth foundation + portal backend. No external dependencies. |
| Phase 2 | F, H | Portal frontend + API key UI. Delivers user-facing value. |
| Phase 3 | E, I | Feishu sync. Requires Feishu app credentials (external dependency). |
| Phase 4 | G | Feishu OAuth. Nice-to-have, depends on Feishu app being configured. |
| Phase 5 | J | Frontend redesign. Do last so all pages/routes are stable. |

## Patterns to Follow

### Pattern 1: Role-Scoped Dependencies

**What:** Use FastAPI dependency injection to enforce role-based access at the router level, not inside each endpoint.

**When:** Every protected route.

**Example:**

```python
# dependencies.py
def require_role(*allowed: AuthRole):
    def _guard(user: AuthUser = Depends(require_authenticated_user)):
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail='Insufficient permissions.')
        return user
    return Depends(_guard)

# router.py
api_router.include_router(imports_router, dependencies=[require_role('admin', 'hr')])
api_router.include_router(portal_router, dependencies=[require_role('employee')])
api_router.include_router(api_keys_router, dependencies=[require_role('admin')])
```

### Pattern 2: Token Scope Separation

**What:** Employee tokens and admin/hr tokens are distinct token types with different payloads and expiry.

**When:** Issuing tokens, verifying tokens.

**Example:**

```python
# Employee token payload includes scope field
{
    "sub": "EMP001",
    "role": "employee",
    "scope": "portal",
    "employee_master_id": "uuid-here",
    "exp": 1711540800  # 60 min
}

# Admin/HR token payload (existing format, unchanged)
{
    "sub": "admin",
    "role": "admin",
    "exp": 1711569600  # 480 min
}
```

### Pattern 3: Feature Flags for External Integrations

**What:** Gate Feishu sync and OAuth behind feature flags in Settings. System must work with these disabled.

**When:** Any external integration.

**Example:**

```python
# config.py
feishu_sync_enabled: bool = False
feishu_oauth_enabled: bool = False

# feishu router
@router.post('/sync/push')
def push_to_feishu(settings = Depends(get_settings)):
    if not settings.feishu_sync_enabled:
        raise HTTPException(501, 'Feishu sync is not enabled.')
```

### Pattern 4: Sync as Explicit Action, Not Background Process

**What:** All data synchronization (Feishu push/pull) is triggered by explicit user action via API call. No background polling, no cron jobs.

**When:** Feishu integration.

**Why:** SQLite does not handle concurrent writes well. A background sync process competing with user-initiated pipeline operations will cause locking issues. Explicit triggers let the user control when writes happen.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Shared Token Namespace

**What:** Using the same token format/verification for admin/hr and employee roles without scope distinction.

**Why bad:** An employee token that passes `require_authenticated_user` could be used to access admin endpoints if role checking is done inconsistently. A missing `require_role()` on one endpoint becomes a privilege escalation.

**Instead:** Always use `require_role()` at the router level. The `require_authenticated_user` dependency alone is not sufficient for authorization.

### Anti-Pattern 2: Real-Time Feishu Sync

**What:** Building a webhook listener or polling loop for continuous Feishu sync.

**Why bad:** SQLite WAL mode allows one writer at a time. A background sync writer competing with the import pipeline will cause `SQLITE_BUSY` errors under load. Also, real-time sync is complex to get right (conflict resolution, ordering, retries).

**Instead:** Manual push/pull with explicit triggers. Add webhook support only after migrating to PostgreSQL (if ever).

### Anti-Pattern 3: Separate API for External Consumers

**What:** Creating a `/api/external/` or `/api/public/` route namespace that duplicates existing endpoints.

**Why bad:** Doubles maintenance burden. API drift between internal and external versions. Double the test surface.

**Instead:** Reuse existing `/api/v1/` endpoints. Add API key auth as an alternative credential type. External consumers get the same API as the frontend.

### Anti-Pattern 4: Storing Employee Passwords

**What:** Creating a user account table with passwords for the employee portal.

**Why bad:** Employees already have identity data in `EmployeeMaster` (employee_id, id_number, name). Creating a separate password system adds registration flow, password reset, and account management overhead for a simple lookup portal.

**Instead:** Verify identity using existing `EmployeeMaster` fields (employee_id + id_number + name), issue a short-lived scoped token. No passwords stored.

## Scalability Considerations

| Concern | Current (< 100 users) | At 500 users | At 2000+ users |
|---------|----------------------|-------------|----------------|
| **Auth** | Hardcoded users in env | Still fine for admin/hr; employee tokens scale naturally | Consider DB-backed user table for admin/hr |
| **SQLite concurrency** | No issues | WAL handles reads well; serialize writes | Migrate to PostgreSQL if write contention appears |
| **Feishu sync volume** | < 1000 records/sync | Batch in 500-record pages | Add progress streaming for large syncs |
| **API key management** | 1-5 keys | DB-backed, fine | Add rate limiting per key |
| **Employee portal** | Few concurrent users | Read-only queries, SQLite handles well | Add query caching if slow |

## SQLite Compatibility Notes

The architecture deliberately avoids patterns that stress SQLite:

1. **No background workers** -- all processing is request-scoped or explicitly triggered
2. **No concurrent writes** -- Feishu sync is manual, not background
3. **Employee portal is read-only** -- no write contention from portal users
4. **API keys verified via single SELECT** -- minimal DB load per request

If the system ever needs concurrent background processing (e.g., scheduled Feishu sync, automatic re-parsing), that is the signal to migrate to PostgreSQL. Until then, SQLite is appropriate.

## New Database Models Summary

| Model | Purpose | Phase |
|-------|---------|-------|
| `ApiKey` | External API authentication | Phase 1 |
| `FeishuUserMapping` | Map Feishu users to internal roles | Phase 3 (or config file) |
| `FeishuSyncLog` | Track sync operations and status | Phase 3 |

No changes needed to existing models. The employee portal queries existing `NormalizedRecord` and `MatchResult` tables.

## New Config Entries Summary

```python
# Auth extensions
employee_token_expire_minutes: int = 60

# Feishu integration
feishu_app_id: str = ''
feishu_app_secret: str = ''
feishu_bitable_app_token: str = ''
feishu_bitable_table_id: str = ''
feishu_sync_enabled: bool = False
feishu_oauth_enabled: bool = False
feishu_oauth_redirect_uri: str = ''

# API keys
api_key_enabled: bool = True
```

## Sources

- [Feishu Bitable API Overview](https://open.larkoffice.com/document/server-docs/docs/bitable-v1/bitable-overview) -- Bitable endpoints, auth requirements, batch limits
- [Feishu Bitable Data Structure](https://open.larkoffice.com/document/server-docs/docs/bitable-v1/bitable-structure) -- Table/record/field model
- [lark-oapi on PyPI](https://pypi.org/project/lark-oapi/) -- v1.5.3, Python SDK for all Feishu APIs
- [Feishu OAuth Login Overview](https://open.feishu.cn/document/sso/web-application-sso/login-overview) -- SSO login flow documentation
- [Feishu user_access_token API](https://open.feishu.cn/document/authentication-management/access-token/get-user-access-token) -- OAuth code exchange endpoint
- [Feishu OAuth implementation guide](https://iamazing.cn/page/feishu-oauth-login) -- Practical implementation walkthrough

---

*Architecture research: 2026-03-27*
