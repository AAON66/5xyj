# Architecture Patterns

**Domain:** v1.1 体验优化与功能完善 -- 集成架构分析
**Researched:** 2026-04-04

## Current Architecture Overview

```
Frontend (React 18 + Ant Design 5 + Vite)
  main.tsx
    ConfigProvider(theme, locale=zhCN)  <-- theme injection point
      AntApp
        BrowserRouter
          AuthProvider (context)
            ApiFeedbackProvider (context)
              App.tsx (Routes)
                MainLayout (Sider + Header + Content)
                  Outlet -> page components

Backend (FastAPI 0.115 + SQLAlchemy 2.0 + SQLite WAL)
  api/v1/router.py  ->  routers: auth, users, imports, aggregate, ...
  services/         ->  business logic layer
  models/           ->  SQLAlchemy ORM models
  schemas/          ->  Pydantic schemas
  parsers/          ->  Excel parsing pipeline
  exporters/        ->  Salary + Tool template exporters
  validators/       ->  Non-detail row filter, validation
  mappings/         ->  Field alias rules
```

**Key architectural facts:**
- 24 page components in `frontend/src/pages/`
- 14 flat navigation items in MainLayout + dynamic Feishu items
- Theme is a single static `ThemeConfig` in `theme/index.ts`, injected once via ConfigProvider
- MainLayout has responsive sidebar collapse via `useResponsiveCollapse(1440)` -- but no mobile drawer mode
- Backend users API is fully implemented (CRUD + password reset) with no frontend consumer
- `from __future__ import annotations` in all 128 backend Python files
- 10 `@dataclass(slots=True)` usages across 5 files -- Python 3.10+ only feature

## Feature Integration Map

### 1. Responsive Design (Full-Page)

**Current state:** MainLayout has `useResponsiveCollapse(1440)` for sidebar auto-collapse. Individual pages use Ant Design `Row/Col` with `xs/sm/md/lg` breakpoints (e.g., Compare.tsx `<Col xs={24} md={12}>`). CSS modules are minimal (only `MainLayout.module.css`).

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Sidebar breakpoint for mobile | `MainLayout.tsx` `useResponsiveCollapse` | Modify -- add Drawer mode at ~768px |
| Header layout | `MainLayout.tsx` Header inline styles | Modify -- stack breadcrumb/user on mobile |
| Content padding | `MainLayout.tsx` Content `padding: '24px'` | Modify -- reduce on mobile |
| Page-level responsive | Each page in `pages/` (24 files) | Modify -- audit all pages |
| Table horizontal scroll | Pages with Ant `Table` | Modify -- add `scroll={{ x: true }}` |
| Card grid layouts | Dashboard, DataManagement, etc. | Modify -- verify Col breakpoints |

**New components needed:**
- `hooks/useBreakpoint.ts` -- centralized responsive breakpoint hook. Wraps Ant Grid's `useBreakpoint` or `window.matchMedia`. Multiple pages need consistent breakpoint logic.

**Approach:**
1. MainLayout: mobile sidebar becomes Ant Drawer below 768px, triggered by hamburger icon in Header
2. Header: compact layout on mobile (hamburger + breadcrumb, user menu collapses)
3. Each page: audit table columns (hide low-priority on mobile), enable horizontal scroll
4. SimpleAggregate file upload area must work on mobile

**Risk:** 24 page files need individual auditing. Some pages (Compare.tsx at 870 lines) have complex custom layouts that don't use Ant Grid consistently.

---

### 2. Dark Mode Toggle

**Current state:** Theme defined in `frontend/src/theme/index.ts` as static `ThemeConfig`. Colors are hardcoded in inline styles throughout MainLayout (e.g., `background: '#fff'`, `borderBottom: '1px solid #DEE0E3'`, `background: '#F5F6F7'`). Module CSS also hardcodes colors (`.logo { color: #fff }`).

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Theme config | `theme/index.ts` | Modify -- export light + dark ThemeConfig |
| Theme provider | `main.tsx` ConfigProvider | Modify -- dynamic theme switching |
| Theme context | New | **New** -- ThemeProvider with localStorage persistence |
| Toggle button | `MainLayout.tsx` Header | Modify -- add sun/moon toggle |
| Inline style colors | `MainLayout.tsx` + ~15 pages | Modify -- replace hardcoded colors with tokens |
| Module CSS colors | `MainLayout.module.css` | Modify -- use CSS variables |
| Sider theme prop | `MainLayout.tsx` `<Sider theme="dark">` | Evaluate -- may need dynamic theme prop |

