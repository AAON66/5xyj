# Domain Pitfalls: v1.1 Feature Additions

**Domain:** Social insurance management system — retrofitting responsive design, dark mode, diff UI, account management, Python 3.9 compat, cascade delete to existing React 18 + Ant Design 5 + FastAPI + SQLite app
**Researched:** 2026-04-04
**Overall confidence:** HIGH (based on direct codebase inspection + known ecosystem patterns)

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or major regressions.

### Pitfall 1: SQLite CASCADE DELETE silent failure without PRAGMA foreign_keys

**What goes wrong:** SQLite ignores `ON DELETE CASCADE` by default. Even though `ForeignKey(..., ondelete="CASCADE")` is declared on every child model (source_files, normalized_records, match_results, export_jobs, etc.), deleting an ImportBatch will silently leave orphan rows if `PRAGMA foreign_keys=ON` is not active on the connection.

**Why it happens:** SQLite requires `PRAGMA foreign_keys=ON` on every new connection. The codebase already does this in `database.py:_apply_sqlite_pragmas`, but test sessions, migration scripts, manual DB access, or any code path that bypasses the configured engine will produce silent orphans.

**Consequences:** Deleting a batch leaves orphaned normalized_records, match_results, validation_issues, export_jobs, and export_artifacts. The "batch delete cascading to month data" feature becomes unreliable. Orphan data appears in queries and corrupts dashboard statistics.

**Prevention:**
1. Before implementing cascade batch delete, write an integration test that deletes a batch and asserts all child table counts drop to zero.
2. Add a `PRAGMA foreign_keys` check assertion to the test fixture that creates DB sessions.
3. For the v1.1 "data cascade delete" feature, do NOT rely solely on database-level CASCADE. Use SQLAlchemy's `cascade="all, delete-orphan"` (already present on ImportBatch relationships) AND verify with explicit count queries in the service layer.
4. Add a startup assertion that verifies `PRAGMA foreign_keys` returns `1`.

**Detection:** Run `SELECT COUNT(*) FROM normalized_records WHERE batch_id NOT IN (SELECT id FROM import_batches)` after any delete operation in tests.

---

### Pitfall 2: Python 3.9 downgrade breaks `X | Y` union type syntax in 30+ files

**What goes wrong:** The codebase uses `str | None`, `dict[str, object] | None`, `Awaitable[None] | None` extensively in service layer type hints (found in import_service.py, aggregate_service.py, feishu_sync_service.py, housing_fund_service.py, export_utils.py, and 25+ more files). Python 3.9 does not support `X | Y` syntax for type unions at runtime.

**Why it happens:** Most files use `from __future__ import annotations` (which defers annotation evaluation and makes `X | Y` syntax work as strings), BUT several files use `X | Y` in runtime contexts — default arguments, isinstance checks, or files that lack the `__future__` import. Mixed patterns across the codebase make it easy to miss problematic files.

**Consequences:** `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` at import time on Python 3.9, crashing the entire application on startup.

**Prevention:**
1. Systematically audit every `.py` file: ensure ALL files have `from __future__ import annotations` as the first import.
2. Search for runtime `X | Y` usage outside annotations: `isinstance()` checks, `typing.get_type_hints()` calls, any place types are evaluated at runtime.
3. Run the full test suite under Python 3.9 before merging — set up CI to test on 3.9 as a gate.
4. For Pydantic v2 models (schemas/), `X | Y` in field annotations is safe WITH `from __future__ import annotations`, but `model_validator` and discriminated unions may evaluate types at runtime — test thoroughly.
5. `collections.abc` imports (used in database.py, import_service.py) are fine in 3.9, but verify each import path.

**Detection:** `python3.9 -c "import backend.app.main"` will immediately fail on any problematic file.

---

### Pitfall 3: `dict[str, ...]` and `list[...]` built-in generics fail at runtime on Python 3.9

**What goes wrong:** Python 3.9 supports `list[X]` and `dict[K, V]` in annotations only with `from __future__ import annotations`. Without it, `dict[str, object]` raises `TypeError` at runtime. The codebase uses these generics pervasively in function signatures and variable annotations.

**Why it happens:** PEP 585 made built-in generics work at runtime in Python 3.10+, but 3.9 only supports them as string annotations (via `__future__`). Most app files have the import, but test files and alembic migrations may not.

