# Project Research Summary

**Project:** Social Security & Housing Fund Management System (v2 milestone)
**Domain:** Chinese Enterprise Social Insurance Data Aggregation & Management Platform
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

This project transitions an existing React + FastAPI Excel merge tool into a multi-user management platform with authentication, employee self-service, Feishu Bitable integration, and a professional UI redesign. The core data pipeline (upload, parse, normalize, validate, match, dual-template export) already works -- the Salary template exports correctly and the Tool template needs field mapping fixes. The v2 milestone adds three major capability layers: access control (RBAC with admin/HR/employee roles), an employee self-service portal, and bidirectional Feishu Bitable sync.

The recommended approach is to build incrementally on the existing working pipeline without disrupting it. Ant Design 5.x is the clear frontend framework choice for this Chinese enterprise context (native zh-CN, rich data tables, Feishu-aesthetic compatibility). PyJWT replaces the deprecated python-jose for auth tokens. The official `lark-oapi` SDK handles all Feishu integration. The architecture stays monolithic (React SPA + FastAPI + SQLite) which is appropriate for a single-company internal tool. The key architectural principle is that external integrations (Feishu sync, OAuth) must be gated behind feature flags and must never run as background processes -- SQLite cannot handle concurrent writers.

The three highest risks are: (1) auth retrofit breaking the working NDJSON streaming pipeline and unauthenticated self-service endpoint, (2) frontend redesign accidentally changing API contracts and regressing the Salary export, and (3) Feishu Bitable sync becoming an uncontrollable consistency problem due to rate limits and bidirectional conflict. All three are mitigable with disciplined sequencing: fix the Tool template first as a safety baseline, add auth with router-level guards, write E2E smoke tests before any frontend work, and implement Feishu sync as push-only first with explicit triggers (never background polling).

## Key Findings

### Recommended Stack

The existing stack (React 18.3, FastAPI 0.115, SQLite WAL, Vite 6.2) is retained. New additions are chosen for minimal footprint and maximum fit with the Chinese enterprise context.

**Core technologies:**
- **Ant Design 5.x**: UI component library -- native zh-CN, best-in-class data tables for insurance record display, Feishu-aesthetic alignment. Stay on v5 (v6 requires React 19).
- **PyJWT 2.9+**: JWT token handling -- replaces deprecated python-jose. FastAPI docs officially recommend it.
- **lark-oapi 1.5.3**: Official Feishu/Lark Python SDK -- covers Bitable CRUD, OAuth, token management. No community alternatives needed.
- **motion 12.x**: Animation library -- page transitions and micro-interactions for "premium feel" without conflicting with Ant Design's CSS-in-JS.
- **tenacity 9.0+**: Retry logic -- essential for Feishu API rate limit handling with exponential backoff.
- **ahooks 3.8+**: React hooks collection -- useRequest, useDebounceFn from the Ant Design ecosystem.

**What to remove:** `python-jose[cryptography]` from requirements.server.txt (deprecated, security issues).

### Expected Features

**Must have (table stakes):**
- RBAC with Admin/HR/Employee roles -- every enterprise system needs permission boundaries
- Employee self-service query -- the headline reason employees would use the system
- Multi-period data browsing -- view and compare months of contribution data
- Data search and filtering -- HR must filter by region, company, employee, insurance type
- Dual template export (fix Tool template) -- both templates must work; this is the core deliverable
- Data validation dashboard -- visibility into import health and data quality
- Employee master data CRUD -- HR needs to manage the employee registry
- Professional UI (Ant Design redesign) -- ugly internal tools get abandoned
- Secure authentication with proper login UI -- legal/compliance requirement for PII access

**Should have (differentiators):**
- Feishu Bitable bidirectional sync -- killer feature for Feishu-native organizations
- REST API with API key auth -- transforms the tool into a data platform
- Cross-period comparison and trend view -- spot anomalies across months
- Feishu OAuth login -- SSO convenience for Feishu-native users
- Anomaly detection and alerts -- proactive data quality flagging

**Defer indefinitely:**
- Salary/payroll calculation -- out of scope, creates liability
- Government portal direct submission -- each city has different portals, massive compliance surface
- Custom report builder -- Feishu Bitable covers ad-hoc analysis
- Multi-tenant / SaaS -- single company use, zero benefit from tenant isolation

### Architecture Approach

The system remains a monolithic two-tier app (React SPA + FastAPI + SQLite) with the API layer extended to serve three distinct consumer types: Admin Console, HR Console, and Employee Portal. Authentication splits into three paths: password login (admin/HR), employee verification (ID + name triple-check, no password), and optional Feishu OAuth. External API access reuses existing endpoints with API key authentication as an alternative credential type -- no separate "external" API namespace. Feishu sync is explicit-trigger only (never background), and the system is the authoritative data source in all sync conflicts.