**New files needed:**
- `theme/darkTheme.ts` -- dark mode token overrides
- `hooks/useThemeMode.ts` -- theme mode state + localStorage persistence

**Approach:** Ant Design 5 has first-class dark mode via `algorithm: theme.darkAlgorithm`:

```typescript
import { theme as antTheme } from 'antd';

export const darkTheme: ThemeConfig = {
  ...lightTheme,
  algorithm: antTheme.darkAlgorithm,
  token: { /* dark-specific overrides */ },
  components: {
    Layout: { siderBg: '#141414', ... },
  },
};
```

**Critical prerequisite:** All inline `style={{ background: '#fff' }}` and hardcoded color values MUST be replaced with Ant Design token references (`token.colorBgContainer`, etc.) or they will look broken in dark mode. This "color extraction" work is the largest effort and MUST come before the dark mode toggle itself.

**Estimated touch points:** MainLayout + ~15 pages with hardcoded colors.

---

### 3. Diff-Style Comparison (Redesign)

**Current state:** `Compare.tsx` (870 lines) renders comparison as card-per-row with tabs (left/right) and inline Input fields for cell editing. Backend `compare_service.py` returns `CompareRowRead` with `left`/`right` record sides, `diff_status`, and `different_fields`. Backend is well-structured; the redesign is purely frontend.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Compare page UI | `pages/Compare.tsx` | **Rewrite** -- dual-panel Excel layout |
| Compare service API | `services/compare.ts` | Keep -- API contract unchanged |
| Backend compare_service | `services/compare_service.py` | Keep -- no changes needed |
| Field label map | `pages/Compare.tsx` FIELD_LABELS | Extract to shared constant |

**New components needed:**
- `components/DiffTable.tsx` -- reusable side-by-side diff table
- `components/DiffCell.tsx` -- cell-level diff highlighting

**Target UX:** "左右 Excel 表格 + 差异高亮"

```
+--------+---------------------------+---+---------------------------+
| Status | Left (Base)               |   | Right (New)               |
+--------+---------------------------+---+---------------------------+
| same   | 张三 | 1000 | 500        |   | 张三 | 1000 | 500        |
| diff   | 李四 | [800] | 400       | > | 李四 | [900] | 400       |
| left   | 王五 | 700 | 350         |   |      |      |            |
| right  |      |      |            |   | 赵六 | 600 | 300         |
+--------+---------------------------+---+---------------------------+
```

Two synchronized scrolling tables. Changed cells get background highlighting (red for removed, green for added, yellow for changed). Row-level status indicators in gutter column. Scroll sync via `onScroll` + `requestAnimationFrame`.

**Backend is already sufficient.** `CompareRowRead` has `left.values`, `right.values`, `different_fields`, `diff_status`. No API changes required.

---

### 4. Account Management (Admin CRUD)

**Current state:** Backend already has full CRUD in `api/v1/users.py`: create, list, get by ID, update, reset password. `user_service.py` has all business logic. `User` model has username, hashed_password, role, display_name, is_active, must_change_password, feishu_open_id. **There is NO frontend page for this.** The API is fully implemented but unconsumed by the frontend.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| New page | `pages/UserManagement.tsx` | **New** |
| Route | `App.tsx` | Modify -- add admin-only route |
| Navigation | `MainLayout.tsx` ALL_NAV_ITEMS | Modify -- add nav item |
| Frontend service | `services/users.ts` | **New** -- API client |
| Backend | `api/v1/users.py`, `user_service.py` | **Keep** -- already complete |

**New files needed:**
- `pages/UserManagement.tsx` -- CRUD table with create modal, edit drawer, password reset
- `services/users.ts` -- API client (createUser, listUsers, updateUser, resetPassword)

**Approach:** Standard Ant Design CRUD page:
- Table listing users (username, display_name, role, is_active, created_at)
- "Create" button -> Modal with form
- Row actions: Edit, Reset Password, Toggle Active
- Admin-only route at `/users`

**This is the simplest feature.** Backend is 100% done; just needs frontend page + API client.

---

### 5. Python 3.9 Compatibility

**Current state:** Development runs Python 3.14. All 128 backend Python files use `from __future__ import annotations`, which means type hints like `list[str]` are strings at runtime and won't break on 3.9.

**Incompatibilities found:**

