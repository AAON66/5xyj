# Phase 10: Feishu Integration - Research

**Researched:** 2026-03-31
**Domain:** Feishu (Lark) Open Platform - Bitable API, OAuth 2.0, bidirectional sync
**Confidence:** MEDIUM-HIGH

## Summary

Phase 10 integrates the social insurance system with Feishu Bitable (multi-dimensional tables) for bidirectional data sync, plus optional Feishu OAuth login. The core technical challenge is three-fold: (1) wrapping Feishu's REST Bitable API for push/pull operations with conflict detection, (2) implementing a drag-and-drop field mapping UI that stores reusable configurations, and (3) adding Feishu OAuth as an alternative login method behind a feature flag.

The Feishu Open Platform provides well-documented REST APIs for Bitable CRUD operations. The official Python SDK `lark-oapi` (v1.5.3) exists but is heavyweight and brings dependencies (requests, pycryptodome, websockets) the project does not need. Since the project already uses `httpx` for DeepSeek API calls, the recommendation is to call Feishu APIs directly via `httpx` -- this keeps the dependency footprint small and aligns with existing patterns.

**Primary recommendation:** Use `httpx` directly for all Feishu API calls (Bitable CRUD + OAuth token exchange). Use `@xyflow/react` for the drag-and-drop field mapping UI. Implement feature flags via environment variables + Settings class, consistent with existing config patterns.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Support two push granularities: normalized record detail (per person per month) and summary level (by company+region+month), each to separate Bitable tables
- **D-02:** User chooses push detail or summary; each granularity has independently configured target table
- **D-03:** HR manually creates Bitable and defines columns; system auto-matches by column name or admin manually configures mapping
- **D-04:** Field mapping UI uses drag-and-drop line-drawing design: system fields on left, Feishu columns on right, drag to connect
- **D-05:** Support configuring multiple sync targets (multiple Bitable tables), each with independent field mapping
- **D-06:** Pull reuses the mapping recorded during push (reverse direction); must push first before pulling
- **D-07:** Push to existing data (same employee+month): prompt user to choose overwrite/skip/cancel with diff display
- **D-08:** Pull conflict preview supports two views: diff-only filter and batch strategy selection (summary + detail expand)
- **D-09:** Three conflict resolution strategies: system wins, Feishu wins, per-record selection
- **D-10:** Feishu OAuth login issues system JWT token (unified with password login)
- **D-11:** Bound users get existing role; unbound new users default to employee role
- **D-12:** Feishu OAuth controlled by feature flag, disabled by default
- **D-13:** Feishu App ID/Secret: env vars take priority (FEISHU_APP_ID / FEISHU_APP_SECRET), fallback to encrypted DB storage; admin can modify in settings UI
- **D-14:** Bitable sync targets (app_token / table_id) configured by admin in settings; HR only triggers sync
- **D-15:** Support multiple Bitable tables as sync targets
- **D-16:** Sync history list: timestamp, direction, target table, record count, success/failure
- **D-17:** Failed sync tasks support one-click retry
- **D-18:** Sync progress uses NDJSON streaming (reuse import pattern)
- **D-19:** Env vars as master switches (FEISHU_SYNC_ENABLED / FEISHU_OAUTH_ENABLED, default false); admin can fine-tune sub-features in UI
- **D-20:** Feature flag off = no Feishu menu items or routes in frontend

