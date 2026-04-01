---
phase: 10
reviewers: [claude]
reviewed_at: 2026-03-31T12:00:00Z
plans_reviewed: [10-01-PLAN.md, 10-02-PLAN.md, 10-03-PLAN.md, 10-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 10

## Claude Review

# Phase 10: Feishu Integration - Plan Review

## 1) Summary Assessment

Phase 10 is well-structured across 4 plans in 3 waves, covering backend foundation (Plan 01), API endpoints (Plan 02), frontend core pages (Plan 03), and advanced UI features (Plan 04). The plans collectively address all 5 FEISHU requirements and 20 design decisions from CONTEXT.md. The wave-based dependency ordering (01 -> 02+03 parallel -> 04) is sound. The decision to use `httpx` directly over `lark-oapi` SDK and `@xyflow/react` for field mapping are well-justified.

**Overall verdict: GOOD with several concerns to address before execution.**

---

## 2) Strengths

- **Thorough research foundation.** The RESEARCH.md identifies concrete API endpoints, version-specific deprecations (old OAuth URL, list vs search endpoints), batch size limits, and rate limiting considerations. Common pitfalls are documented with error codes.

- **Clean dependency graph.** Plan 01 (models/services) has no dependencies. Plans 02+03 depend only on 01 and can run in parallel. Plan 04 depends on both 02+03. This maximizes parallelism.

- **Feature flag design is comprehensive.** Both backend (endpoint-level 404 when disabled) and frontend (route guard + nav item hiding) are covered. Pitfall 6 in RESEARCH.md explicitly calls out the direct-URL bypass risk.

- **Reuse of established patterns.** NDJSON streaming from imports, RBAC from dependencies.py, JWT issuance from auth.py, Ant Design component system — all leveraged correctly.

- **Conflict resolution is well-specified.** Both push conflicts (overwrite/skip/cancel with diff display, D-07) and pull conflicts (three strategies with per-record selection, D-08/D-09) are fully designed with UI specs.

- **Security-aware OAuth design.** D-10 correctly issues system JWT rather than storing Feishu tokens. CSRF state parameter is included in the flow.

---

## 3) Concerns

### HIGH Severity

**H1: Synchronous httpx client in async FastAPI endpoints.**
Plan 01 uses `httpx.Client` (synchronous) in `FeishuClient`, but Plan 02 wraps this in FastAPI endpoints that serve `StreamingResponse`. Calling synchronous HTTP within an async event loop will block the server. The sync service functions (`push_records_to_feishu`, etc.) do synchronous httpx calls inside what Plan 02 implies will be async generators for NDJSON streaming.
- **Impact:** Server thread starvation under concurrent sync requests.
- **Fix:** Either use `httpx.AsyncClient` throughout, or run sync operations in a thread pool executor.

**H2: OAuth state parameter validation is incomplete.**
Plan 02 Task 1 mentions generating a `state` with `secrets.token_urlsafe(32)` in the `/authorize-url` endpoint, but there is no mechanism to store this state server-side and validate it when the callback arrives. The callback endpoint accepts `state` as a parameter but never checks it against a stored value. The frontend callback in Plan 04 reads `code` and `state` from URL params but sends them to the backend without any client-side state verification either.
- **Impact:** CSRF vulnerability in OAuth flow.
- **Fix:** Store the generated state in a short-lived cookie or server-side cache. Validate in the callback before exchanging the code.

**H3: Pull modifying NormalizedRecord directly is architecturally dangerous.**
Plan 01's `pull_records_from_feishu` says "Update or create NormalizedRecord entries." NormalizedRecords are the output of the parsing pipeline and carry provenance (`source_file_name`, `source_row_number`, `raw_header_signature`). Overwriting them from Feishu data breaks the provenance chain that CLAUDE.md mandates ("每条标准化结果都必须可追溯到原始文件和原始行").
- **Impact:** Data lineage corruption; auditors can't trace values back to source Excel files.
- **Fix:** Either (a) create a separate `feishu_overrides` table that layers on top of NormalizedRecord, or (b) add clear provenance markers (e.g., `source_file_name = "feishu_pull:{config_name}"`) when pull-created records are inserted.

### MEDIUM Severity

**M1: Singleton `FeishuClient` with global mutable state is test-unfriendly.**
`feishu_token_service.py` uses a module-level `_client_instance` global. This creates implicit coupling and makes parallel test execution problematic. The `reset_feishu_client()` function helps but relies on manual cleanup.
- **Fix:** Use FastAPI's dependency injection system (e.g., `Depends(get_feishu_client)`) instead of a module-level singleton.

**M2: No rate limiting on Feishu API calls.**
RESEARCH.md notes "Bitable field list is 20 req/s" and recommends throttling, but none of the plans implement any rate limiting. Batch operations during large pushes could hit Feishu's rate limits.
- **Fix:** Add a simple semaphore or sleep-based throttle in `FeishuClient`, especially for paginated reads in `search_records` and `list_fields`.

**M3: Credential storage via PUT /credentials is under-specified.**
Plan 02 says "Store to DB (encrypted)" but no encryption mechanism is defined. There's no model for storing DB-based credentials, no encryption key management, and D-13 says env vars take priority anyway. This endpoint could become dead code or, worse, store secrets in plaintext.
- **Fix:** Either defer the DB credential storage entirely (v2) and only support env vars for now, or define the encryption approach (e.g., Fernet with a key from env var).

**M4: Plan 03 depends on Plan 02's API endpoints but is in the same wave.**
Plans 02 and 03 are both Wave 2, depending only on Plan 01. However, Plan 03's frontend pages call API endpoints defined in Plan 02. If Plan 03 is built before Plan 02's endpoints exist, the frontend will have no backend to call.
- **Impact:** Low practical impact since both are typically built in sequence by a single agent, but the wave designation is misleading.
- **Fix:** Either accept this as a known constraint or move Plan 03 to Wave 3 alongside Plan 04.

**M5: Missing pagination in sync history API.**
`get_sync_history` uses a simple `limit` parameter but no offset/cursor pagination. For a system with frequent syncs, this will become a performance issue.
- **Fix:** Add `offset` parameter or cursor-based pagination consistent with other paginated endpoints.

### LOW Severity

**L1: `SyncConfigRead` uses `str` for `created_at`/`updated_at` instead of `datetime`.**
This requires manual serialization and may cause timezone inconsistencies.

**L2: The "auto-match" feature in FeishuFieldMapping uses simple label containment.**
This will produce false positives. Consider exact match first, then containment as fallback.

**L3: Plan 04 is `autonomous: false` but only Task 3 requires human input.** Tasks 1 and 2 are `type: auto`.

**L4: No cleanup/disconnect logic for `FeishuClient._http`.**
The httpx `Client` in the singleton is never closed during normal shutdown.

---

## 4) Suggestions

1. **Add an async variant of FeishuClient** or use `run_in_executor` for sync calls within streaming endpoints.
2. **Implement OAuth state validation** using a short-lived server-side store.
3. **Create a `feishu_sync_records` table** or add provenance markers instead of directly modifying `normalized_records` during pull.
4. **Add a `/api/v1/feishu/sync/push/check` endpoint** (pre-flight) separate from the actual push.
5. **Consider testing with `respx`** (mock library for httpx) rather than `unittest.mock.patch`.
6. **Add a `last_synced_at` field to SyncConfig** so the UI can show when each target was last synced.

---

## 5) Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Feishu App not yet registered | HIGH | MEDIUM | All tests use mocks |
| Sync httpx calls block async event loop | HIGH | HIGH | Switch to AsyncClient or use executor (H1) |
| OAuth CSRF vulnerability | MEDIUM | HIGH | Implement state validation (H2) |
| Pull corrupts NormalizedRecord provenance | HIGH | HIGH | Use separate table or provenance markers (H3) |
| Rate limit hits on large pushes | MEDIUM | MEDIUM | Add throttling |
| @xyflow/react version incompatibility | LOW | MEDIUM | Version 12.x supports React 18 |
| Feature flag bypass via direct URL | LOW | LOW | Already addressed |
| Alembic migration conflicts | LOW | MEDIUM | Use auto-generated revision IDs |

**Overall risk level: MEDIUM-HIGH**, primarily driven by H1, H2, and H3. All are fixable before execution begins.

---

## Consensus Summary

*(Single reviewer — no cross-reviewer consensus available. Gemini CLI was not available.)*

### Key Strengths
- Clean wave-based dependency graph maximizing parallelism
- Comprehensive feature flag design (backend + frontend)
- Thorough reuse of established project patterns
- Well-specified conflict resolution for both push and pull

### Top Concerns (must address before execution)
1. **H1:** Synchronous httpx in async FastAPI endpoints → use AsyncClient or run_in_executor
2. **H2:** OAuth state parameter not validated → implement CSRF protection
3. **H3:** Pull directly modifying NormalizedRecord breaks provenance → add provenance markers or separate table

### Improvement Suggestions
- Add rate limiting for Feishu API calls (M2)
- Define encryption approach for DB credential storage (M3)
- Add pagination to sync history API (M5)