| Issue | Files Affected | Severity |
|-------|---------------|----------|
| `@dataclass(slots=True)` | 10 usages in 5 files: `header_extraction.py`, `workbook_discovery.py`, `export_utils.py`, `manual_field_aliases.py`, `non_detail_row_filter.py` | **Critical** -- requires Python 3.10+ |
| `@dataclass(frozen=True, slots=True)` | `compare_service.py`, `manual_field_aliases.py` | **Critical** -- same issue |
| `match/case` statements | **None found** | Safe |
| `X \| Y` union syntax at runtime | **None found** -- all behind `__future__` | Safe |

**Fix strategy:** Remove `slots=True` from all dataclass decorators. It's a micro-optimization (saves ~16 bytes per instance) with zero functional impact for an Excel processing tool. Keep `frozen=True` where present (available since Python 3.0).

```python
# Before (3.10+ only)
@dataclass(frozen=True, slots=True)
class CompareIdentity:
    basis: str
    value: str

# After (3.9 compatible)
@dataclass(frozen=True)
class CompareIdentity:
    basis: str
    value: str
```

**Dependency compatibility:** FastAPI 0.115, SQLAlchemy 2.0, pandas, openpyxl, PyJWT, pwdlib all support Python 3.9. No dependency blockers.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Dataclass slots | 5 backend files, 12 decorators | Modify -- remove `slots=True` |
| Dependencies | `requirements.txt` | Verify -- ensure all support 3.9 |
| CI/test | If exists | Modify -- add 3.9 target |

**This is the smallest change** -- 12 lines across 5 files.

---

### 6. Data Cascade Delete (Batch Delete -> Period Data Cleanup)

**Current state:** `delete_import_batch` in `import_service.py` deletes batch via `db.delete(batch)` + `db.commit()`, relying on SQLAlchemy cascade. Also cleans up file artifacts on disk. The `data_management` API is currently **read-only** (no delete endpoints).

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Period delete service | `services/data_management_service.py` | **New function** -- `delete_records_by_period()` |
| Period delete endpoint | `api/v1/data_management.py` | **New** -- DELETE endpoint |
| Batch delete cascade verification | `models/import_batch.py` relationships | Verify -- ensure cascade="all, delete-orphan" |
| Frontend delete UI | `pages/DataManagement.tsx` | Modify -- add delete actions |
| Audit logging | `services/data_management_service.py` | **New** -- log deletions |

**Key design question:** When user says "delete period 2026-02", should we:
- (A) Delete NormalizedRecords only, keeping batch metadata -- simpler, but orphans batches
- (B) Find and delete entire batches belonging to that period -- cleaner, but a period can span multiple batches

**Recommendation:** Option A (delete records only) with a "batch cleanup" follow-up. Delete NormalizedRecords + related MatchResults + ValidationIssues for the period. Mark affected batches as "partially deleted" in status. This is safer and more granular.

```python
def delete_records_by_period(db: Session, billing_period: str, region: Optional[str] = None) -> int:
    query = db.query(NormalizedRecord).filter(NormalizedRecord.billing_period == billing_period)
    if region:
        query = query.filter(NormalizedRecord.region == region)
    count = query.count()
    # Also delete related match_results and validation_issues
    record_ids = [r.id for r in query.all()]
    db.query(MatchResult).filter(MatchResult.normalized_record_id.in_(record_ids)).delete(synchronize_session=False)
    db.query(ValidationIssue).filter(ValidationIssue.normalized_record_id.in_(record_ids)).delete(synchronize_session=False)
    query.delete(synchronize_session=False)
    db.commit()
    return count
```

---

### 7. Menu Reorganization (Multi-Level Collapsible)

**Current state:** `MainLayout.tsx` has flat `ALL_NAV_ITEMS` array (14 items + dynamic Feishu). Menu renders as `<Menu mode="inline">` with no nesting.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Menu structure | `MainLayout.tsx` ALL_NAV_ITEMS | **Rewrite** -- hierarchical structure |
| Menu builder | `MainLayout.tsx` buildMenuItems | Modify -- support nested children |
| Menu open state | `MainLayout.tsx` | Modify -- track `openKeys` for SubMenu |
| Role filtering | `MainLayout.tsx` buildMenuItems | Modify -- recursive role filtering |

**Proposed hierarchy:**

```
Core Operations:
  快速融合, 处理看板

Data Analysis:
  月度对比, 跨期对比, 异常检测

Data Management:
  批次管理, 数据管理, 映射修正, 校验匹配, 导出结果, 员工主档

Advanced Settings (collapsed by default):
  审计日志 (admin), API 密钥 (admin), 账号管理 (admin, NEW)
  飞书同步, 飞书设置 (admin)
```

**Implementation:** Ant Design Menu supports `children` for SubMenu. Role filtering must work recursively -- hide a SubMenu group if ALL its children are hidden for the current role.