### Claude's Discretion
- Feishu API SDK choice (official SDK vs direct httpx) -- RECOMMENDATION: direct httpx
- Sync task database model design (SyncJob / SyncConfig) -- see Architecture Patterns
- Drag-and-drop line UI frontend library -- RECOMMENDATION: @xyflow/react
- Feishu OAuth callback implementation details
- Sync batch size and error retry strategy

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FEISHU-01 | System data push to Feishu Bitable | Bitable batch_create/batch_update APIs, httpx client, tenant_access_token auth, field mapping config |
| FEISHU-02 | Feishu Bitable data pull to system | Bitable search/list APIs, reverse field mapping, conflict detection via employee+month key |
| FEISHU-03 | Sync status viewable (success/failure/conflict records) | SyncJob model with status tracking, sync history API + frontend page |
| FEISHU-04 | Sync operations are manual-trigger only | No cron/scheduler; API endpoints triggered by HR button clicks |
| FEISHU-05 | Feishu OAuth login (optional, feature flag) | OAuth 2.0 authorization code flow, user_access_token exchange, JWT issuance |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Backend: FastAPI; Frontend: React with Ant Design 5.x
- Data processing: pandas, openpyxl ecosystem
- LLM: DeepSeek fallback only (not relevant to this phase)
- Must support dual template export (not affected by this phase)
- Rules-first approach; provenance tracking on all data
- SQLAlchemy 2.0 + Alembic for migrations
- Existing auth: JWT via PyJWT, dual-auth (JWT + API Key) in dependencies.py
- NDJSON streaming already implemented for aggregate/import operations
- Chinese localization throughout UI

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 (already installed) | Feishu API HTTP client | Already in project for DeepSeek; async-capable; no new dependency |
| @xyflow/react | 12.10.2 | Drag-and-drop field mapping UI | Industry standard for node/edge graph UIs in React; actively maintained |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyJWT (jwt) | already installed | JWT token issuance after OAuth | Reuse existing auth.py pattern |
| antd | 5.29.3 (already installed) | Sync status pages, settings forms, conflict preview tables | All UI components |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx (direct) | lark-oapi 1.5.3 (official SDK) | SDK adds requests, pycryptodome, websockets deps; project already uses httpx; direct calls are simpler for the limited API surface needed |
| @xyflow/react | react-dnd + custom canvas | react-dnd handles drag but not visual connections/lines; @xyflow/react provides the full line-drawing experience D-04 requires |
| @xyflow/react | Ant Design Pro mapping component | No official Ant Design mapping component exists; would need to hand-roll |

**Installation:**
```bash
# Backend -- no new packages needed (httpx already installed)

# Frontend
cd frontend && npm install @xyflow/react
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── api/v1/
│   ├── feishu_sync.py         # Push/pull/retry/history endpoints
│   ├── feishu_settings.py     # Sync config CRUD (admin only)
│   └── feishu_auth.py         # OAuth callback + login endpoint
├── services/
│   ├── feishu_client.py       # Low-level Feishu API wrapper (httpx)
│   ├── feishu_sync_service.py # Push/pull orchestration + conflict detection
│   ├── feishu_token_service.py # tenant_access_token caching
│   └── feishu_oauth_service.py # OAuth code exchange + user binding
├── models/
│   ├── sync_config.py         # SyncConfig (target table + field mapping)
│   └── sync_job.py            # SyncJob (execution history)
├── schemas/
│   └── feishu.py              # Pydantic schemas for all Feishu endpoints

frontend/src/
├── pages/
│   ├── FeishuSync.tsx         # Main sync page (push/pull triggers + history)
│   ├── FeishuSettings.tsx     # Admin config page (credentials + targets)
│   └── FeishuFieldMapping.tsx # Drag-and-drop mapping editor
├── services/
│   └── feishu.ts              # API client for feishu endpoints
├── hooks/
│   └── useFeishuFeatureFlag.ts # Feature flag hook for conditional rendering
```

### Pattern 1: Feishu API Client with Token Caching

**What:** A thin httpx wrapper that auto-manages tenant_access_token lifecycle
**When to use:** All server-to-server Feishu API calls (Bitable CRUD)
**Example:**
```python
# backend/app/services/feishu_client.py
import time
import httpx
from backend.app.core.config import get_settings

FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"

class FeishuClient:
    def __init__(self, app_id: str, app_secret: str):
        self._app_id = app_id
        self._app_secret = app_secret
        self._token: str | None = None
        self._token_expires_at: float = 0
        self._http = httpx.Client(base_url=FEISHU_BASE_URL, timeout=30)

    def _ensure_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 300:
            return self._token
        resp = self._http.post("/auth/v3/tenant_access_token/internal", json={
            "app_id": self._app_id,
            "app_secret": self._app_secret,
        })
        data = resp.json()
        self._token = data["tenant_access_token"]
        self._token_expires_at = time.time() + data["expire"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._ensure_token()}"}

    def list_fields(self, app_token: str, table_id: str) -> list[dict]:
        """Fetch all field definitions from a Bitable table."""
        resp = self._http.get(
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            headers=self._headers(), params={"page_size": 100}
        )
        return resp.json()["data"]["items"]

    def batch_create_records(self, app_token: str, table_id: str,
                             records: list[dict]) -> dict:
        """Create up to 1000 records in a single batch."""
        resp = self._http.post(
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            headers=self._headers(),
            json={"records": [{"fields": r} for r in records]}
        )
        return resp.json()

    def search_records(self, app_token: str, table_id: str,
                       filter_expr: str | None = None,
                       page_token: str | None = None) -> dict:
        """Search records with optional filter. Max 500 per page."""
        body: dict = {"page_size": 500}
        if filter_expr:
            body["filter"] = filter_expr
        if page_token:
            body["page_token"] = page_token
        resp = self._http.post(
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
            headers=self._headers(), json=body
        )
        return resp.json()
```

