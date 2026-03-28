# Phase 2: Authentication & RBAC - Research

**Researched:** 2026-03-27
**Domain:** Authentication, JWT tokens, password hashing, role-based access control in FastAPI
**Confidence:** HIGH

## Summary

This phase migrates the existing custom HMAC token system to PyJWT (HS256) and extends the two-role model (admin/hr) to three roles (admin/hr/employee). The current auth code in `backend/app/core/auth.py` is a clean, self-contained module (~130 lines) with manual base64 + HMAC signing. Replacing it with PyJWT simplifies token handling to two function calls (`jwt.encode` / `jwt.decode`) while keeping the same Bearer token format and payload structure (`sub`, `role`, `iat`, `exp`).

The current system authenticates admin/hr via hardcoded credentials in `Settings`. This phase adds a `User` database model for admin/hr accounts with bcrypt-hashed passwords, an employee triple-factor verification endpoint (employee_id + id_number + person_name against `EmployeeMaster`), and a `require_role` dependency factory for RBAC enforcement on routes.

**Primary recommendation:** Use PyJWT 2.12.1 for token operations, `pwdlib[bcrypt]` for password hashing (replaces abandoned passlib), and a simple closure-based `require_role()` dependency factory in `dependencies.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Employee verification via employee_id + id_number + person_name against EmployeeMaster table
- D-02: Employee gets temporary Token (role=employee) after verification
- D-03: Employee Token TTL = 30 minutes
- D-04: 5 failed attempts per IP or employee_id = 15 minute lockout
- D-05: Admin/HR accounts stored in DB (new User model), passwords bcrypt-hashed
- D-06: Employees do not need separate accounts, verify against EmployeeMaster
- D-07: First boot auto-creates default admin (admin/admin), prompt password change
- D-08: Admin can create/edit/disable HR and admin accounts via UI
- D-09: Migrate from custom HMAC to PyJWT (HS256), keep Bearer token format
- D-10: Admin/HR Token TTL = 8 hours
- D-11: Employee Token TTL = 30 minutes
- D-12: Token payload: sub (username or employee_id), role (admin/hr/employee), iat, exp
- D-13: Admin: user management + system config + all business functions
- D-14: HR: all business functions except user management and system settings
- D-15: Employee: personal social security data only, no access to others
- D-16: Auth layer only on API routes (dependencies.py), no changes to business logic
- D-17: Preserve auth_enabled switch, disabled = current behavior
- D-18: No new external services, keep SQLite
- D-19: pip install PyJWT + password hashing library automatically
- D-20: First boot auto-creates tables + default admin, no manual steps

### Claude's Discretion
- require_role dependency injection implementation approach
- Password strength validation rules
- Token refresh mechanism (whether refresh tokens are needed)
- Database migration strategy (Alembic migration details)

### Deferred Ideas (OUT OF SCOPE)
- Feishu OAuth login -- Phase 10
- API Key authentication -- Phase 9
- ID number masking -- Phase 3
- Audit logging -- Phase 3
- Rate limiting for non-employee endpoints -- Phase 3
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | Admin/HR login with username+password | PyJWT token issuance + pwdlib bcrypt verification; User model with hashed passwords |
| AUTH-02 | Employee verification via employee_id+id_number+name | New `/auth/employee-verify` endpoint; query EmployeeMaster; rate limiting with in-memory counter |
| AUTH-03 | Three-role RBAC (admin/hr/employee) | `require_role()` dependency factory; AuthRole extended to include 'employee' |
| AUTH-04 | Admin manages user accounts (create/edit/disable) | New `/users` CRUD endpoints; admin-only via `require_role('admin')` |
| AUTH-05 | Session persists after browser refresh | Bearer token in localStorage (already works); PyJWT tokens are self-contained |
| AUTH-06 | PyJWT replaces deprecated python-jose | PyJWT 2.12.1 with HS256; drop all custom HMAC code |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | 2.12.1 | JWT encode/decode with HS256 | Official FastAPI docs recommend it; actively maintained; simple API |
| pwdlib[bcrypt] | 0.3.0 | bcrypt password hashing | FastAPI official docs switched from passlib to pwdlib; passlib is abandoned and breaks on Python 3.13 |
| bcrypt | (transitive) | bcrypt C implementation | Installed as pwdlib[bcrypt] extra dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy 2.0.36 | (existing) | User model + queries | Already in stack, no new install |
| Alembic 1.14.0 | (existing) | Schema migration for User table | Already in stack, no new install |
| pydantic 2.10.3 | (existing) | Request/response schemas | Already in stack, no new install |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pwdlib | passlib[bcrypt] | passlib is abandoned, breaks on Python 3.13+; pwdlib is the official FastAPI replacement |
| pwdlib | bcrypt (direct) | Direct bcrypt works but pwdlib provides hash migration helpers and cleaner API |
| PyJWT | python-jose | python-jose is abandoned (last release 2022); PyJWT is the active standard |
| In-memory rate limiter | Redis/DB rate limiter | Overkill for single-server SQLite deployment; in-memory dict is sufficient |

**Installation:**
```bash
pip install PyJWT "pwdlib[bcrypt]"
```

**Version verification:** PyJWT 2.12.1 confirmed on PyPI (released 2026-03-13). pwdlib 0.3.0 confirmed on PyPI (released 2025-10-25).

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── core/
│   └── auth.py              # Rewrite: PyJWT encode/decode, AuthUser dataclass (add 'employee' role)
├── dependencies.py           # Add: require_role() factory, update require_authenticated_user
├── models/
│   └── user.py              # NEW: User SQLAlchemy model (admin/hr accounts)
├── schemas/
│   └── auth.py              # Extend: add employee verify request/response, user CRUD schemas
├── services/
│   └── user_service.py      # NEW: user CRUD + password hashing + default admin seeding
├── api/v1/
│   ├── auth.py              # Extend: add employee-verify endpoint
│   └── users.py             # NEW: user management CRUD endpoints (admin-only)
├── bootstrap.py             # Extend: call seed_default_admin on startup
└── core/
    └── config.py            # Extend: add JWT_SECRET_KEY (or reuse auth_secret_key)
```

