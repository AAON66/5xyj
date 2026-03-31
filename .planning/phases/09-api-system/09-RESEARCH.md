# Phase 9: API System - Research

**Researched:** 2026-03-31
**Domain:** REST API formalization, API Key authentication, OpenAPI documentation
**Confidence:** HIGH

## Summary

Phase 9 converts the existing internal FastAPI endpoints into a formal external REST API system. The codebase already has a well-structured `/api/v1/` router with role-based access control via JWT, unified response helpers (`success_response`/`error_response`), and consistent patterns across all endpoint modules. The primary work is: (1) adding an `ApiKey` model and CRUD management endpoints, (2) extending `dependencies.py` to accept both JWT and `X-API-Key` authentication transparently, (3) adding pagination fields to `success_response`, (4) enriching all endpoints with Chinese descriptions and OpenAPI tags, (5) restricting `/docs` access to admin role, and (6) generating a Markdown API document.

No new external libraries are needed. FastAPI's built-in OpenAPI generation, Python's `secrets` and `hashlib` standard libraries, and the existing SQLAlchemy/Pydantic stack cover all requirements. The key technical challenge is making the dual-auth (JWT + API Key) transparent to business logic so no endpoint code changes are needed beyond adding descriptions.

**Primary recommendation:** Extend `require_authenticated_user` in `dependencies.py` to check `X-API-Key` header first (DB lookup), fall back to Bearer JWT, and return the same `AuthUser` dataclass -- making all existing role checks work automatically for API Key users.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** API Key binds to a specific user (admin/HR), inherits that user's role permissions, audit logs trace to the specific user
- **D-02:** API Key never expires, admin can manually disable or delete
- **D-03:** Each user can have at most 5 API Keys
- **D-04:** API Key passed via `X-API-Key` request header
- **D-05:** Only admin role can create and manage API Keys
- **D-06:** External API and frontend share the same `/api/v1/` endpoints, only authentication method differs (JWT vs API Key)
- **D-07:** All existing functionality open to API Key; sensitive functions (user management, audit logs) only accessible with admin API Key
- **D-08:** Backend dependencies layer handles both JWT and API Key authentication transparently to business layer
- **D-09:** Keep existing `{success, message, data}` / `{success, error: {code, message}}` response structure unchanged
- **D-10:** List endpoints add pagination in response: `{total, page, page_size}`
- **D-11:** Establish unified error code prefix system by module: AUTH_xxx, IMPORT_xxx, EMPLOYEE_xxx, EXPORT_xxx, SYSTEM_xxx
- **D-12:** All endpoints, parameters, models get Chinese description/summary
- **D-13:** Endpoints grouped by functional tags (social insurance queries, employee management, import/export, authentication, system management)
- **D-14:** Key endpoints provide request/response example values (FastAPI example schema)
- **D-15:** Internal-only endpoints (e.g., system config) hidden from Swagger (`include_in_schema=False`)
- **D-16:** /docs only accessible after admin role login
- **D-17:** Additionally generate Markdown format API documentation file
- **D-18:** Provide an API endpoint (GET /api/v1/docs/markdown) returning API doc content

### Claude's Discretion
- API Key generation algorithm and length (recommended 32-64 character random string)
- API Key storage in database (plaintext vs hash, recommended hash with one-time display)
- Pagination parameter defaults and maximums
- Error code numbering rules specifics
- Markdown document format and section structure

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-01 | RESTful API covers all core functions (social insurance queries/employee management/import-export) | All existing endpoints already at `/api/v1/`; need Chinese descriptions and tag grouping |
| API-02 | API documentation auto-generated (OpenAPI/Swagger) | FastAPI auto-generates; need Chinese descriptions, example schemas, /docs access control |
| API-03 | API response format unified and standardized | Existing `success_response`/`error_response` cover base; need pagination extension and error code prefixes |
| API-04 | External programs can call all public endpoints via API Key | Dual-auth in dependencies.py; ApiKey model; CRUD endpoints |
| AUTH-07 | API Key authentication mechanism (for external program calls) | ApiKey model + `require_authenticated_user` extension |
| AUTH-08 | Admin can create and manage API Keys | CRUD endpoints + frontend management page |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.0 | Web framework (already installed) | Already in use; built-in OpenAPI generation |
| SQLAlchemy | 2.0.36 | ORM (already installed) | Already in use for all models |
| Pydantic | 2.10.3 | Schema validation (already installed) | Already in use for all schemas |
| secrets (stdlib) | Python 3.x | API Key generation | `secrets.token_urlsafe(48)` produces cryptographically secure random strings |
| hashlib (stdlib) | Python 3.x | API Key hashing (SHA-256) | Standard, no dependency; hash stored, plaintext shown once |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Ant Design | 5.x | Frontend UI (already installed) | API Key management page |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SHA-256 for key hashing | bcrypt (already available via pwdlib) | SHA-256 is sufficient for random API keys (no dictionary attacks); bcrypt adds unnecessary latency on every API call |
| Custom Markdown generation | Sphinx/MkDocs | Overkill; FastAPI OpenAPI schema can be walked programmatically |