### Pattern 2: SyncConfig and SyncJob Models

**What:** Database models for sync configuration and execution history
**When to use:** Persisting field mappings, sync targets, and job history
**Example:**
```python
# backend/app/models/sync_config.py
from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class SyncConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sync_configs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    app_token: Mapped[str] = mapped_column(String(255), nullable=False)
    table_id: Mapped[str] = mapped_column(String(255), nullable=False)
    granularity: Mapped[str] = mapped_column(String(20), nullable=False)  # 'detail' | 'summary'
    field_mapping: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # field_mapping format: {"system_field": "feishu_column_name", ...}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# backend/app/models/sync_job.py
class SyncJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "sync_jobs"

    config_id: Mapped[str] = mapped_column(ForeignKey("sync_configs.id"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # 'push' | 'pull'
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # status: 'pending' | 'running' | 'success' | 'failed' | 'partial'
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    success_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(2000))
    detail: Mapped[dict | None] = mapped_column(JSON)  # conflict info, error details
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False)
```

### Pattern 3: Feature Flag Pattern

**What:** Environment variable master switches + DB-level fine-tuning
**When to use:** Controlling Feishu feature visibility
**Example:**
```python
# In config.py Settings class:
feishu_sync_enabled: bool = False
feishu_oauth_enabled: bool = False
feishu_app_id: str = ''
feishu_app_secret: str = ''

# In frontend -- useFeishuFeatureFlag hook:
# Calls GET /api/v1/system/features which returns enabled flags
# Navigation items conditionally rendered based on flags
```

### Pattern 4: OAuth Authorization Code Flow for Feishu

**What:** Standard OAuth 2.0 authorization code flow adapted for Feishu
**When to use:** FEISHU-05 - optional Feishu login
**Flow:**
1. Frontend redirects to `https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={APP_ID}&response_type=code&redirect_uri={URI}&state={CSRF_TOKEN}`
2. User authorizes on Feishu page
3. Feishu redirects back to frontend callback URL with `?code=xxx&state=yyy`
4. Frontend sends code to backend: `POST /api/v1/auth/feishu/callback`
5. Backend exchanges code for user_access_token via Feishu API: `POST /open-apis/authen/v1/access_token`
6. Backend extracts user info (name, open_id, union_id) from token response
7. Backend checks if Feishu user is bound to existing system user
8. If bound: issue system JWT with existing role
9. If not bound: create new user with employee role, issue JWT
10. Return JWT to frontend (same format as password login)

### Pattern 5: NDJSON Streaming for Sync Progress

**What:** Reuse existing NDJSON streaming pattern for real-time sync progress
**When to use:** Push/pull operations that process many records
**Example:**
```python
# Reuse the same StreamingResponse + async generator pattern from aggregate.py
async def push_stream(config_id: str, ...):
    async def event_stream():
        yield json.dumps({"type": "start", "total": total_records}) + "\n"
        for batch in chunks(records, 500):
            result = feishu_client.batch_create_records(...)
            yield json.dumps({"type": "progress", "processed": count}) + "\n"
        yield json.dumps({"type": "complete", "job_id": job.id}) + "\n"
    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
```