### Pattern 1: PyJWT Token Issuance/Verification
**What:** Replace custom HMAC with two PyJWT calls
**When to use:** All token creation and validation
**Example:**
```python
# Source: PyJWT official docs + FastAPI tutorial
import jwt
from datetime import datetime, timedelta, timezone

def issue_access_token(secret_key: str, sub: str, role: str, expire_minutes: int) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expire_minutes)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token, expires_at

def verify_access_token(secret_key: str, token: str) -> dict:
    # jwt.decode automatically checks exp claim
    return jwt.decode(token, secret_key, algorithms=["HS256"])
```

### Pattern 2: require_role Dependency Factory
**What:** Closure that returns a FastAPI dependency checking user role
**When to use:** Protecting routes by required role(s)
**Example:**
```python
# Source: FastAPI dependency injection patterns
from fastapi import Depends, HTTPException, status

def require_role(*allowed_roles: str):
    """Dependency factory: returns a dependency that enforces role membership."""
    def dependency(user: AuthUser = Depends(require_authenticated_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized for this resource.",
            )
        return user
    return dependency

# Usage in router:
# dependencies=[Depends(require_role("admin"))]
# dependencies=[Depends(require_role("admin", "hr"))]
```

### Pattern 3: Password Hashing with pwdlib
**What:** Hash and verify passwords using bcrypt via pwdlib
**When to use:** User account creation, login verification
**Example:**
```python
# Source: pwdlib docs + FastAPI official tutorial
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
# For bcrypt specifically:
# from pwdlib.hashers.bcrypt import BcryptHasher
# password_hash = PasswordHash((BcryptHasher(),))

# Hash
hashed = password_hash.hash("plaintext_password")

# Verify
is_valid = password_hash.verify("plaintext_password", hashed)
```