**No new packages required.** All dependencies are already in the project.

## Architecture Patterns

### Recommended Project Structure (new/modified files)
```
backend/app/
  models/
    api_key.py            # NEW: ApiKey SQLAlchemy model
  schemas/
    api_key.py            # NEW: Pydantic schemas for API Key CRUD
  services/
    api_key_service.py    # NEW: business logic (create, list, revoke, lookup)
  api/v1/
    api_keys.py           # NEW: CRUD endpoints for API Key management
    responses.py          # MODIFY: add paginated_response helper
    router.py             # MODIFY: add api_keys router, update tags
    auth.py               # MINOR: no change needed (separate module for keys)
  dependencies.py         # MODIFY: dual-auth (JWT + API Key)
  main.py                 # MODIFY: /docs access control, app metadata
  core/
    api_doc_generator.py  # NEW: Markdown doc generation from OpenAPI schema
frontend/src/
  pages/
    ApiKeys.tsx           # NEW: API Key management page (admin only)
  services/
    apiKeys.ts            # NEW: frontend API client for key management
```

### Pattern 1: Dual Authentication in Dependencies
**What:** Extend `require_authenticated_user` to check `X-API-Key` header first, then fall back to Bearer JWT. Returns the same `AuthUser` dataclass so all downstream `require_role` checks work unchanged.
**When to use:** Every authenticated request.
**Example:**
```python
# In dependencies.py
from fastapi import Header
from typing import Optional

def require_authenticated_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> AuthUser:
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return default_authenticated_user()

    # 1) Try API Key first
    if x_api_key:
        return _authenticate_via_api_key(request, x_api_key)

    # 2) Fall back to JWT Bearer
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=401, detail='Authentication required.')

    try:
        return verify_access_token(settings.auth_secret_key, credentials.credentials)
    except TokenVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _authenticate_via_api_key(request: Request, raw_key: str) -> AuthUser:
    from backend.app.services.api_key_service import lookup_api_key
    db = next(get_db_session())
    try:
        api_key_record = lookup_api_key(db, raw_key)
    finally:
        db.close()

    if api_key_record is None:
        raise HTTPException(status_code=401, detail='Invalid API key.')

    # Return AuthUser with the key owner's identity
    return AuthUser(username=api_key_record.owner_username, role=api_key_record.owner_role)
```

### Pattern 2: API Key Model Design
**What:** SHA-256 hashed key storage with prefix for identification.
**Example:**
```python
# models/api_key.py
class ApiKey(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    owner_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id"), nullable=False)
    owner_username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    owner_role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
```

### Pattern 3: Key Generation and Hashing
**What:** Generate with `secrets.token_urlsafe(48)`, hash with SHA-256, store prefix (first 8 chars) for admin identification.
**Example:**
```python
import secrets, hashlib

def generate_api_key() -> tuple[str, str, str]:
    """Returns (raw_key, key_prefix, key_hash)."""
    raw_key = secrets.token_urlsafe(48)  # ~64 chars
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_prefix, key_hash
```

### Pattern 4: Paginated Response Extension
**What:** Extend `success_response` to optionally include pagination metadata.
**Example:**
```python
def paginated_response(
    data: Any, total: int, page: int, page_size: int,
    message: str = "ok", status_code: int = 200
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        media_type="application/json; charset=utf-8",
        content={
            "success": True,
            "message": message,
            "data": jsonable_encoder(data),
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        },
    )
```