### Anti-Patterns to Avoid
- **Storing Feishu access tokens long-term:** tenant_access_token expires in 2h; cache in memory with refresh, never persist to DB
- **Calling Feishu API without rate limiting:** Bitable field list is 20 req/s; add simple throttling
- **Hardcoding field names in push/pull logic:** All field mapping must go through SyncConfig.field_mapping; never assume column names
- **Mixing sync concerns into existing import/export code:** Keep Feishu sync as a separate module; it reads from NormalizedRecord but has its own pipeline

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Visual field-to-field mapping with connecting lines | Custom SVG/Canvas drawing code | @xyflow/react nodes + edges | Complex drag, zoom, pan, line routing already solved |
| OAuth CSRF protection | Custom token generation | `secrets.token_urlsafe()` + session/cookie state | Avoid security mistakes |
| Token caching with expiry | Manual timer/thread | Simple in-memory cache with TTL check in FeishuClient | tenant_access_token is 2h, just check before each call |
| Conflict diff computation | Row-by-row comparison loop | dict comprehension comparing system vs Feishu record fields | Keep it simple -- these are flat key-value records |

**Key insight:** The Feishu Bitable API is straightforward REST CRUD. The complexity is not in calling it but in: (1) field mapping configuration/storage, (2) conflict detection during pull, and (3) the drag-and-drop mapping UI. Focus effort there.

## Common Pitfalls

### Pitfall 1: tenant_access_token vs user_access_token Confusion
**What goes wrong:** Using user_access_token for server-side batch operations, which requires per-user authorization
**Why it happens:** Feishu docs show both token types for every endpoint
**How to avoid:** Use tenant_access_token for ALL Bitable CRUD (push/pull). user_access_token is ONLY for OAuth login flow to get user identity.
**Warning signs:** "token expired" errors during batch operations; needing user interaction for background tasks

### Pitfall 2: Bitable Batch Size Limits
**What goes wrong:** Sending >1000 records in batch_create or >500 in search response
**Why it happens:** Not chunking data before API calls
**How to avoid:** Chunk push operations into batches of 500 (conservative, max 1000). Use page_token for paginated reads.
**Warning signs:** Error code 1254104 in Feishu response

### Pitfall 3: Feishu Field Type Mismatches
**What goes wrong:** Sending string values to number fields or wrong date format
**Why it happens:** System fields are Decimal/string but Feishu fields have specific type expectations
**How to avoid:** When discovering Feishu fields via list_fields API, store the field type. Apply type conversion in the push mapper: Decimal -> float for number fields, date string -> millisecond timestamp for date fields.
**Warning signs:** Error code 1254045 on batch_create

### Pitfall 4: Concurrent Write Conflicts on Bitable
**What goes wrong:** Two sync operations writing to the same Bitable simultaneously cause data corruption
**Why it happens:** Feishu recommends "request API write operations only once simultaneously for a single Base"
**How to avoid:** Implement a sync lock per SyncConfig (check if a job is already running before starting a new one). D-04 helps -- manual trigger means lower concurrency risk.
**Warning signs:** Error code 1254291 (write conflict)

### Pitfall 5: OAuth State Parameter Missing/Ignored
**What goes wrong:** CSRF attacks or callback parameter confusion
**Why it happens:** Skipping state parameter in OAuth redirect
**How to avoid:** Generate random state token, store in cookie/session, validate on callback before exchanging code
**Warning signs:** OAuth callback accepting any state value

### Pitfall 6: Feature Flag Frontend Leakage
**What goes wrong:** Feishu routes/components still accessible via direct URL when feature flag is off
**Why it happens:** Only hiding menu items but not guarding routes
**How to avoid:** Feature flag must control both navigation visibility AND route guard. Backend endpoints should also check the flag and return 404/403.
**Warning signs:** Accessing /feishu-sync directly when FEISHU_SYNC_ENABLED=false shows the page

## Code Examples