### Pattern 4: Employee Triple-Factor Verification
**What:** Verify employee identity by matching three fields against EmployeeMaster
**When to use:** Employee login (not username/password, but identity verification)
**Example:**
```python
def verify_employee(db: Session, employee_id: str, id_number: str, person_name: str) -> EmployeeMaster | None:
    return db.query(EmployeeMaster).filter(
        EmployeeMaster.employee_id == employee_id.strip(),
        EmployeeMaster.id_number == id_number.strip(),
        EmployeeMaster.person_name == person_name.strip(),
        EmployeeMaster.active == True,
    ).first()
```

### Pattern 5: In-Memory Rate Limiter
**What:** Dict-based rate limiter for employee verification failures
**When to use:** Prevent brute-force enumeration of employee_id + id_number combinations
**Example:**
```python
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

@dataclass
class FailureRecord:
    count: int = 0
    locked_until: float = 0.0

class RateLimiter:
    def __init__(self, max_failures: int = 5, lockout_seconds: int = 900):
        self._records: dict[str, FailureRecord] = {}
        self._lock = Lock()
        self._max_failures = max_failures
        self._lockout_seconds = lockout_seconds

    def is_locked(self, key: str) -> bool:
        with self._lock:
            rec = self._records.get(key)
            if rec and rec.locked_until > time.time():
                return True
            return False

    def record_failure(self, key: str) -> bool:
        """Returns True if now locked."""
        with self._lock:
            rec = self._records.setdefault(key, FailureRecord())
            rec.count += 1
            if rec.count >= self._max_failures:
                rec.locked_until = time.time() + self._lockout_seconds
                return True
            return False

    def reset(self, key: str) -> None:
        with self._lock:
            self._records.pop(key, None)
```

### Pattern 6: Default Admin Seeding on Startup
**What:** Create default admin user in DB if no admin exists
**When to use:** First boot / empty database
**Example:**
```python
# In bootstrap.py or user_service.py, called from lifespan
def seed_default_admin(db: Session) -> None:
    from backend.app.models.user import User
    existing = db.query(User).filter(User.role == "admin").first()
    if existing:
        return
    admin = User(
        username="admin",
        hashed_password=password_hash.hash("admin"),
        role="admin",
        display_name="Default Admin",
        must_change_password=True,
    )
    db.add(admin)
    db.commit()
```

### Anti-Patterns to Avoid
- **Storing plaintext passwords in config:** The current system stores passwords in Settings. The new system MUST hash passwords in DB. Remove `admin_login_password` and `hr_login_password` from Settings after migration.
- **Checking role with string comparison at every endpoint:** Use the `require_role()` dependency factory at the router level, not inline checks in handler bodies.
- **Skipping timing-safe comparison for employee verification:** Use `hmac.compare_digest` for id_number comparison or at minimum ensure constant-time comparison to prevent timing attacks.
- **Forgetting auth_enabled bypass:** Every new auth dependency must check `settings.auth_enabled` and return `default_authenticated_user()` when disabled.
- **Importing `jwt` vs `PyJWT`:** The import is `import jwt` (not `import PyJWT`). Ensure `PyJWT` is installed, NOT the conflicting `jwt` package. They share the import name.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT encode/decode | Custom base64+HMAC (current) | PyJWT `jwt.encode()` / `jwt.decode()` | Handles exp validation, algorithm enforcement, proper base64url, header generation |
| Password hashing | Custom bcrypt wrapper | pwdlib `PasswordHash` | Handles salt generation, cost factor, hash migration, constant-time comparison |
| Token expiry validation | Manual `exp` timestamp check | PyJWT automatic exp claim validation | `jwt.decode()` raises `ExpiredSignatureError` automatically |
| Bearer token extraction | Custom header parsing | FastAPI `HTTPBearer` (already used) | Handles scheme validation, auto_error, OpenAPI docs |

**Key insight:** The current codebase already implements JWT-like functionality manually (base64 payload + HMAC signature). PyJWT does exactly this but handles edge cases (padding, algorithm headers, claim validation) that the custom code skips.

## Common Pitfalls

