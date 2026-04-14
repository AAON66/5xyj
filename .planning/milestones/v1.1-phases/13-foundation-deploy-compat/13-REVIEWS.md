---
phase: 13
reviewers: [codex]
reviewed_at: 2026-04-04T12:00:00Z
plans_reviewed: [13-01-PLAN.md, 13-02-PLAN.md, 13-03-PLAN.md, 13-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 13

## Codex Review

Review is based on the current branch state, not just the plan text. Overall, the wave split is sensible, but the set needs rebasing before execution: some items are already true, such as `xlrd` existing in requirements.txt and Wuhan housing-fund coverage existing in test_housing_fund_service.py, while two material gaps remain: Python 3.9 compatibility is understated, and INFRA-04 is not actually covered by the audit-log plan.

### Plan 13-01: Python 3.9 兼容性修复 + 依赖清理
**Summary**
Directionally correct, but incomplete in the one place that matters most: Python 3.9 parsing/runtime compatibility. As written, this plan is likely to leave the codebase still unstartable on 3.9.

**Strengths**
- Targets the right class of issue with `@dataclass(slots=True)`.
- Tries to reduce dependency drift and deployment variance.

**Concerns**
- HIGH: The real 3.9 blocker is not just `slots=True`; the codebase already contains many `A | B` type annotations in backend and tests, for example in workbook_loader.py and template_exporter.py. Adding `from __future__ import annotations` does not solve Python 3.9 syntax incompatibility for PEP 604 unions.
- MEDIUM: The plan spends effort on adding `from __future__ import annotations` to `__init__.py` files, which is mostly noise compared with the actual syntax surface.
- MEDIUM: Replacing exact pins with loose upper-bound ranges weakens reproducibility for "cloud server stable run"; that is the opposite of INFRA-01's deployment goal.
- MEDIUM: The plan is stale against the repo state. `requirements.server.txt` is absent, `xlrd` is already present in requirements.txt, and that file is currently UTF-16LE, which is itself a Linux deployment risk not mentioned in the plan.
- LOW: architecture.md still says Python 3.11+ and PostgreSQL/Docker Compose, so code-only fixes will leave documentation drift.

**Suggestions**
- Expand Task 1 to explicitly convert all PEP 604 unions to `Optional`/`Union` and run the backend test suite under Python 3.9, not just "verify no match/case".
- Keep an exact lock file or constraints file for server deploys; do not downgrade to broad version ranges unless you also generate a tested lock.
- Add requirements-file normalization to UTF-8 and a smoke step: `python3.9 -m pip install -r requirements.txt && pytest`.
- Add a docs subtask to align architecture.md and deployment docs with the 3.9 target.

**Risk Assessment**
HIGH. The plan misses a hard syntax-compatibility class and contains stale assumptions about current dependency files.

### Plan 13-02: 前端废弃组件清理 + 快速融合页面小修复
**Summary**
This is the cleanest plan of the set. The scope is contained and aligned with the phase goals, but the verification story is too light for the async default-selection behavior.

**Strengths**
- The file-count requirement maps directly to the current UI in SimpleAggregate.tsx.
- The proposed `useRef` guard is a reasonable way to prevent late async data from overriding a user's manual choice.

**Concerns**
- MEDIUM: The plan should define what "file count" means. The page deduplicates files via `mergeFiles`, supports removal, and can also restore session state; the count must follow the displayed source of truth, not just local arrays in one state branch.
- MEDIUM: There is no explicit verification for the race where employee-master availability arrives after the user already chose `none` or `upload` in SimpleAggregate.tsx.
- LOW: "Update barrel export" is not enough by itself because `AppShell` directly imports `GlobalFeedback` in AppShell.tsx; deletion must verify direct imports, not only `components/index.ts`.
- LOW: There is no frontend test harness in the repo today, so this plan needs either a lightweight regression test addition or an explicit manual QA checklist.

**Suggestions**
- Define counts as the visible, deduplicated counts for social and housing-fund files, including restored session records.
- Add a small regression check for three states: server has master, server has none, user manually changes selection before fetch resolves.
- Delete component files only after verifying they are unused across the app, not just absent from the barrel.

**Risk Assessment**
LOW. Small, local, and easy to validate if the async-state edge cases are made explicit.

### Plan 13-03: 技术债常量合并 + 自助查询端点认证修复
**Summary**
This plan has the highest behavioral risk. The constants cleanup is good but under-scoped, and the auth change is likely correct architecturally yet currently conflicts with existing tests and a still-present public client path.

**Strengths**
- Consolidating region and filename constants would reduce real duplication across import and aggregate flows.
- Locking down the legacy self-service endpoint is directionally consistent with the authenticated employee portal model.

**Concerns**
- HIGH: `/employees/self-service/query` is currently treated as public by existing regression tests in test_auth_api.py and test_employee_portal_api.py. This is not a safe "small fix"; it is a contract change.
- HIGH: The frontend still has a client for that public route in employees.ts. If auth is added, caller behavior and error handling must be updated or removed.
- MEDIUM: Moving only constants does not remove the duplicated filename/company inference logic still split across aggregate_service.py and import_service.py.
- MEDIUM: The proposed ID regex merge is incomplete. The codebase also duplicates the non-mainland pattern, not just `ID_NUMBER_PATTERN`, in matching_service.py and export_utils.py.

**Suggestions**
- Decide explicitly whether the old endpoint is being retired, protected, or replaced with a compatibility shim; then update tests, client code, and any user-facing copy in one change.
- Expand the cleanup from "constants" to shared helper functions for filename normalization and company inference.
- Put shared region constants in a leaf module, not a business-mapping module, to avoid semantic drift and import cycles.

**Risk Assessment**
HIGH. The auth change is a breaking behavior change, and the cleanup portion only partially removes the duplicated logic it claims to address.

### Plan 13-04: 审计日志 IP 解析增强 + nginx 配置文档
**Summary**
The core idea is right, but the plan only fully addresses INFRA-03. As written, it does not really satisfy INFRA-04, and the IP logic is security-sensitive enough that the exact trust model needs to be spelled out.

**Strengths**
- Fixing request_helpers.py is necessary; the current implementation trusts any `X-Forwarded-For` blindly.
- Adding proxy documentation is practical for the stated cloud-server deployment target.

**Concerns**
- HIGH: A safe `X-Forwarded-For` implementation must only trust proxy headers when `request.client.host` is itself trusted; otherwise header spoofing remains trivial.
- MEDIUM: `trusted_proxies` as a literal list of `127.0.0.1` and `::1` may be too narrow for real reverse-proxy or ingress setups. At minimum, the config contract needs to be explicit.
- MEDIUM: INFRA-04 is not actually covered. Current audit call sites such as aggregate.py and auth.py still log fairly thin detail payloads.
- LOW: A frontend warning in AuditLogs.tsx based on "all IPs are 127.0.0.1" can false-positive in local/dev, filtered views, or internal-service actions.

**Suggestions**
- Specify the algorithm: trust headers only from trusted peers, parse multi-hop `X-Forwarded-For` safely, fall back to `X-Real-IP` only under the same trust rule.
- Add one integration test through FastAPI/TestClient, not just pure unit tests, to verify real request behavior.
- Split INFRA-04 into an explicit subtask: audit all `log_audit` call sites and enrich them with consistent `resource_type`, `resource_id`, batch/context identifiers, and operation detail.

**Risk Assessment**
MEDIUM. The implementation is small, but it is security-sensitive and currently incomplete against the stated requirement set.

---

## Consensus Summary

> Note: Only one external reviewer (Codex) was available. Consensus is based on single-reviewer findings.

### Key Concerns (Priority Order)

1. **HIGH — Python 3.9 PEP 604 unions not addressed (Plan 01):** `from __future__ import annotations` does NOT fix `A | B` syntax on Python 3.9. The codebase has many such unions in backend files. This is a hard blocker for the phase goal.

2. **HIGH — Self-service endpoint auth is a breaking change (Plan 03):** Existing tests treat `/employees/self-service/query` as public. Frontend client code in `employees.ts` calls it without auth. Must update tests + frontend together.

3. **HIGH — INFRA-04 not actually covered (Plan 04):** The plan only addresses IP resolution (INFRA-03). INFRA-04 calls for richer audit log content (operation detail, resource context), which no plan addresses.

4. **MEDIUM — Plan 01 stale assumptions:** `requirements.server.txt` may already be absent, `xlrd` may already be present, `requirements.txt` encoding (UTF-16LE) could break Linux pip.

5. **MEDIUM — File count definition unclear (Plan 02):** Page deduplicates via `mergeFiles` and supports session restore — count must follow the displayed list, not raw upload arrays.

### Agreed Strengths
- Wave structure is sensible (01/02/04 parallel, 03 after 01)
- `@dataclass(slots=True)` removal is correctly identified as priority
- `useRef` guard for async default-selection is a good pattern
- Trusted proxy model for IP resolution is the right approach

### Divergent Views
N/A — single reviewer