### Pattern 5: /docs Access Control
**What:** Override the default `/docs` and `/redoc` routes with admin-only middleware or custom route.
**Example:**
```python
# In main.py: disable default docs, add custom protected route
app = FastAPI(
    docs_url=None,  # Disable default
    redoc_url=None,
    openapi_url="/api/v1/openapi.json",  # Keep schema accessible
)

# Custom protected docs endpoint
from fastapi.openapi.docs import get_swagger_ui_html

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui(request: Request, user: AuthUser = Depends(require_role("admin"))):
    return get_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title=f"{settings.app_name} - API Documentation",
    )
```

### Pattern 6: Markdown API Documentation Generation
**What:** Walk the OpenAPI JSON schema and generate Markdown programmatically.
**Example:**
```python
# core/api_doc_generator.py
def generate_markdown_from_openapi(openapi_schema: dict) -> str:
    """Convert OpenAPI JSON schema to Markdown documentation."""
    lines = []
    lines.append(f"# {openapi_schema.get('info', {}).get('title', 'API')}")
    lines.append(f"\n{openapi_schema.get('info', {}).get('description', '')}\n")

    for tag in openapi_schema.get("tags", []):
        lines.append(f"## {tag['name']}")
        # Group paths by tag...

    for path, methods in openapi_schema.get("paths", {}).items():
        for method, detail in methods.items():
            lines.append(f"### {method.upper()} {path}")
            lines.append(f"{detail.get('summary', '')}")
            # Parameters, request body, responses...

    return "\n".join(lines)
```

### Anti-Patterns to Avoid
- **Separate API Key middleware:** Don't use a Starlette middleware for API Key auth. It would run before FastAPI dependency injection, making it impossible to share `AuthUser` with endpoint handlers. Use the existing dependency injection pattern instead.
- **Storing raw API keys:** Never store the plaintext key. Hash with SHA-256 and only return the raw key once at creation time.
- **Creating a separate `/api/external/` prefix:** Per D-06, external and internal APIs share the same `/api/v1/` endpoints. Don't create a separate route namespace.
- **Modifying existing endpoint signatures:** The dual-auth must be transparent. Don't add `api_key` parameters to individual endpoints.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API Key random generation | Custom random string | `secrets.token_urlsafe(48)` | Cryptographically secure, proper entropy |
| OpenAPI spec generation | Manual JSON/YAML authoring | FastAPI automatic generation | Already built-in, auto-syncs with code |
| Swagger UI | Custom documentation frontend | `get_swagger_ui_html` from FastAPI | Standard, maintained, feature-complete |
| Request validation | Manual param checking | Pydantic schemas + FastAPI | Already the project pattern |
| Password/key hashing | Custom crypto | `hashlib.sha256` for API keys | Standard library, well-tested |

**Key insight:** The entire OpenAPI/Swagger infrastructure is already built into FastAPI. This phase is about enrichment (Chinese descriptions, examples, tags) and access control, not building documentation from scratch.

## Common Pitfalls

### Pitfall 1: Circular Import in dependencies.py
**What goes wrong:** `dependencies.py` importing from `services/api_key_service.py` which imports from `models/` which imports from `dependencies.py`.
**Why it happens:** The API key lookup needs DB access, and `dependencies.py` is imported early.
**How to avoid:** Use lazy imports inside the `_authenticate_via_api_key` function (import inside function body), or inject the DB session via FastAPI's dependency system rather than creating one manually.
**Warning signs:** `ImportError` at startup.

### Pitfall 2: DB Session Leak in API Key Authentication
**What goes wrong:** Creating a new DB session inside `_authenticate_via_api_key` without proper cleanup.
**Why it happens:** The dependency `get_db` is a generator that FastAPI manages, but if you create a session manually in the auth check, it won't be cleaned up.
**How to avoid:** Use FastAPI's `Depends(get_db)` properly by making the DB session a parameter of `require_authenticated_user`, or use `request.state` to cache the looked-up key.
**Warning signs:** SQLite "database is locked" errors under load.

### Pitfall 3: /docs Protection Breaking OpenAPI Schema Access
**What goes wrong:** Protecting `/docs` but forgetting `/openapi.json` is also exposed; or protecting both and breaking the Swagger UI which needs to fetch the schema.
**Why it happens:** FastAPI serves the OpenAPI JSON at a separate URL.
**How to avoid:** Protect `/docs` and `/redoc` routes, but keep `/api/v1/openapi.json` accessible (or protect it with the same admin check). The Swagger UI HTML page fetches the JSON schema client-side, so both must be accessible to the same user.
**Warning signs:** Swagger UI loads but shows "Failed to load API definition."