**Consequences:** Same crash as Pitfall 2 — immediate `TypeError` on import.

**Prevention:**
1. Same `from __future__ import annotations` audit as Pitfall 2.
2. Alembic migration files (versions/) already use `Sequence` and `Union` from typing — verify any new migrations follow this pattern.
3. For runtime-evaluated annotations (FastAPI dependency injection, Pydantic schema construction), verify the framework handles deferred annotations correctly under 3.9.

**Detection:** Full import scan under Python 3.9.

---

### Pitfall 4: Dark mode breaks 329 hardcoded inline styles across 22 page files

**What goes wrong:** The codebase has 329 occurrences of `style={...}` across 22 page files with hardcoded colors like `background: '#F5F6F7'`, `color: '#1F2329'`, `borderBottom: '1px solid #DEE0E3'`. The MainLayout itself has hardcoded `background: '#fff'` and `background: '#F5F6F7'` in inline styles. These ignore Ant Design's theme tokens and will remain light-colored in dark mode.

**Why it happens:** v1.0 Phase 8 did a "full page rebuild" using inline styles for development speed. The `theme/index.ts` defines tokens but they are only consumed by Ant Design components, not by inline styles in page code.

**Consequences:** Dark mode toggle changes Ant Design component colors but leaves page backgrounds, card borders, text colors, and layout chrome in light mode. The result looks broken — white content areas floating in a dark shell, unreadable text on wrong backgrounds.

**Prevention:**
1. Before implementing dark mode, refactor inline color styles to use Ant Design's `token` via `theme.useToken()` hook or CSS custom properties.
2. Prioritize the MainLayout (Header background, Content background, Sider logo text) — this is the shell wrapping everything.
3. For page-level styles, create a shared pattern: `const { token } = theme.useToken()` and replace hardcoded hex values.
4. Do NOT attempt dark mode until at least MainLayout and top-5 most-used pages (Dashboard, DataManagement, SimpleAggregate, Imports, Employees) have their inline styles tokenized.
5. Ant Design 5's `ConfigProvider` supports `theme.algorithm: theme.darkAlgorithm` — use this as the toggle mechanism, but understand it only affects components, not inline styles.

**Detection:** Visually test every page in dark mode. Grep for hardcoded hex colors in `.tsx` files: `#F5F6F7`, `#FFFFFF`, `#fff`, `#1F2329`, `#DEE0E3`, `#646A73`.

---

### Pitfall 5: Responsive retrofit breaks complex social insurance data tables

**What goes wrong:** Social insurance data tables have 15-25 columns (pension_company, pension_personal, medical_company, medical_personal, unemployment_company, etc.). On mobile or narrow windows, these tables become completely unusable. Naive responsive approaches (hiding columns, wrapping text) lose critical data visibility that HR users depend on.

**Why it happens:** Ant Design Table does not automatically handle horizontal scrolling for many columns. The existing tables use fixed column definitions without `scroll={{ x: ... }}` or responsive column visibility logic.

**Consequences:** Mobile users see broken tables with overlapping columns. HR users on tablets cannot do their core work. Worse: if columns are hidden for responsive layout, users may not realize data is missing and make decisions on incomplete information.

**Prevention:**
1. Do NOT hide insurance columns to fit mobile screens. Instead: use `scroll={{ x: true }}` with a fixed left column (person_name) for horizontal scrolling on narrow screens.
2. For mobile-first views, consider a card-based layout showing summary (name, total_amount, company_total, personal_total) with expandable detail for per-insurance-type breakdown.
3. Test with real data widths — Chinese insurance field names are long (e.g., "职工基本养老保险(单位缴纳)") and numeric values have decimal places.
4. The DataManagement page has cascading filters (region + company + period) — these Row/Col layouts need responsive breakpoints. Use Ant Design's `<Col xs={24} sm={12} lg={8}>` pattern.
5. The SimpleAggregate page has a multi-step upload flow with WorkflowSteps — test this on mobile.

**Detection:** Resize browser to 375px width and verify every page is usable. Test on actual mobile device with touch interactions.

---

## Moderate Pitfalls

### Pitfall 6: Account management CRUD without self-demotion protection

**What goes wrong:** Adding account management (create/edit/delete users, change roles, reset passwords) to the existing JWT auth system. An admin accidentally changes their own role to 'hr' or 'employee', or deletes their own account, locking themselves out of the system.

