---
phase: 17
slug: data-management-enhancement
status: blocked
threats_open: 1
asvs_level: 1
created: 2026-04-09
---

# Phase 17 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| internal mapping rules | Plan 17-01 only changes static alias rules and tests inside the codebase | Internal code and test fixtures |
| client -> API | Plan 17-02 and 17-03 accept user-supplied filters and batch identifiers over authenticated API routes | Filter values and batch identifiers |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-17-01 | Tampering | `manual_field_aliases.py` | accept | Internal-only alias rule change; accepted risk documented in the log below | closed |
| T-17-02 | Tampering | `data_management.py` query params | mitigate | FastAPI `Query(Optional[List[str]])` type validation constrains filter inputs on records, filter-options, and summary endpoints | closed |
| T-17-03 | Denial of Service | `data_management_service.py` `IN` clause filtering | accept | Residual risk accepted because requests are paginated with `page_size <= 100` and selector sets are business-bounded | closed |
| T-17-04 | Information Disclosure | `deletion-impact` endpoint | mitigate | Import routes are protected by `require_role("admin", "hr")`; endpoint returns counts only, not row-level data | closed |
| T-17-05 | Tampering | `batch_id` parameter | mitigate | Expected UUID validation at the API boundary or explicit parsing before querying; current implementation only shows parameterized lookups | open |

*Status: open · closed*  
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-17-01 | T-17-01 | The alias-rule change only affects static internal mapping code and regression tests. The phase does not expose any new external write path into `manual_field_aliases.py`. | Codex security audit | 2026-04-09 |
| AR-17-02 | T-17-03 | The multi-select feature still enforces `page_size <= 100`, and the `.in_()` selectors operate on small region/company/period sets rather than arbitrary unbounded payloads. Residual DoS risk is low and documented. | Codex security audit | 2026-04-09 |

*Accepted risks do not resurface in future audit runs.*

---

## Evidence

- `T-17-02`: [backend/app/api/v1/data_management.py](/Users/mac/PycharmProjects/5xyj/backend/app/api/v1/data_management.py#L25) uses `Optional[List[str]]` query parameters, and [backend/app/api/v1/data_management.py](/Users/mac/PycharmProjects/5xyj/backend/app/api/v1/data_management.py#L30) caps `page_size` at `100`.
- `T-17-03`: [backend/app/services/data_management_service.py](/Users/mac/PycharmProjects/5xyj/backend/app/services/data_management_service.py#L44) applies `.in_()` filters only after typed inputs are accepted, and the paginated query remains bounded.
- `T-17-04`: [backend/app/api/v1/router.py](/Users/mac/PycharmProjects/5xyj/backend/app/api/v1/router.py#L41) mounts `imports_router` behind `require_role("admin", "hr")`; [backend/app/dependencies.py](/Users/mac/PycharmProjects/5xyj/backend/app/dependencies.py#L43) enforces authentication; [backend/app/schemas/imports.py](/Users/mac/PycharmProjects/5xyj/backend/app/schemas/imports.py#L34) limits the response to count fields.
- `T-17-05`: [backend/app/api/v1/imports.py](/Users/mac/PycharmProjects/5xyj/backend/app/api/v1/imports.py#L113) and [backend/app/api/v1/imports.py](/Users/mac/PycharmProjects/5xyj/backend/app/api/v1/imports.py#L125) still type `batch_id` as plain `str`; [backend/app/services/import_service.py](/Users/mac/PycharmProjects/5xyj/backend/app/services/import_service.py#L215) and [backend/app/services/import_service.py](/Users/mac/PycharmProjects/5xyj/backend/app/services/import_service.py#L291) use safe parameterized lookups, but explicit UUID validation from the plan is absent.

---

## Open Threat Follow-up

| Threat ID | Gap | Required Action |
|-----------|-----|-----------------|
| T-17-05 | `batch_id` is not validated as UUID at the API boundary, so the planned mitigation is only partially implemented. | Change route parameters to UUID-typed values or parse/validate UUIDs before calling service-layer queries, then re-run `/gsd-secure-phase 17`. |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-09 | 5 | 4 | 1 | Codex + gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [ ] `threats_open: 0` confirmed
- [ ] `status: verified` set in frontmatter

**Approval:** pending - blocked by T-17-05