### Feishu OAuth Callback Handler
```python
# backend/app/api/v1/feishu_auth.py
@router.post("/auth/feishu/callback")
def feishu_oauth_callback(
    code: str = Body(...),
    state: str = Body(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.feishu_oauth_enabled:
        raise HTTPException(status_code=404, detail="Feishu OAuth is not enabled")

    # Exchange code for user info
    # 1. Get app_access_token first
    app_token_resp = httpx.post(
        "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": settings.feishu_app_id, "app_secret": settings.feishu_app_secret}
    )
    app_token = app_token_resp.json()["app_access_token"]

    # 2. Exchange code for user_access_token + user info
    user_resp = httpx.post(
        "https://open.feishu.cn/open-apis/authen/v1/access_token",
        headers={"Authorization": f"Bearer {app_token}"},
        json={"grant_type": "authorization_code", "code": code}
    )
    user_data = user_resp.json()["data"]
    # user_data contains: name, open_id, union_id, user_id, email, mobile

    # 3. Find or create system user
    user = find_user_by_feishu_open_id(db, user_data["open_id"])
    if not user:
        user = create_user_from_feishu(db, user_data, default_role="employee")

    # 4. Issue system JWT
    token, exp = issue_access_token(
        settings.auth_secret_key, user.username, user.role,
        settings.auth_token_expire_minutes
    )
    return {"access_token": token, "expires_at": exp.isoformat(), "role": user.role}
```

### Field Mapping Flow Node Setup (@xyflow/react)
```typescript
// frontend/src/pages/FeishuFieldMapping.tsx
import { ReactFlow, Background, Controls, type Node, type Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// System fields on left, Feishu columns on right
// Each field is a node; mappings are edges
const systemNodes: Node[] = systemFields.map((f, i) => ({
  id: `sys-${f.key}`,
  type: 'input',
  position: { x: 50, y: i * 60 },
  data: { label: f.label },
}));

const feishuNodes: Node[] = feishuColumns.map((c, i) => ({
  id: `fs-${c.field_id}`,
  type: 'output',
  position: { x: 450, y: i * 60 },
  data: { label: c.field_name },
}));

// User creates edges by dragging from system node handle to Feishu node handle
// On save, extract edge source/target to build field_mapping dict
```