### Pitfall 4: API Key Lookup Performance
**What goes wrong:** SHA-256 hashing every incoming API key and doing a full table scan.
**Why it happens:** The key_hash column isn't indexed, or the hash computation is done incorrectly.
**How to avoid:** Index `key_hash` column (UNIQUE constraint auto-indexes in SQLite). The SHA-256 computation is negligible (~microseconds). Also index `key_prefix` for optional fast rejection.
**Warning signs:** Slow API responses when using API Key auth.

### Pitfall 5: Existing Pagination Inconsistency
**What goes wrong:** Some endpoints already return pagination in `data` (e.g., `AuditLogListResponse` has `total, page, page_size` inside data). Adding a top-level `pagination` field creates two sources of truth.
**Why it happens:** D-10 says add pagination at response level, but existing endpoints embed it in data.
**How to avoid:** Adopt a consistent approach -- either move pagination to a top-level field on all list endpoints (breaking change) or keep it in `data` and add the same structure there. Recommendation: keep inside `data` to avoid breaking existing frontend code, and just ensure all list endpoints include `total, page, page_size`.
**Warning signs:** Frontend pagination breaks after API changes.

### Pitfall 6: Error Code Prefix Retrofit
**What goes wrong:** Trying to change all existing error codes in one pass breaks frontend error message mapping.
**Why it happens:** The frontend `getChineseErrorMessage` function maps error codes to Chinese messages.
**How to avoid:** Add the new prefix system for NEW error codes only. Existing codes like `"not_found"`, `"validation_error"` etc. remain as-is. Document the prefix convention for future endpoints.
**Warning signs:** Frontend error messages stop displaying correctly.

## Code Examples

### API Key CRUD Schema
```python
# schemas/api_key.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="API Key 名称")
    owner_id: str = Field(description="绑定用户 ID")

class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # Raw key, shown only once!
    key_prefix: str
    owner_username: str
    owner_role: str
    created_at: datetime

class ApiKeyRead(BaseModel):
    id: str
    name: str
    key_prefix: str
    owner_id: str
    owner_username: str
    owner_role: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyRead]
    total: int
```

### API Key Service
```python
# services/api_key_service.py
import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.api_key import ApiKey

class ApiKeyLimitExceededError(ValueError):
    pass

class ApiKeyNotFoundError(ValueError):
    pass

def generate_api_key() -> tuple[str, str, str]:
    raw_key = secrets.token_urlsafe(48)
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_prefix, key_hash

def create_api_key(db: Session, name: str, owner_id: str,
                   owner_username: str, owner_role: str) -> tuple[ApiKey, str]:
    # Check limit (D-03: max 5 per user)
    count = db.query(ApiKey).filter(
        ApiKey.owner_id == owner_id, ApiKey.is_active == True
    ).count()
    if count >= 5:
        raise ApiKeyLimitExceededError("Each user can have at most 5 active API keys.")

    raw_key, prefix, key_hash = generate_api_key()
    record = ApiKey(
        name=name, key_prefix=prefix, key_hash=key_hash,
        owner_id=owner_id, owner_username=owner_username, owner_role=owner_role,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, raw_key

def lookup_api_key(db: Session, raw_key: str) -> ApiKey | None:
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    record = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash, ApiKey.is_active == True
    ).first()
    if record:
        record.last_used_at = datetime.now(timezone.utc)
        db.commit()
    return record
```

### Chinese Description Pattern for Endpoints
```python
@router.get(
    '',
    summary="查询员工主数据列表",
    description="分页查询员工主数据，支持按姓名、地区、公司筛选。",
    response_description="员工主数据列表及分页信息",
)
def list_employee_masters_endpoint(...):
    ...
```