### Pitfall 1: PyJWT vs jwt Package Conflict
**What goes wrong:** `pip install jwt` installs a DIFFERENT package that also uses `import jwt`. If both are installed, imports break.
**Why it happens:** PyPI has both `jwt` and `PyJWT` packages sharing the `jwt` namespace.
**How to avoid:** Always `pip install PyJWT`. In requirements.txt use `PyJWT==2.12.1`. Check with `pip show PyJWT` not `pip show jwt`.
**Warning signs:** `AttributeError: module 'jwt' has no attribute 'encode'` or unexpected decode behavior.

### Pitfall 2: passlib Abandoned -- Use pwdlib
**What goes wrong:** passlib breaks on Python 3.13+ due to removed `crypt` module. requirements.server.txt already lists `passlib[bcrypt]`.
**Why it happens:** passlib last release was 2022. Python 3.13 removed the `crypt` module passlib depends on.
**How to avoid:** Use `pwdlib[bcrypt]` instead. Update requirements.server.txt to replace passlib.
**Warning signs:** `ImportError: cannot import name 'crypt'` on Python 3.13+.

### Pitfall 3: Forgetting auth_enabled Bypass
**What goes wrong:** New auth dependencies (require_role) reject requests when auth is disabled, breaking existing functionality.
**Why it happens:** New code doesn't check `settings.auth_enabled`.
**How to avoid:** `require_role()` must delegate to `require_authenticated_user()` which already handles the bypass. Chain dependencies, don't duplicate the bypass logic.
**Warning signs:** 401 errors in development when auth_enabled=false.

### Pitfall 4: Employee Token Leaking Others' Data
**What goes wrong:** Employee gets a valid token but API endpoints return all records, not just their own.
**Why it happens:** Data filtering by employee_id is not implemented at the query layer.
**How to avoid:** This is a Phase 5 (PORTAL) concern, but the token MUST include the correct `sub` (employee_id) so that downstream filters can work. Verify token sub matches the employee.
**Warning signs:** Employee API returning lists instead of filtered results.

### Pitfall 5: Race Condition in Rate Limiter
**What goes wrong:** Concurrent requests bypass the failure count.
**Why it happens:** Non-thread-safe dict access in ASGI/uvicorn with multiple workers.
**How to avoid:** Use `threading.Lock` in the rate limiter. For single-worker uvicorn (default for SQLite), this is sufficient. For multi-worker, would need shared state (but SQLite already constrains to single writer).
**Warning signs:** Lockout not triggering after exactly 5 failures.

### Pitfall 6: Timing Attack on Employee Verification
**What goes wrong:** Attacker can determine which of the three fields (employee_id, id_number, name) is wrong based on response time.
**Why it happens:** Short-circuit evaluation in database query returns faster when employee_id doesn't match.
**How to avoid:** Always execute the full query. If no result, do not indicate which field failed. Return generic "Verification failed" message.
**Warning signs:** Measurable response time differences between valid employee_id with wrong name vs invalid employee_id.

### Pitfall 7: Default Admin Password Not Prompted for Change
**What goes wrong:** System runs in production with default admin/admin credentials indefinitely.
**Why it happens:** `must_change_password` flag exists but frontend doesn't enforce it.
**How to avoid:** Add `must_change_password` boolean to User model. Return it in login response. Frontend should redirect to password change page. Backend should reject non-password-change requests from must_change_password users (this can be Phase 3 enforcement; Phase 2 just sets the flag and returns it).
**Warning signs:** Default admin still active in production after months.

## Code Examples

### Migration: Current HMAC to PyJWT

```python
# BEFORE (current auth.py - lines 51-65):
def issue_access_token(settings, user):
    payload = {"sub": user.username, "role": user.role, "iat": issued_at, "exp": exp}
    payload_segment = _encode_segment(payload)
    signature_segment = _sign_segment(payload_segment, settings.auth_secret_key)
    return f"{payload_segment}.{signature_segment}", expires_at

# AFTER (new auth.py):
import jwt

def issue_access_token(secret_key: str, sub: str, role: str, expire_minutes: int) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": sub, "role": role, "iat": datetime.now(timezone.utc), "exp": expires_at}
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token, expires_at
```