### Push Sync Service
```python
# backend/app/services/feishu_sync_service.py
def push_records(db: Session, config: SyncConfig, records: list[NormalizedRecord]):
    client = get_feishu_client()
    mapping = config.field_mapping  # {"person_name": "姓名", "id_number": "身份证号", ...}

    mapped_records = []
    for rec in records:
        row = {}
        for sys_field, feishu_col in mapping.items():
            value = getattr(rec, sys_field, None)
            if value is not None:
                row[feishu_col] = float(value) if isinstance(value, Decimal) else str(value)
        mapped_records.append(row)

    # Chunk into batches of 500
    for chunk in chunked(mapped_records, 500):
        result = client.batch_create_records(config.app_token, config.table_id, chunk)
        if result.get("code") != 0:
            raise FeishuSyncError(result.get("msg", "Unknown error"))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Feishu OAuth via `/suite/passport/oauth/token` | OAuth via `/open-apis/authen/v1/access_token` + new authorize URL at `accounts.feishu.cn` | 2024-2025 | Old endpoint deprecated; must use new flow |
| Bitable `list` endpoint for reading records | Bitable `search` endpoint (POST with filters) | 2024 | List is deprecated; search is recommended |
| lark-oapi SDK mandatory | Direct REST API calls equally supported | Ongoing | No need for heavy SDK dependency |

**Deprecated/outdated:**
- `GET /bitable/v1/apps/:app_token/tables/:table_id/records` (list) -- deprecated in favor of `POST .../records/search`
- `POST /suite/passport/oauth/token` -- old OAuth token endpoint, use authen/v1/access_token instead

## Open Questions

1. **Feishu App Credentials Availability**
   - What we know: STATE.md notes "Feishu app credentials must be registered before Phase 10 can begin"
   - What's unclear: Whether the app has been registered on Feishu Open Platform yet
   - Recommendation: Implementation can proceed with mock/configurable credentials; real testing requires registered app with Bitable permissions

2. **Bitable Permission Scopes**
   - What we know: App needs `bitable:app` scope for read/write access
   - What's unclear: Exact minimum scopes needed; whether additional approval is required
   - Recommendation: Document required scopes (bitable:app, contact:user.base:readonly for OAuth) in settings page guidance text

3. **User Model Extension for Feishu Binding**
   - What we know: User model needs feishu_open_id and feishu_union_id columns
   - What's unclear: Whether to add columns directly to User table or create a separate FeishuUserBinding table
   - Recommendation: Add nullable columns to User table (simpler, one-to-one relationship); Alembic migration to add columns

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| httpx | Feishu API calls | Yes | 0.28.1 | -- |
| @xyflow/react | Field mapping UI | No (needs install) | 12.10.2 (npm) | -- |
| Feishu App credentials | All Feishu features | Unknown | -- | Graceful degradation: show config guidance |
| Alembic | DB migrations | Yes | 1.14.0 | -- |

**Missing dependencies with no fallback:**
- @xyflow/react must be installed via npm (frontend dependency)

**Missing dependencies with fallback:**
- Feishu App credentials: system works without them; shows configuration guidance instead of sync UI

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | No pytest.ini; uses default discovery |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEISHU-01 | Push records to Bitable via API | unit (mock httpx) | `pytest tests/test_feishu_sync.py::test_push_records -x` | No -- Wave 0 |
| FEISHU-01 | Push with field mapping transformation | unit | `pytest tests/test_feishu_sync.py::test_push_field_mapping -x` | No -- Wave 0 |
| FEISHU-02 | Pull records from Bitable | unit (mock httpx) | `pytest tests/test_feishu_sync.py::test_pull_records -x` | No -- Wave 0 |
| FEISHU-02 | Pull conflict detection (same employee+month) | unit | `pytest tests/test_feishu_sync.py::test_pull_conflict_detection -x` | No -- Wave 0 |
| FEISHU-03 | Sync history API returns job list | unit | `pytest tests/test_feishu_sync.py::test_sync_history -x` | No -- Wave 0 |
| FEISHU-04 | No auto-sync scheduler exists | manual-only | Verify no cron/background task code | -- |
| FEISHU-05 | OAuth callback exchanges code for JWT | unit (mock httpx) | `pytest tests/test_feishu_auth.py::test_oauth_callback -x` | No -- Wave 0 |
| FEISHU-05 | OAuth disabled returns 404 | unit | `pytest tests/test_feishu_auth.py::test_oauth_disabled -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_feishu_sync.py tests/test_feishu_auth.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_feishu_sync.py` -- covers FEISHU-01, FEISHU-02, FEISHU-03, FEISHU-04
- [ ] `tests/test_feishu_auth.py` -- covers FEISHU-05
- [ ] Mock fixtures for Feishu API responses (httpx mock or respx library)
- [ ] `conftest.py` update: add feishu-related Settings overrides and seed data fixtures

## Sources

### Primary (HIGH confidence)
- [Feishu Bitable API Overview](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview) -- endpoints, auth, batch limits
- [Feishu Bitable batch_create API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/batch_create) -- 1000 record limit, field format, error codes
- [Feishu Bitable list fields API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/list) -- field discovery, types, pagination
- [Feishu tenant_access_token API](https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal) -- 2h expiry, refresh logic
- [Feishu OAuth authorize endpoint](https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code) -- authorization URL, parameters, code flow
- [Feishu authen/v1/access_token API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/authen-v1/authen/access_token) -- code exchange, user info in response
- [lark-oapi on PyPI](https://pypi.org/project/lark-oapi/) -- v1.5.3, official ByteDance SDK (evaluated but not recommended)
- [@xyflow/react on npm](https://www.npmjs.com/package/@xyflow/react) -- v12.10.2, React Flow library

### Secondary (MEDIUM confidence)
- [fastapi-oauth20 Feishu client docs](https://fastapi-practices.github.io/fastapi-oauth20/clients/feishu/) -- Feishu OAuth setup steps
- [feishu-lark-agent GitHub](https://github.com/joeseesun/feishu-lark-agent/) -- Python Bitable interaction reference

### Tertiary (LOW confidence)
- Feishu Bitable search API pagination behavior -- official doc says max 500 per page but pagination token mechanics not fully verified

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- httpx already in project, @xyflow/react well-documented with clear version
- Architecture: HIGH -- patterns follow existing project conventions (models, services, API routes)
- Pitfalls: MEDIUM-HIGH -- based on official API docs and error codes; some edge cases may emerge during real testing
- Feishu OAuth flow: MEDIUM -- old endpoint deprecated, new flow documented but some transition details unclear

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (Feishu API is stable; check for deprecation notices monthly)