**Prevention:**
1. Prevent admins from changing their own role or deactivating their own account via API-level validation.
2. Require at least one admin account to exist at all times — block the last admin from being demoted or deleted.
3. Password changes for other users should not invalidate existing JWT tokens immediately (tokens are stateless). Consider adding a `password_changed_at` field and checking it during token verification to force re-login.
4. The existing `user_service.py` has `create_user` and `authenticate_user_login` but no `update_user` or `delete_user` — these need careful implementation with the above guards.

### Pitfall 7: Cascade delete deletes more than intended (month data cleanup ambiguity)

**What goes wrong:** The v1.1 feature "batch delete cascading to month data" is ambiguous. If it means deleting a batch should also clean up all data for that billing_period, a billing_period may contain records from multiple batches. Naive implementation could delete records belonging to batch B when only batch A is being targeted.

**Prevention:**
1. Cascade delete should ONLY delete records belonging to the specific batch, not all records for the billing_period.
2. The current ImportBatch model already has `cascade="all, delete-orphan"` on normalized_records relationship — this correctly scopes deletion to the batch's own records. Use this mechanism.
3. If the feature intent is "delete all data for a month" (not just one batch), implement this as a separate service method that explicitly queries by billing_period, NOT by cascading from batch delete.
4. Add a confirmation step in the UI that shows exactly what will be deleted (X records from Y batches for period Z) before executing.
5. Log every cascade delete operation in the audit trail with the full scope of what was deleted.

### Pitfall 8: Dark mode theme duplication and drift

**What goes wrong:** Creating a separate `darkTheme` object that duplicates all token values from the light theme but with dark colors. Over time, the two theme objects drift — new component customizations get added to light theme but not dark, causing visual inconsistencies.

**Prevention:**
1. Use Ant Design 5's built-in dark algorithm: `{ algorithm: theme.darkAlgorithm }` as the primary mechanism — it automatically derives dark variants.
2. Keep ONE base theme config (the existing `theme/index.ts`) and compose dark mode as an override layer, not a copy.
3. Structure: `const darkOverrides: ThemeConfig = { algorithm: theme.darkAlgorithm, token: { /* only explicit overrides */ }, components: { /* only explicit overrides */ } }`.
4. The existing Feishu-style dark sider (`siderBg: '#1F2329'`) is already dark — in dark mode, the sider should stay similar while the content area darkens. Test that the sider doesn't become indistinguishable from content background.

### Pitfall 9: Diff-style comparison UI performance with large datasets

**What goes wrong:** The "left-right Excel table + diff highlighting" approach for monthly comparison renders two full tables side-by-side. With 500+ employee records per period and 20+ columns, this means rendering 20,000+ cells with diff computation. React re-renders on scroll and filter become visibly sluggish.

