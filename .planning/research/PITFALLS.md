# Domain Pitfalls

**Domain:** Social insurance & housing fund management system (Excel merge tool -> management platform)
**Researched:** 2026-03-27

---

## Critical Pitfalls

Mistakes that cause rewrites, data breaches, or major regressions.

### Pitfall 1: Auth Retrofit Breaks Existing Unauthenticated Workflows

**What goes wrong:** Adding authentication to an app that currently works without it causes the working upload/parse/export pipeline to break. The employees router is already inconsistently protected -- it lacks router-level `dependencies=[Depends(require_authenticated_user)]` while most other routers have it. The self-service endpoint at `/employees/self-service/query` is completely unauthenticated. When adding a third role ("employee"), the existing two-role system (`admin`/`hr` as a `Literal` type) needs to expand, and every `_normalize_role`, `AuthUser`, and role-check callsite must be updated.

**Why it happens:** The current auth is a bolt-on with hardcoded credentials in `config.py` (`admin123`/`hr123`) and a custom HMAC token scheme. There are ghost dependencies (`python-jose`, `passlib`) in `requirements.server.txt` that suggest an abandoned JWT migration. Teams add the third role and miss callsites, or they add middleware-level auth and break the streaming NDJSON endpoints that the frontend depends on.

**Consequences:**
- Working Salary template export pipeline breaks because auth middleware interferes with streaming responses
- Employee self-service is either left wide open (PII exposure) or locked behind credentials employees don't have
- Role checks scattered across individual endpoints rather than router-level, leading to forgotten unprotected routes

**Prevention:**
1. Use router-level `dependencies=` for auth, not per-endpoint decorators -- this is already the pattern for most routers, just not `employees_router`. Fix the inconsistency first.
2. Expand `AuthRole` Literal type to include `'employee'` and audit every usage with `grep -r "AuthRole\|admin.*hr\|role.*admin"`.
3. Keep the employee "login" as a separate mechanism (ID number + name verification) that issues a restricted token, not a full user/password account.
4. Test the NDJSON streaming aggregate endpoint specifically after adding auth -- streaming responses + auth middleware is a known conflict point in FastAPI.
5. Replace the custom HMAC token with PyJWT before adding the third role. The custom scheme has no `iss`/`aud` claims and no refresh tokens, which matters once employees are logging in.

**Detection:** Any existing integration test that calls the aggregate or export endpoints without a token should fail after auth changes. If they still pass, auth was applied inconsistently.

**Phase:** Auth & Roles phase (should be early, before frontend redesign)

---

### Pitfall 2: Frontend Redesign Accidentally Breaks Backend Contract

**What goes wrong:** The frontend is rebuilt with new UI (Feishu-inspired design), new routing, and new state management. During the rewrite, the API contract drifts: request body shapes change, the NDJSON streaming protocol is replaced with a simpler polling approach "temporarily," or the upload flow changes from multipart to a different pattern. The Salary template export -- which works perfectly -- breaks because someone refactored the frontend export trigger.

**Why it happens:** Frontend redesigns create pressure to "clean up" everything. Developers see the old API calls and decide to "improve" them. The NDJSON streaming pattern (`/api/v1/aggregate/stream`) is non-trivial to re-implement in a new frontend framework/state management approach. There are no frontend tests (zero test files exist), so regressions are invisible.

**Consequences:**
- Salary template export (the one thing that works perfectly and MUST NOT be touched) breaks
- Streaming progress feedback regresses to polling, losing real-time UX
- Months of working pipeline integration lost to a UI rewrite

**Prevention:**
1. Create an API contract snapshot (OpenAPI spec export) BEFORE starting frontend work. Compare against it during development.
2. Write E2E smoke tests for the critical path (upload -> parse -> export Salary template) BEFORE redesigning anything. These become the safety net.
3. Treat the frontend redesign as a new app that consumes the existing API. Do NOT modify any backend endpoint signatures during the frontend phase.
4. Keep the old frontend accessible at a `/legacy` route until the new frontend passes all smoke tests against the same API.
5. The NDJSON streaming consumer code should be extracted into a standalone hook/utility early -- it is the most fragile integration point.

**Detection:** If any backend endpoint signature changes during the frontend redesign phase, something went wrong. If the Salary export test fails, stop immediately.

**Phase:** Frontend redesign phase. Must be sequenced AFTER auth is stable, AFTER Tool template fix is done. The Salary export E2E test must exist before this phase begins.

---