**Major components:**
1. **Auth & Permission Layer** -- role-scoped FastAPI dependencies (require_role), three auth paths, API key support
2. **Employee Portal** -- separate login flow, scoped token, read-only personal record queries
3. **Feishu Sync Service** -- push-first to Bitable via lark-oapi, sync log for reconciliation, rate-limit-aware batching
4. **Feishu Auth Service** -- OAuth code exchange, identity-to-role mapping, additive to existing auth
5. **External API Layer** -- reuses existing /api/v1/ endpoints, API key model for programmatic access

### Critical Pitfalls

1. **Auth retrofit breaks streaming pipeline** -- The NDJSON streaming aggregate endpoint and unauthenticated self-service endpoint are fragile integration points. Use router-level `dependencies=` (not per-endpoint), audit all routes with grep, and test streaming specifically after auth changes.

2. **Frontend redesign regresses Salary export** -- Zero frontend tests exist. Write E2E smoke tests for the critical path (upload -> parse -> export Salary template) BEFORE any redesign. Export an OpenAPI spec snapshot as the API contract. Treat the redesign as a new app consuming the existing API.

3. **Feishu Bitable sync consistency nightmare** -- Rate limits (50 writes/sec, 1000 records/batch), token expiry (2 hours), and bidirectional conflicts. Start push-only, use sync log table, make operations idempotent (upsert on id_number + period), and define field ownership (system owns insurance data, Feishu owns annotations).

4. **PII exposure under PIPL** -- National ID numbers and salary data are "sensitive personal information" under PIPL. The current unauthenticated self-service endpoint enables ID enumeration. Add rate limiting, audit logging, and field masking as the first commits of the auth phase.