**Prevention:**
1. Use virtualized tables (`react-window` or Ant Design's `virtual` prop on Table) for both sides.
2. Compute diffs server-side and send only diff metadata (changed cells, added/removed rows), not raw data for client-side diffing.
3. The existing `PeriodCompare.tsx` already fetches diff data from the backend `compare_service.py` — extend this pattern rather than building client-side diffing from scratch.
4. For the "Excel-like" visual experience, consider `react-data-grid` or similar, but weigh the added dependency against Ant Design Table's virtual mode.

### Pitfall 10: Menu reorganization breaks bookmarked URLs and browser history

**What goes wrong:** Moving menu items into sub-menus or "advanced settings" changes the URL structure. Users who bookmarked `/audit-logs` or `/api-keys` get 404s. The existing `App.tsx` routes are flat — no nested route groups.

**Prevention:**
1. Keep existing URLs unchanged. Menu reorganization should only affect visual grouping in the sidebar, not route paths.
2. Use Ant Design Menu's items with `children` for visual nesting while keeping `key` values as the same flat paths.
3. If URLs must change, add permanent redirects from old paths to new paths in the router.
4. The `LABEL_MAP` in MainLayout.tsx and `ALL_NAV_ITEMS` array both need updating for any new groupings — keep them in sync.

### Pitfall 11: `from __future__ import annotations` breaks Pydantic model validation edge cases

**What goes wrong:** Adding `from __future__ import annotations` to schema files for Python 3.9 compatibility can break Pydantic v2 model validation. When annotations are deferred (become strings), Pydantic v2 must evaluate them at model creation time. Edge cases with complex validators, `model_validator`, `Literal`, and discriminated unions can fail.

**Prevention:**
1. Test every Pydantic schema file individually after adding the import.
2. Pay special attention to files using `Literal`, discriminated unions, or custom validators.
3. The existing schemas (auth.py, users.py, data_management.py, etc.) appear straightforward, but run the full test suite after changes.
4. If issues arise, use `typing.Optional` and `typing.Union` explicitly instead of relying on `__future__` for those specific files.

### Pitfall 12: Settings search exposes admin-only settings to lower roles

**What goes wrong:** A global settings search indexes all settings pages. If search results include links to admin-only pages (API Keys, Feishu Settings, Audit Logs), HR or employee users see results they cannot access, leading to confusing 403 errors or automatic redirects.

**Prevention:**
1. Filter search results by the current user's role using the existing `RoleRoute` allowedRoles logic.
2. Index settings with role metadata so search only returns accessible items.
3. The existing `ALL_NAV_ITEMS` array in MainLayout.tsx already has `roles` per item — reuse this as the search index with role filtering built in.

---

## Minor Pitfalls

### Pitfall 13: CSS module isolation insufficient for dark mode propagation

**What goes wrong:** Only 2 CSS module files exist (MainLayout.module.css, animations.module.css). All other styling is inline. Dark mode CSS variable propagation only works through CSS files or the theme token system, not through inline style objects.

**Prevention:** Accept that dark mode implementation requires a style refactoring pass first. Budget time for this preparatory work in the roadmap — it is not optional.

### Pitfall 14: Responsive sidebar overlay on mobile doesn't close on navigation

**What goes wrong:** On mobile, the sidebar should overlay content and close after a menu item is clicked. The existing `useResponsiveCollapse` hook collapses the sider at 1440px but doesn't implement drawer behavior for small screens.

**Prevention:** For mobile (<768px), switch from `Sider` to Ant Design's `Drawer` component. Trigger `onClose` on route change via `useEffect` on `location.pathname`.

### Pitfall 15: Employee self-service portal overlooked in responsive design

**What goes wrong:** The employee role only has one page (`/employee/query`) which is the most likely to be accessed on a phone (employees checking their social insurance on mobile). But responsive design efforts focus on admin/HR pages because they have more visual complexity.

**Prevention:** Prioritize the EmployeeSelfService page for mobile responsiveness — it is the highest-value mobile use case. Design it mobile-first.

### Pitfall 16: Audit log real IP fix breaks behind reverse proxy

**What goes wrong:** The v1.1 feature "audit log real IP address" reads client IP from `request.client.host`. Behind a reverse proxy (nginx, cloud load balancer), this returns `127.0.0.1` or the proxy's internal IP.

**Prevention:** Use `X-Forwarded-For` header with a trusted proxy configuration. FastAPI's `Request.client.host` is not sufficient alone. Add a configurable `TRUSTED_PROXIES` environment variable. Use the `X-Real-IP` header as fallback.

### Pitfall 17: Dark mode preference not persisted across sessions

**What goes wrong:** User toggles dark mode, refreshes page, and it resets to light mode.

**Prevention:** Store preference in `localStorage`. Load it before initial React render to prevent flash of wrong theme (FOWT). Use `prefers-color-scheme` media query as the initial default for first-time visitors.

### Pitfall 18: Fusion personal insurance/housing fund amounts break Salary template

**What goes wrong:** Adding personal social insurance and personal housing fund contribution fields to the fusion pipeline. The Salary template export is explicitly marked as "must not be modified" in project constraints. Adding new fields could accidentally change the Salary export mapping.

**Prevention:** The fusion enhancement should only affect data ingestion and storage. Salary exporter must remain completely untouched. Add new fields to normalized_records if needed, but ensure the Salary exporter's field list is frozen. Write a regression test asserting the Salary template output is byte-identical before and after the fusion enhancement.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Python 3.9 compat | Pitfall 2, 3, 11 — union types, built-in generics, Pydantic interaction | Do this FIRST. Run full test suite under 3.9. Systematic `__future__` audit across all files. |
| Dark mode | Pitfall 4, 8, 13, 17 — inline styles, theme duplication, CSS modules, persistence | Refactor inline styles to tokens BEFORE enabling dark toggle. Budget 2x estimated time. |
| Responsive design | Pitfall 5, 14, 15 — data tables, mobile sidebar, employee portal | Start with layout shell (MainLayout), then employee portal, then data pages. Never hide insurance columns. |
| Cascade delete | Pitfall 1, 7 — SQLite FK enforcement, scope of deletion | Write integration tests first. Verify PRAGMA. Separate batch-delete from period-delete semantics. |
| Account management | Pitfall 6 — self-demotion, last-admin protection | Add guard rails before CRUD. Token invalidation strategy needed. |
| Diff comparison UI | Pitfall 9 — performance with large datasets | Server-side diff computation. Virtualized rendering. |
| Menu reorganization | Pitfall 10 — broken bookmarks | Visual-only grouping, keep flat URL paths. |
| Settings search | Pitfall 12 — role-based filtering | Reuse existing NAV_ITEMS roles array as search index. |
| Audit log fix | Pitfall 16 — reverse proxy IP | X-Forwarded-For + trusted proxy config. |
| Fusion enhancements | Pitfall 18 — Salary template regression | Freeze Salary exporter, regression test with byte-identical output check. |

---

## Integration Pitfalls (Cross-Feature Interactions)

### Dark mode + Responsive design timing

**Risk:** If responsive design is done first with new inline styles, then dark mode has to re-refactor those same styles. If dark mode is done first, responsive breakpoints may need to account for both themes.

**Mitigation:** Do the inline-style-to-token refactoring as a preparatory phase before either feature. This single refactoring step enables both features cleanly.

### Python 3.9 compat + All subsequent backend features

**Risk:** If Python 3.9 compat is done late, all new code written for cascade delete, account management, and fusion enhancements may use 3.10+ syntax, requiring a second audit pass.

**Mitigation:** Do Python 3.9 compat FIRST. Set up CI to test on 3.9 so all subsequent work is automatically validated against the target runtime.

### Account management + Audit logs

**Risk:** New account CRUD operations (create user, change role, change password, delete user) should generate audit log entries. If audit log enhancement and account management are in different phases, the audit entries are likely to be forgotten.

**Mitigation:** Define audit event types for account operations upfront. Implement audit logging as part of the account management feature, not as a separate effort.

### Cascade delete + Data management filters

**Risk:** The "data management multi-select filter + matched/unmatched filter" feature changes how data is queried. If cascade delete introduces soft-delete patterns (is_deleted flags), all existing filter queries need to exclude soft-deleted records.

**Mitigation:** Use hard deletes (matching the existing CASCADE pattern in the models) rather than soft deletes. This avoids complicating every existing query with `WHERE is_deleted = false`.

### Fusion enhancements + Feishu sync

**Risk:** Adding personal insurance/housing fund amounts to fusion output changes the data model. If Feishu sync pushes these records to Bitable, the field mapping configuration needs updating. Implementing both features independently could leave Feishu sync unaware of new fields.

**Mitigation:** Define the extended data model (with new personal contribution fields) before implementing either feature. Both fusion and Feishu sync should target the same schema.

---

## Sources

- Direct codebase inspection: `backend/app/core/database.py` lines 29-36 (PRAGMA foreign_keys enforcement)
- Direct codebase inspection: `backend/app/models/import_batch.py` (ForeignKey + cascade="all, delete-orphan" declarations)
- Direct codebase inspection: 30+ backend service files with `X | Y` type syntax (grep results documented above)
- Direct codebase inspection: `frontend/src/theme/index.ts` (hardcoded Feishu-style theme tokens, no dark variant)
- Direct codebase inspection: `frontend/src/layouts/MainLayout.tsx` (inline styles with hardcoded hex colors, useResponsiveCollapse hook)
- Direct codebase inspection: 22 page files with 329 inline style occurrences (grep count documented above)
- Direct codebase inspection: `backend/app/services/user_service.py` (existing create_user/authenticate, no update/delete)
- SQLite documentation: PRAGMA foreign_keys default-off behavior (HIGH confidence, well-documented)
- Python 3.9 release notes: PEP 585 built-in generic limitations (HIGH confidence)
- Ant Design 5 theming documentation: darkAlgorithm + ConfigProvider pattern (HIGH confidence)

---

*Pitfalls audit: 2026-04-04 (v1.1 milestone)*