---

### 8. Settings Search + Quick Navigation

**Current state:** No unified settings page. Settings spread across FeishuSettings, ApiKeys, Mappings pages.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Settings page | `pages/Settings.tsx` | **New** |
| Route | `App.tsx` | Modify -- add route |
| Navigation | `MainLayout.tsx` | Modify -- add to Advanced Settings group |
| Search index | `config/settingsIndex.ts` | **New** |

**Approach:** Navigation hub page with a search input. Static list of settings entries with keywords. Typing filters entries, clicking navigates. Lightweight implementation.

---

### 9. Audit Log Improvements (Real IP)

**Current state:** `get_client_ip()` in `request_helpers.py` reads `X-Forwarded-For`, falls back to `request.client.host`. AuditLog model stores `ip_address` as `String(45)`.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| IP extraction | `utils/request_helpers.py` | Modify -- add X-Real-IP support |
| Audit log display | `pages/AuditLogs.tsx` | Verify -- IP column visible |
| Deployment docs | New | **New** -- trusted proxy config |

**Implementation:** Add `X-Real-IP` header priority (common with Nginx):

```python
def get_client_ip(request: Request) -> str:
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
```

---

### 10. Fusion Enhancements (Special Rules, File Count, Defaults)

**Current state:** `SimpleAggregate.tsx` has employee master mode selection (none/existing/upload). `aggregate_service.py` handles full pipeline. Current default employee master mode is selectable.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Special rules config UI | `pages/SimpleAggregate.tsx` | Modify -- add rules section |
| Special rules backend | `services/aggregate_service.py` | Modify -- apply rules post-normalization |
| Special rules model | `models/special_rule.py` | **New** -- persist saved rules |
| Special rules API | `api/v1/aggregate.py` or new router | **New** -- CRUD for rule sets |
| File count display | `pages/SimpleAggregate.tsx` | Modify -- show count badge |
| Default employee master | `pages/SimpleAggregate.tsx` | Modify -- change default to "existing" |
| Insurance base fix | `services/normalization_service.py` | Modify |

**Special rules spec:** "选人+选字段+覆盖值，可保存复用"

**New model:**
```python
class SpecialRule(Base):
    __tablename__ = "special_rules"
    id: Mapped[str]             # UUID
    name: Mapped[str]           # Rule set name
    rules_json: Mapped[str]     # JSON: [{employee_filter, field, override_value}]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**Application point:** After normalization, before export -- iterate rules, find matching records by employee filter, override specified fields.

---

### 11. Data Management Filter Enhancements

**Current state:** Single-select cascading filters (region -> company -> period). Backend uses `==` comparison.

**Integration points:**

| What | Where | Change Type |
|------|-------|-------------|
| Multi-select filters | `pages/DataManagement.tsx` | Modify -- `Select mode="multiple"` |
| Backend filter params | `api/v1/data_management.py` | Modify -- accept comma-separated values |
| Backend query | `services/data_management_service.py` | Modify -- `.in_()` instead of `==` |
| Match status filter | `pages/DataManagement.tsx` | Modify -- add toggle |
| Match status query | `services/data_management_service.py` | Modify -- join MatchResult |

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **ThemeProvider** (new) | Dark/light mode state + localStorage persistence | ConfigProvider, MainLayout |
| **useBreakpoint** (new) | Centralized responsive breakpoints | All page components |
| **DiffTable** (new) | Side-by-side comparison Excel-style rendering | Compare page |
| **UserManagement** (new page) | Account CRUD UI | users API service |
| **SpecialRulesEditor** (new component) | Rule set creation/editing | aggregate API |
| **SettingsHub** (new page) | Searchable settings navigation | Router |
| **MainLayout** (modified) | Menu hierarchy, mobile drawer, dark mode toggle, responsive header | All pages |
| **SpecialRule** (new model) | Persist reusable override rules | aggregate_service |

## Data Flow Changes

### Existing Flow (unchanged)
```
Upload -> Parse -> Normalize -> Validate -> Match -> Export
```

### New Flows

**Special Rules Application:**
```
SpecialRulesEditor -> POST /api/v1/special-rules -> DB (save)
SimpleAggregate -> aggregate_service -> normalize -> apply_special_rules(records, rules) -> Export
```

**Cascade Delete:**
```
DataManagement -> DELETE /api/v1/data-management/records?period=X
  -> delete NormalizedRecords WHERE billing_period = X
  -> cascade delete related MatchResults, ValidationIssues
  -> audit_log entry