### Pitfall 3: Feishu Bitable Sync Becomes an Uncontrollable Data Consistency Problem

**What goes wrong:** Bidirectional sync with Feishu Bitable sounds simple ("push data to Feishu, pull changes back") but creates a distributed data consistency nightmare. Feishu Bitable has strict rate limits (50 writes/sec, max 1000 records per batch insert; 20 reads/sec, max 50 records per query). A typical monthly batch with 6 regions and hundreds of employees easily exceeds these limits. Worse, "bidirectional" means conflicts: if someone edits a record in Feishu and someone else edits the same record in the system, which wins?

**Why it happens:** Teams underestimate Feishu API constraints:
- Token expiry: `user_access_token` expires every 2 hours, `tenant_access_token` every 2 hours. Forgetting to refresh = silent sync failures.
- Rate limits are per-app, not per-user. Multiple HR users triggering sync simultaneously exhaust the quota.
- Feishu Bitable field types are restrictive -- they don't map 1:1 to the system's canonical fields. Currency fields, date formats, and multi-line text behave differently.
- WebSocket events from Feishu can be delivered multiple times, causing duplicate processing.
- The Feishu China platform (`feishu.cn`) and international Lark platform (`larksuite.com`) are completely separate -- apps built for one do not work on the other.

**Consequences:**
- Partial sync failures leave Feishu and system out of sync with no way to reconcile
- Rate limit hits during large batch pushes cause data loss (records that didn't make it)
- Duplicate records from retry logic or duplicate WebSocket events
- HR manually "fixes" data in Feishu, creating conflicts that the system doesn't know about

**Prevention:**
1. Start with ONE direction first: system -> Feishu (push only). Get this reliable before attempting pull.
2. Implement a sync log table that records every push/pull operation with status, timestamp, and Feishu record ID. This is the reconciliation source of truth.
3. Build rate limiting into the sync client: queue operations, batch them (max 1000 per request for inserts), and respect the 50 req/sec ceiling with backpressure.
4. Use `tenant_access_token` (app-level) rather than `user_access_token` for sync operations -- longer-lived and doesn't require user interaction. Implement automatic refresh 5 minutes before expiry.
5. Make Feishu sync idempotent: use a unique key (e.g., `id_number + billing_period`) to upsert, never blind-insert.
6. For "bidirectional," define clear ownership: system owns insurance data (Feishu is read-only for these fields), Feishu owns annotations/comments (system is read-only for those). Never allow both sides to write the same field.
7. Defer WebSocket/event-driven pull until push is proven stable. Start with scheduled pull (every N minutes) which is debuggable.

**Detection:** If the sync log shows any failed operations that weren't retried, or if record counts differ between system and Feishu after a full sync, the consistency model is broken.

**Phase:** Feishu integration should be its own dedicated phase, sequenced AFTER auth and AFTER the core data pipeline is stable. Never bundle it with other work.

---

### Pitfall 4: PII Exposure Through Inadequate Access Controls on Social Insurance Data

**What goes wrong:** Social insurance data contains some of the most sensitive PII in China: national ID numbers (`id_number`), social security numbers, salary-derived payment bases, and medical insurance details. Under PIPL (Personal Information Protection Law), ID numbers and financial data are classified as sensitive personal information with heightened processing requirements. The current system has an unauthenticated endpoint that returns PII, default credentials, and no audit logging.

**Why it happens:** The system started as an internal Excel merge tool where security wasn't a priority. Now it's becoming a management platform with employee self-service access, REST API, and Feishu sync -- dramatically expanding the attack surface. Specific existing vulnerabilities from CONCERNS.md:
- Self-service endpoint has no authentication (exposes name + ID number matching without any gate)
- Default passwords `admin123`/`hr123` are active in "local" mode, which is the default
- No rate limiting on the self-service query (enables ID number enumeration)
- No audit trail for who accessed whose data
- Uploaded Excel files accumulate forever in `data/uploads/` with no cleanup

**Consequences:**
- PIPL non-compliance: mandatory compliance audits became effective May 1, 2025. Processing sensitive PI without proper safeguards can result in fines up to 50 million RMB or 5% of annual revenue.
- ID number enumeration attack: attacker can cycle through ID number patterns on the unauthenticated endpoint to extract employee data
- Data retention violation: social insurance records stored indefinitely without purpose limitation or deletion policy

**Prevention:**
1. **Immediate (before any new feature work):**
   - Add authentication to the self-service endpoint
   - Add rate limiting (max 5 queries per minute per IP) to self-service
   - Remove or disable default credentials in any non-explicitly-local deployment
   - Add audit logging: every data access must record who, when, what records, from which IP

2. **During auth phase:**
   - Employee self-service should require ID number + name + a verification code (sent to their registered contact), not just ID number + name alone
   - Implement field-level access control: employees see only their own records; HR sees all records but with ID numbers partially masked in the UI; only admin sees unmasked data
   - Add a `data_access_log` table: `(user_id, action, resource, record_ids, ip, timestamp)`

3. **During Feishu sync phase:**
   - ID numbers must be masked or encrypted before pushing to Feishu Bitable (Feishu storage is outside your direct control)
   - Define data retention: auto-delete uploaded files after 30 days, archive processed data after 12 months

4. **Ongoing:**
   - Implement data export logging (who downloaded what template, when)
   - Add a `/api/v1/audit/log` endpoint for admins to review access history

**Detection:** If you cannot answer "who accessed employee X's data in the last 30 days" from system logs, the audit trail is insufficient. If the self-service endpoint responds to requests without any form of authentication, the PII gate is missing.

**Phase:** PII protections are cross-cutting. Rate limiting and audit logging should be in the auth phase. Field-level masking should be in the frontend redesign phase. Feishu data masking should be in the Feishu integration phase.

---

## Moderate Pitfalls

### Pitfall 5: Tool Template Fix Accidentally Breaks Salary Template

**What goes wrong:** The Tool template export has field mapping issues that need fixing. The Salary template export works perfectly. Both templates share code in `template_exporter.py` (1160 lines, a single monolithic file). Fixing the Tool template changes shared logic and regresses the Salary template.

**Prevention:**
1. Split `template_exporter.py` into three modules BEFORE fixing the Tool template: `salary_exporter.py`, `tool_exporter.py`, `export_utils.py`. The split itself should be a zero-behavior-change refactor with existing tests passing.
2. Write a Salary template regression test using real production templates (not synthetic fixtures) before touching any export code.
3. The Tool template fix should only touch `tool_exporter.py` after the split.

**Detection:** Run the Salary template export test after every change to export code. If it fails, revert immediately.

**Phase:** This must be the FIRST phase. It de-risks everything else.

---

### Pitfall 6: SQLite Concurrency Collapse Under Multi-User Access

**What goes wrong:** The system moves from single-user (one HR person running batch imports) to multi-user (admin + HR + employees querying simultaneously). SQLite with WAL mode supports concurrent reads but only one writer at a time. The current busy timeout is 120 seconds. When HR triggers a batch import (heavy write) while employees are querying (reads that become writes for audit logs), everything queues.

**Prevention:**
1. Accept SQLite for this milestone -- the project constraint says single company use. But design the data access layer so PostgreSQL migration is a config change, not a rewrite.
2. Move batch import writes to a background task with a dedicated connection, not the request connection.
3. Use read-only connections for employee queries: `engine.connect().execution_options(sqlite_read_only=True)`.
4. If audit logging causes write contention, write audit logs to a separate SQLite database file.

**Detection:** If employee self-service queries take >2 seconds during a batch import, concurrency is the bottleneck.

**Phase:** Addressed during auth phase (when multi-user access is introduced).

---

### Pitfall 7: Feishu OAuth Login vs. Internal Auth Creates Identity Split

**What goes wrong:** The system implements both internal auth (username/password for admin/HR) and Feishu OAuth (for employees or all users). Two identity systems create confusion: which login does a user use? What happens when a Feishu user doesn't have a matching internal account? What if someone logs in via Feishu but their Feishu identity doesn't map to an employee record?

**Prevention:**
1. Make Feishu OAuth optional and additive, not a replacement. Internal auth stays primary.
2. Link Feishu identity to employee records via a `feishu_user_id` column on the employee table, populated during first OAuth login by matching email or phone number.
3. Never create a "new user" automatically from Feishu OAuth -- require admin approval or pre-registration.
4. If Feishu OAuth is used for employee self-service, the flow is: Feishu login -> look up `feishu_user_id` in employee table -> if found, issue restricted token -> if not found, show "contact HR" message. No silent account creation.

**Detection:** If users report "I can log in via Feishu but see no data" or "I have two accounts," the identity linking is broken.

**Phase:** Feishu integration phase, specifically after basic auth is working.

---

### Pitfall 8: Normalization Service Becomes Unmaintainable Before New Regions Are Added

**What goes wrong:** `normalization_service.py` is already 863 lines with Wuhan and Changsha special-case logic hardcoded. The next milestone adds more regions or housing fund variants. Each new region adds another 50-100 lines of special cases to a file that's already hard to test in isolation.

**Prevention:**
1. Extract region-specific normalizers into a strategy pattern: `backend/app/services/region_normalizers/{region}.py` with a common interface.
2. Do this refactor BEFORE adding any new region or housing fund logic.
3. Each region normalizer should be independently testable with its own sample files.

**Detection:** If `normalization_service.py` exceeds 1000 lines, the refactor was skipped.

**Phase:** Should happen during the Tool template fix phase as preparatory cleanup.

---

## Minor Pitfalls

### Pitfall 9: CORS Configuration Breaks After Frontend Redeploy

**What goes wrong:** The frontend is rebuilt and deployed to a new URL or port. The backend CORS config still points to the old origin. All API calls fail with opaque CORS errors that are hard to debug.

**Prevention:**
- Make CORS origins configurable via environment variable (already partially done in `config.py`)
- Add the new frontend origin to CORS config BEFORE deploying the new frontend
- Never use `allow_origins=["*"]` with `allow_credentials=True` -- this is already a noted concern

**Detection:** Frontend shows "network error" on all API calls after deployment.

**Phase:** Frontend redesign phase.

---

### Pitfall 10: Alembic Migrations Drift From Actual Schema

**What goes wrong:** The SQLite database (`data/app.db`) is in version control and has been modified directly. Alembic migrations exist but may not reflect the actual schema. Adding new tables for auth (users, roles, sessions, audit_log) via Alembic when the migration history doesn't match reality causes migration failures.

**Prevention:**
1. Before writing any new migration, dump the current schema with `sqlite3 data/app.db .schema` and compare to the latest Alembic migration state.
2. If they diverge, create a "stamp" migration that marks current state as baseline.
3. Remove `data/app.db` from version control (add to `.gitignore`). It's already showing as modified in git status.

**Detection:** `alembic upgrade head` fails or produces a different schema than the running database.

**Phase:** Auth phase (first migration will add user/role tables).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Tool template fix | Salary template regression (#5) | Split exporter first, regression test before any fix |
| Auth & roles | Inconsistent route protection (#1) | Router-level deps, audit all endpoints |
| Auth & roles | SQLite write contention (#6) | Background tasks, read-only connections |
| Auth & roles | PII exposure during transition (#4) | Rate limit + audit log as first commits |
| Auth & roles | Migration drift (#10) | Schema baseline before first migration |
| Frontend redesign | Backend contract drift (#2) | API snapshot, E2E smoke tests as gate |
| Frontend redesign | CORS breakage (#9) | Environment-driven CORS config |
| Feishu integration | Rate limit data loss (#3) | Queue + batch + sync log table |
| Feishu integration | Identity split (#7) | Feishu OAuth as additive, not primary |
| Feishu integration | PII in Feishu storage (#4) | Mask ID numbers before push |
| New regions / housing fund | Normalization bloat (#8) | Strategy pattern extraction first |

---

## Sources

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI Auth: Router-Level Dependencies vs Middleware](https://medium.com/@anto18671/efficiency-of-using-dependencies-on-router-in-fastapi-c3b288ac408b)
- [Feishu Bitable API Overview](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview)
- [Feishu Bitable Rate Limits](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-structure)
- [Feishu Server SDK](https://open.feishu.cn/document/server-docs/server-side-sdk)
- [PIPL Compliance Guide - China Briefing](https://www.china-briefing.com/doing-business-guide/china/company-establishment/pipl-personal-information-protection-law)
- [Sensitive Personal Data Standards GB/T 45574-2025](https://www.china-briefing.com/news/sensitive-personal-data-in-china-guidelines/)
- [China Data Protection 2025 Review - Bird & Bird](https://www.twobirds.com/en/insights/2026/china/china-data-protection-and-cybersecurity-annual-review-of-2025-and-outlook-for-2026)
- [Frontend Migration Guide - Frontend Mastery](https://frontendmastery.com/posts/frontend-migration-guide/)
- [Feishu Bitable Python Tool](https://github.com/dungeer619/feishu-bitable-python-tool)
- Codebase analysis: `backend/app/core/auth.py`, `backend/app/api/v1/router.py`, `.planning/codebase/CONCERNS.md`

---

*Pitfalls audit: 2026-03-27*