### Migration: Current verify to PyJWT

```python
# BEFORE (current auth.py - lines 68-91):
def verify_access_token(settings, token):
    payload_segment, signature_segment = token.split(".", maxsplit=1)
    expected = _sign_segment(payload_segment, settings.auth_secret_key)
    if not hmac.compare_digest(signature_segment, expected):
        raise TokenVerificationError(...)
    payload = _decode_segment(payload_segment)
    # manual exp check...
    return AuthUser(username=..., role=...)

# AFTER (new auth.py):
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

def verify_access_token(secret_key: str, token: str) -> AuthUser:
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise TokenVerificationError("Authentication token has expired.")
    except InvalidTokenError:
        raise TokenVerificationError("Authentication token is invalid.")
    return AuthUser(
        username=payload.get("sub", ""),
        role=_normalize_role(payload.get("role", "")),
    )
```

### User Model

```python
# backend/app/models/user.py
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'admin' | 'hr'
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

### require_role Dependency

```python
# backend/app/dependencies.py (addition)
from typing import Sequence

def require_role(*allowed_roles: str):
    def _dependency(user: AuthUser = Depends(require_authenticated_user)) -> AuthUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return user
    return _dependency

# Usage in router.py:
api_router.include_router(users_router, dependencies=[Depends(require_role("admin"))])
api_router.include_router(aggregate_router, dependencies=[Depends(require_role("admin", "hr"))])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| passlib[bcrypt] | pwdlib[bcrypt] | 2024 | FastAPI official docs updated; passlib breaks on Python 3.13+ |
| python-jose | PyJWT | 2023-2024 | python-jose abandoned; PyJWT is the active standard |
| Custom HMAC tokens | PyJWT HS256 | This migration | Removes ~60 lines of hand-rolled crypto code |
| Hardcoded credentials in config | DB-stored bcrypt hashes | This migration | Supports user management, password changes |

**Deprecated/outdated:**
- `passlib`: Abandoned, breaks on Python 3.13+. Use `pwdlib` instead.
- `python-jose`: Abandoned (last release 2022). Use `PyJWT` instead. Note: requirements.server.txt still lists `python-jose[cryptography]` -- must be removed.

## Open Questions

1. **Token Refresh Mechanism**
   - What we know: D-10 says 8hr TTL for admin/hr, D-11 says 30min for employee. No refresh token mentioned.
   - What's unclear: Should admin/hr sessions auto-extend, or must they re-login after 8 hours?
   - Recommendation: No refresh token for Phase 2. 8hr TTL covers a full workday. Employee 30min is intentionally short. Add refresh tokens in Phase 3 if needed.

2. **Password Strength Rules**
   - What we know: D-07 says default admin is admin/admin with prompt to change.
   - What's unclear: What minimum password requirements for created accounts?
   - Recommendation: Minimum 8 characters for admin/hr accounts. No complexity rules beyond length (users tend to work around complex rules poorly). Enforce on the schema validation level.

3. **Backward Compatibility of Existing Tokens**
   - What we know: Current tokens are custom HMAC format (base64_payload.base64_hmac). New tokens are standard JWT (header.payload.signature -- 3 segments).
   - What's unclear: Should old tokens be accepted during transition?
   - Recommendation: No backward compatibility needed. Token TTL is 8hr max. Deploy, and existing sessions expire naturally. The token format change (2 segments to 3 segments) means old tokens will fail `jwt.decode()` immediately -- which is correct behavior.

4. **Alembic Migration vs create_all**
   - What we know: Alembic is in requirements but no migration files were found in the project.
   - What's unclear: Does the project use `Base.metadata.create_all()` or Alembic migrations?
   - Recommendation: Check if `create_all()` is called at startup. If so, adding the User model to the imports will auto-create the table. Generate an Alembic migration as well for documentation purposes, but the auto-create handles first-boot.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | none -- see Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | Admin/HR login with username+password returns JWT | unit | `pytest tests/test_auth.py::test_admin_login -x` | Wave 0 |