### Error Code Prefix Convention
```python
# New error codes follow module prefix pattern:
ERROR_CODES = {
    # AUTH module
    "AUTH_001": "认证失败",
    "AUTH_002": "API Key 无效",
    "AUTH_003": "API Key 已禁用",
    "AUTH_004": "API Key 数量已达上限",
    # EMPLOYEE module
    "EMPLOYEE_001": "员工不存在",
    # IMPORT module
    "IMPORT_001": "文件格式不支持",
    # EXPORT module
    "EXPORT_001": "导出任务未找到",
    # SYSTEM module
    "SYSTEM_001": "内部服务器错误",
}
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | Uses existing conftest.py at `tests/conftest.py` |
| Quick run command | `pytest tests/test_api_key.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | All core endpoints accessible | integration | `pytest tests/test_api_compatibility.py -x` | Exists (extend) |
| API-02 | OpenAPI/Swagger docs generated | integration | `pytest tests/test_api_docs.py -x` | Wave 0 |
| API-03 | Response format consistent | integration | `pytest tests/test_api_response_format.py -x` | Wave 0 |
| API-04 | API Key auth works for all endpoints | integration | `pytest tests/test_api_key_auth.py -x` | Wave 0 |
| AUTH-07 | API Key authentication mechanism | unit+integration | `pytest tests/test_api_key.py -x` | Wave 0 |
| AUTH-08 | Admin CRUD for API Keys | integration | `pytest tests/test_api_key.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_api_key.py tests/test_api_key_auth.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_api_key.py` -- covers AUTH-07, AUTH-08 (CRUD, limit, revoke)
- [ ] `tests/test_api_key_auth.py` -- covers API-04 (dual-auth, role inheritance)
- [ ] `tests/test_api_docs.py` -- covers API-02 (Swagger access, Markdown generation)
- [ ] `tests/test_api_response_format.py` -- covers API-03 (pagination, error codes)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT (already migrated in Phase 2) | AUTH-06 | No change needed |
| Separate external API routes | Shared routes with dual-auth | D-06 decision | Simplifies architecture |

**Deprecated/outdated:**
- None relevant -- all current libraries are up-to-date for this project's needs.

## Open Questions

1. **Pagination field location (top-level vs inside data)**
   - What we know: Existing endpoints like AuditLogListResponse embed `total, page, page_size` inside `data`. D-10 says "add pagination field in response."
   - What's unclear: Whether D-10 means top-level `pagination` sibling to `data`, or within `data`.
   - Recommendation: Keep inside `data` to avoid breaking existing frontend. The `AuditLogListResponse` pattern is already established. Ensure all list endpoints follow this pattern.

2. **API Key auth DB session management**
   - What we know: `require_authenticated_user` currently doesn't use a DB session. API Key lookup needs one.
   - What's unclear: Best way to inject DB session into the auth dependency without creating session leaks.
   - Recommendation: Add `db: Session = Depends(get_db)` to `require_authenticated_user` signature. FastAPI handles cleanup.

3. **Protecting /docs with admin auth**
   - What we know: D-16 requires admin-only access to /docs.
   - What's unclear: Whether this means JWT-based browser session or a simple approach.
   - Recommendation: Use a custom route that requires admin JWT Bearer token. Frontend can open `/docs` in a new tab with the token in the URL query param (or rely on Swagger UI's "Authorize" button). Alternatively, a simpler approach: check for admin JWT cookie or query param.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified). All tools and libraries are already installed in the project. This phase is purely code/config changes.

## Project Constraints (from CLAUDE.md)

- **Language:** React + FastAPI stack; all communication in Chinese, code/filenames in English
- **Data pipeline first:** Core data pipeline stability must not be compromised
- **Rules before LLM:** API system does not involve LLM
- **No fixed-position parsing:** Not relevant to this phase
- **Keep provenance:** Audit logs must trace API Key usage
- **Testing:** Must verify lint passes and build succeeds
- **Commit workflow:** Only commit after all validations pass

## Sources

### Primary (HIGH confidence)
- Project codebase: `backend/app/dependencies.py`, `backend/app/api/v1/router.py`, `backend/app/api/v1/responses.py`, `backend/app/core/auth.py`, `backend/app/main.py` -- direct code analysis
- FastAPI documentation (training knowledge) -- OpenAPI auto-generation, custom docs routes, dependency injection patterns
- Python stdlib documentation -- `secrets.token_urlsafe`, `hashlib.sha256`

### Secondary (MEDIUM confidence)
- FastAPI `get_swagger_ui_html` pattern for custom /docs route -- verified in FastAPI source code patterns from training data

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- extending existing well-understood patterns (dependencies.py, responses.py)
- Pitfalls: HIGH -- based on direct analysis of existing code patterns and known FastAPI behaviors

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable -- no fast-moving dependencies)