5. **Tool template fix breaks Salary template** -- Both share a 1160-line monolithic exporter. Split into salary_exporter.py, tool_exporter.py, and export_utils.py BEFORE fixing the Tool template. Write Salary regression test first.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Export Stabilization
**Rationale:** Fix the one broken feature before adding anything new. The Tool template field mapping issues are the only regression in the current system. This phase also de-risks all future export work by splitting the monolithic exporter.
**Delivers:** Both templates exporting correctly; exporter codebase split into maintainable modules; Salary template regression test as permanent safety net.
**Addresses:** Dual template export fix (table stakes #5), normalization service cleanup (pitfall #8)
**Avoids:** Salary template regression (pitfall #5)

### Phase 2: Auth, Roles & Security Hardening
**Rationale:** Authentication is a prerequisite for every user-facing feature. The current system has PII exposure via unauthenticated endpoints and default credentials. This must be locked down before adding employee self-service or external API access.
**Delivers:** Three-role RBAC (admin/HR/employee), PyJWT-based tokens, employee verification endpoint, rate limiting, audit logging, API key model for external access.
**Addresses:** RBAC (table stakes #1), secure auth (table stakes #10), PII protection (pitfall #4)
**Avoids:** Auth retrofit breaking streaming (pitfall #1), SQLite contention (pitfall #6), migration drift (pitfall #10)
**Uses:** PyJWT, passlib[bcrypt], FastAPI dependency injection

### Phase 3: Employee Portal & Master Data
**Rationale:** With auth in place, the employee self-service portal becomes deliverable. Employee master data CRUD is a dependency -- employees cannot authenticate without master data to verify against, and matching cannot work without it.
**Delivers:** Employee portal (login, personal records, contribution summary), employee master data CRUD for HR, import history/audit trail UI.
**Addresses:** Employee self-service (table stakes #2), employee master data (table stakes #8), import audit trail (table stakes #7)

### Phase 4: Frontend Redesign
**Rationale:** All backend APIs and new pages (portal, master data, API keys) must be stable before the frontend is rebuilt. Redesigning while backend contracts are still shifting guarantees regressions. Ant Design adoption happens here.
**Delivers:** Feishu-inspired professional UI with Ant Design 5, role-aware routing, responsive layout, data validation dashboard redesign, multi-period browsing, search/filtering.
**Addresses:** Professional UI (table stakes #9), data validation dashboard (table stakes #6), multi-period browsing (table stakes #3), search/filtering (table stakes #4)
**Avoids:** Backend contract drift (pitfall #2), CORS breakage (pitfall #9)
**Uses:** Ant Design 5.x, @ant-design/pro-components, motion 12.x, ahooks

### Phase 5: Feishu Integration
**Rationale:** Feishu sync is the top differentiator but depends on stable data and auth. It also requires external Feishu app credentials that may not be available immediately. Isolate it as its own phase to avoid blocking other work.
**Delivers:** System-to-Feishu push sync, Feishu-to-system pull with diff review, sync status dashboard, Feishu OAuth login (optional).
**Addresses:** Feishu Bitable sync (differentiator #1), Feishu OAuth (differentiator #7)
**Avoids:** Sync consistency collapse (pitfall #3), identity split (pitfall #7), PII in Feishu (pitfall #4)
**Uses:** lark-oapi 1.5.3, tenacity for retries

### Phase 6: Intelligence & Polish
**Rationale:** Cross-period comparison and anomaly detection require multiple periods of clean data to be meaningful. These features build on a stable, multi-period data store.
**Delivers:** Cross-period comparison, anomaly detection, mapping override UI, one-click re-export, housing fund unified view, batch import progress enhancement.
**Addresses:** Remaining differentiators (#4, #5, #6, #8, #9, #10)

### Phase Ordering Rationale

- **Fix before extend**: Tool template fix first establishes a safety baseline and regression test infrastructure
- **Auth before features**: Every user-facing feature depends on roles and permissions. PII compliance is non-negotiable before expanding access.
- **Backend before frontend**: All API contracts must stabilize before the frontend redesign to avoid the #1 cause of regressions in this codebase
- **Internal before external**: HR and employees use the system daily. Feishu sync serves a secondary workflow and has external dependency (app credentials).
- **Intelligence after data**: Trends and anomaly detection require accumulated clean data across multiple periods

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Auth):** The existing custom HMAC token scheme needs careful migration to PyJWT without breaking active sessions. Audit all auth callsites.
- **Phase 5 (Feishu):** Feishu Bitable field type mapping (currency, dates, multi-line text) needs hands-on API testing. Rate limit behavior under batch operations needs empirical validation. The China platform (feishu.cn) vs international Lark (larksuite.com) distinction must be confirmed with the team.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Export Fix):** Well-understood refactoring -- split monolithic file, fix field mappings. No research needed.
- **Phase 3 (Portal):** Standard CRUD + read-only query patterns. FastAPI dependency injection for scoped access is well-documented.
- **Phase 4 (Frontend):** Ant Design 5.x is extensively documented with Chinese ecosystem examples. ProComponents covers the admin layout pattern.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommendations backed by official docs, active maintenance, and ecosystem fit. PyJWT switch confirmed by FastAPI maintainers. Ant Design choice is obvious for Chinese enterprise context. |
| Features | HIGH | Feature prioritization based on domain analysis (Chinese social insurance monthly cycle), existing codebase capabilities, and competitor landscape. Clear dependency chain. |
| Architecture | HIGH | Architecture extends existing patterns (FastAPI deps, SQLite WAL, service layer) rather than introducing new paradigms. Feishu API constraints well-documented by official sources. |
| Pitfalls | HIGH | Pitfalls identified from actual codebase analysis (specific file sizes, existing auth gaps, known vulnerabilities) combined with domain-specific risks (PIPL compliance, Feishu rate limits). |

**Overall confidence:** HIGH

### Gaps to Address

- **Feishu app credentials availability:** The team needs to register a Feishu app and obtain credentials before Phase 5 can begin. This is an external dependency that should be initiated early (during Phase 2-3).
- **Employee master data completeness:** The quality of employee self-service and matching depends on having complete, accurate master data. Need to confirm with HR what data sources exist and how to seed the initial dataset.
- **Tool template exact field mapping issues:** The specific field mapping bugs in the Tool template need to be diagnosed at the start of Phase 1. Research identified the risk of shared exporter code but the exact mapping errors need codebase investigation.
- **PIPL compliance scope:** The PII protection measures recommended are baseline. If the company has a DPO or legal compliance team, their requirements may add constraints to Phase 2.
- **Housing fund data standardization:** Housing fund parsing "partially exists" but the extent of region coverage and field mapping completeness is unclear. Phase 6 may need its own research spike.

## Sources

### Primary (HIGH confidence)
- [FastAPI Security & JWT docs](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) -- Auth patterns, PyJWT migration
- [FastAPI JWT migration PR #11589](https://github.com/fastapi/fastapi/pull/11589) -- python-jose deprecation confirmation
- [Feishu Bitable API Overview](https://open.larkoffice.com/document/server-docs/docs/bitable-v1/bitable-overview) -- Bitable endpoints, rate limits, batch operations
- [lark-oapi on PyPI](https://pypi.org/project/lark-oapi/) -- Official SDK v1.5.3
- [Feishu OAuth Login Overview](https://open.feishu.cn/document/sso/web-application-sso/login-overview) -- SSO flow
- [Ant Design 5.x docs](https://ant.design/) -- Component library, theming, ProComponents
- [Motion (ex-Framer Motion)](https://motion.dev/docs/react-upgrade-guide) -- Animation library v12

### Secondary (MEDIUM confidence)
- [PIPL Compliance Guide - China Briefing](https://www.china-briefing.com/doing-business-guide/china/company-establishment/pipl-personal-information-protection-law) -- PII classification, penalty structure
- [Ant Design vs shadcn comparison](https://www.subframe.com/tips/ant-design-vs-shadcn) -- Framework selection rationale
- [2025 HR System Comparison (Chinese)](https://www.cnblogs.com/worktile/articles/19132742) -- Competitor feature expectations
- [Frontend Migration Guide](https://frontendmastery.com/posts/frontend-migration-guide/) -- Redesign risk patterns

### Tertiary (LOW confidence)
- [Feishu Bitable Python community tool](https://github.com/dungeer619/feishu-bitable-python-tool) -- Implementation patterns (community, not official)

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