| AUTH-01 | Invalid credentials return 401 | unit | `pytest tests/test_auth.py::test_login_invalid_credentials -x` | Wave 0 |
| AUTH-02 | Employee verification with valid triple returns token | unit | `pytest tests/test_auth.py::test_employee_verify_success -x` | Wave 0 |
| AUTH-02 | Employee verification rate limit after 5 failures | unit | `pytest tests/test_auth.py::test_employee_rate_limit -x` | Wave 0 |
| AUTH-03 | require_role enforces admin-only routes | unit | `pytest tests/test_auth.py::test_require_role_admin -x` | Wave 0 |
| AUTH-03 | require_role allows multi-role access | unit | `pytest tests/test_auth.py::test_require_role_multi -x` | Wave 0 |
| AUTH-04 | Admin can create user | integration | `pytest tests/test_users.py::test_create_user -x` | Wave 0 |
| AUTH-04 | Non-admin cannot manage users | integration | `pytest tests/test_users.py::test_non_admin_forbidden -x` | Wave 0 |
| AUTH-05 | Token decode works with valid JWT | unit | `pytest tests/test_auth.py::test_token_roundtrip -x` | Wave 0 |
| AUTH-06 | PyJWT token format (3 segments) | unit | `pytest tests/test_auth.py::test_jwt_format -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` -- shared fixtures (test DB session, test client, test settings with auth_enabled=True)
- [ ] `tests/test_auth.py` -- covers AUTH-01, AUTH-02, AUTH-03, AUTH-05, AUTH-06
- [ ] `tests/test_users.py` -- covers AUTH-04
- [ ] Framework config: `pytest.ini` or `pyproject.toml [tool.pytest]` section
- [ ] No existing project-level test files found -- entire test infrastructure needs creation

## Project Constraints (from CLAUDE.md)

- Tech stack: React + FastAPI + SQLite, do not change
- Auth layer only on API routes (dependencies.py), do not modify business logic (parsers, exporters, etc.)
- Preserve `auth_enabled` switch -- disabled means current behavior unchanged
- Salary template export logic must not be touched
- Testing: pytest for backend; no frontend test framework detected
- Build commands: `uvicorn backend.app.main:app --reload` (backend), `npm run dev` (frontend)
- Agent workflow: read CLAUDE.md/task.json, select task, implement, test, update progress.txt, commit

## Sources

### Primary (HIGH confidence)
- [PyJWT PyPI](https://pypi.org/project/PyJWT/) - Version 2.12.1 confirmed, HS256 usage pattern
- [FastAPI Official JWT Tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) - pwdlib recommendation, dependency pattern
- [pwdlib PyPI](https://pypi.org/project/pwdlib/) - Version 0.3.0 confirmed, bcrypt usage
- Codebase: `backend/app/core/auth.py` - Current HMAC implementation analyzed
- Codebase: `backend/app/dependencies.py` - Current require_authenticated_user pattern
- Codebase: `backend/app/models/employee_master.py` - EmployeeMaster schema for employee verification
- Codebase: `backend/app/bootstrap.py` - Startup logic, auth guardrails

### Secondary (MEDIUM confidence)
- [FastAPI RBAC patterns](https://app-generator.dev/docs/technologies/fastapi/rbac.html) - require_role dependency factory pattern
- [passlib abandonment discussion](https://github.com/fastapi/fastapi/discussions/11773) - passlib deprecation confirmed

### Tertiary (LOW confidence)
- Rate limiter thread safety under uvicorn -- single worker with SQLite is standard, but multi-worker edge case needs validation at implementation time

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyJWT and pwdlib versions verified on PyPI, FastAPI official docs confirm the pattern
- Architecture: HIGH - Current codebase patterns are clear, migration path is straightforward
- Pitfalls: HIGH - PyJWT/jwt conflict, passlib abandonment, auth_enabled bypass are well-documented issues
- Rate limiting: MEDIUM - In-memory approach is correct for single-server SQLite, but threading edge cases exist

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable domain, libraries are mature)