```

**Dark Mode:**
```
User toggles -> useThemeMode -> localStorage + state
  -> ConfigProvider re-renders with darkTheme/lightTheme
  -> All Ant Design components auto-adapt
  -> Custom inline styles / CSS must already use token variables
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Hardcoded Colors in Inline Styles
**What:** `style={{ background: '#fff' }}` instead of Ant Design tokens
**Why bad:** Breaks dark mode, creates maintenance burden
**Instead:** Use `token.colorBgContainer` via `useToken()` hook or CSS custom properties

### Anti-Pattern 2: Per-Page Responsive Logic
**What:** Each page implementing its own breakpoint detection
**Why bad:** Inconsistent breakpoints, duplicated code
**Instead:** Central `useBreakpoint` hook with shared breakpoint constants

### Anti-Pattern 3: Synchronized Scroll via setTimeout
**What:** Syncing two scrollable containers with timers
**Why bad:** Janky, race conditions
**Instead:** `onScroll` event + `requestAnimationFrame` + `scrollLeft` assignment

### Anti-Pattern 4: Deleting Records Without Audit Trail
**What:** Cascade delete without logging
**Why bad:** Violates audit requirements, no recovery information
**Instead:** Log counts, period, affected batches to audit_log BEFORE deletion

### Anti-Pattern 5: Dark Mode as Afterthought
**What:** Adding dark mode toggle without first extracting hardcoded colors
**Why bad:** Toggle works but half the UI is still white/hardcoded
**Instead:** Phase the work: extract colors to tokens FIRST, then add toggle

## Suggested Build Order

Based on dependency analysis and risk:

```
Phase 1: Foundation (no cross-dependencies)
  1. Python 3.9 compatibility (remove slots=True) -- deployment prerequisite
  2. Audit log IP improvement -- isolated 1-file backend change
  3. Account management page -- backend done, just frontend + API client

Phase 2: Theme System (prerequisite for dark mode + responsive)
  4. Theme token extraction (replace all hardcoded colors with Ant tokens)
  5. Dark mode toggle (ThemeProvider + theme switching)
  6. Responsive design (MainLayout mobile drawer + page audits)
  7. Menu reorganization (hierarchy + mobile hamburger)

Phase 3: Feature Enhancements
  8. Diff-style comparison redesign (page rewrite)
  9. Data management filters (multi-select, match status filter)
  10. Data cascade delete (new endpoint + UI)
  11. Settings search page

Phase 4: Fusion & Polish
  12. Special rules config (new model + API + UI)
  13. File count display + employee master default change
  14. Personal insurance base data fix
  15. Feishu frontend enhancements
  16. v1.0 tech debt cleanup (5 deprecated component files)
```

**Phase ordering rationale:**
- Python 3.9 is Phase 1 because it blocks cloud deployment
- Theme token extraction MUST precede dark mode (extracting hardcoded colors is a prerequisite)
- Responsive and dark mode share "remove hardcoded styles" work, so adjacent phases
- Menu reorg pairs with responsive (mobile hamburger trigger)
- Diff comparison is self-contained, no deps on other features
- Special rules are the most complex new feature (new model + CRUD + application logic)
- Tech debt cleanup is lowest priority, can slot anywhere

## Scalability Considerations

| Concern | Current (v1.1) | Future (v2.0) |
|---------|----------------|---------------|
| Dark mode system | Ant Design CSS-in-JS tokens | Could add custom branded themes |
| Menu structure | Static hierarchical config | Could load from backend/permissions |
| Comparison rendering | Client-side diff | Virtual scroll for 1000+ row comparisons |
| Special rules | JSON column in SQLite | Full rules engine with conditions |
| Cascade delete | Direct SQL delete | Soft-delete for recovery in multi-tenant |

## Sources

- Codebase analysis (HIGH confidence): `MainLayout.tsx`, `theme/index.ts`, `main.tsx`, `App.tsx`, `compare_service.py`, `Compare.tsx`, `users.py`, `user_service.py`, `audit_service.py`, `data_management_service.py`, `import_service.py`, `request_helpers.py`, all backend model files
- `@dataclass(slots=True)` Python 3.10 requirement (HIGH confidence): verified via Python language spec
- `from __future__ import annotations` coverage (HIGH confidence): verified 128/128 backend files
- Ant Design 5 dark mode via `theme.darkAlgorithm` (HIGH confidence): standard Ant Design 5 feature, codebase already uses ConfigProvider with ThemeConfig
- Ant Design Menu SubMenu/children support (HIGH confidence): standard Ant Design 5 feature

---

*Architecture research for v1.1: 2026-04-04*
