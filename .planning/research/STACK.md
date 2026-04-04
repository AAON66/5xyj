# Technology Stack -- v1.1 Additions

**Project:** Social Security Aggregation Tool v1.1
**Researched:** 2026-04-04
**Focus:** Stack changes/additions for responsive design, dark mode, diff comparison, account management, Python 3.9 compat, settings search, fusion special rules

---

## Executive Summary

v1.1 requires **zero new npm/pip dependencies**. The existing stack (Ant Design 5 + FastAPI 0.115) already provides built-in solutions for responsive design, dark mode, and account CRUD. The diff comparison panel is a custom UI build on existing Ant Design Table, not a library addition. Python 3.9 compatibility is achievable by pinning upper bounds on two packages and adding `from __future__ import annotations` to 15 remaining files.

**Key insight: This milestone is about using what we have better, not adding new tools.**

---

## Recommended Stack Changes

### Frontend -- Zero New Libraries

| Feature | Solution | Source | Why |
|---------|----------|--------|-----|
| Responsive design | `Grid.useBreakpoint()` from `antd` | Built-in since AntD 5.1+ | Already in `antd ^5.29.3`; provides `xs/sm/md/lg/xl/xxl` breakpoint booleans |
| Dark mode toggle | `theme.darkAlgorithm` from `antd` | Built-in AntD 5 | Pass `algorithm: theme.darkAlgorithm` to `ConfigProvider`. Derives dark tokens from seed colors automatically |
| Diff comparison panel | Custom build with Ant Design `Table` + cell styling | See Architecture below | This is **tabular data diff** (comparing insurance amounts), NOT code diff. AntD Table `onCell` is sufficient |
| Settings search | `Array.filter()` on settings metadata | Pure logic | Settings are a finite list (~15 items). No fuzzy search library needed |
| Multi-level sidebar | `Menu` with `children` items from `antd` | Built-in | Ant Design Menu already supports nested SubMenu/children |
| Account management | `Table` + `Modal` + `Form` from `antd` | Built-in | Standard CRUD pattern with existing components |
| Data filter multi-select | `Select` with `mode="multiple"` from `antd` | Built-in | Already available in current AntD version |

### Backend -- Zero New Libraries

| Feature | Solution | Source | Why |
|---------|----------|--------|-----|
| Account CRUD API | FastAPI endpoints + SQLAlchemy | Existing stack | User model already exists; add admin endpoints for create/update/delete |
| Fusion special rules | Python dict/JSON config in SQLite | Pure logic | Rules = "select person + select field + override value". Simple JSON column |
| Python 3.9 compat | Syntax adjustments + version pinning | See Compatibility section | No library changes needed |
| Audit log real IP | `X-Forwarded-For` header parsing | FastAPI built-in | Already have audit logging; just read the proxy header |
| Batch delete cascade | SQLAlchemy cascade deletes | Existing | Configure `cascade="all, delete-orphan"` on relationships |

---

## What NOT to Add

| Temptation | Why NOT | What to Do Instead |
|------------|---------|-------------------|
| `react-diff-viewer` / `react-diff-view` | These are **code/text diff** libraries. Our diff compares **tabular numeric data** (insurance amounts across months). Text diff output is unusable for spreadsheet data. | Custom dual Ant Design Table with cell-level background coloring (green=increase, red=decrease, blue=new, gray=removed) |
| Tailwind CSS | Conflicts with Ant Design's design token system. Two styling paradigms = confusion and maintenance burden. | Use Ant Design tokens + CSS modules (already in place) |
| `@ant-design/pro-components` | Heavy (~200KB), opinionated, would conflict with existing custom layout. ProTable's opinions clash with our custom table patterns. | Continue using base `antd` components |
| `ag-grid` / `handsontable` | 300KB+ bundle for one feature (diff panel). Commercial licenses for advanced features. | Ant Design Table with custom cell rendering |
| `zustand` / `jotai` / `redux` | Dark mode is a single boolean. Theme preference doesn't need a state management library. | `localStorage` + React Context or `useState` at App root |
| `react-responsive` | Duplicates `Grid.useBreakpoint()` already in Ant Design. | Use `Grid.useBreakpoint()` |
| `fuse.js` / `lunr` | Settings search covers ~15 items. Fuzzy search is overkill. | Simple `String.includes()` filter |
| `motion` / `framer-motion` | Already have CSS animations in `animations.module.css`. No new animation requirements in v1.1. | Keep existing CSS transitions |

---

## Python 3.9 Compatibility Assessment

**Verdict: ACHIEVABLE with minor pinning + 15 trivial file edits.**
**Confidence: HIGH**

### Current Codebase State

| Aspect | Status | Detail |
|--------|--------|--------|
| `from __future__ import annotations` | 92/107 files | Missing files: 14 `__init__.py` (empty/trivial) + 1 `enums.py` (uses no `X\|Y` syntax) |
| `X \| Y` type annotations | 483 occurrences / 58 files | ALL safe -- `__future__` annotations stores them as strings, never evaluated at runtime |
| `isinstance(x, A \| B)` runtime | **0 occurrences** | No runtime union operators -- safe |
| `StrEnum` (3.11+) | **0 occurrences** | Uses `(str, Enum)` pattern -- already 3.9-compatible |
| `match/case` (3.10+) | **0 occurrences** | No structural pattern matching -- safe |
| `tomllib` (3.11+) | **Not used** | No TOML parsing in codebase |
| Builtin generics (`list[x]`, `dict[x,y]`) | Present in annotations | Safe with `__future__` import (stored as strings) |

### Dependency Compatibility Matrix

| Package | Pinned Version | Python 3.9? | Action Required |
|---------|---------------|-------------|-----------------|
| FastAPI | 0.115.0 | YES (dropped at 0.130.0) | **Pin: `>=0.115.0,<0.130.0`** |
| pandas | 2.2.3 | YES (dropped at 2.3.0) | **Pin: `>=2.2.3,<2.3.0`** |
| SQLAlchemy | 2.0.36 | YES | No change |
| Pydantic | 2.10.3 | YES | No change |
| pydantic-settings | 2.6.1 | YES | No change |
| openpyxl | 3.1.5 | YES | No change |
| uvicorn | 0.32.0 | YES | No change |
| httpx | 0.28.1 | YES | No change |
| loguru | 0.7.3 | YES | No change |
| alembic | 1.14.0 | YES | No change |
| PyJWT | (current) | YES | No change |
| pwdlib | (current) | YES | No change |
| python-multipart | 0.0.12 | YES | No change |
| python-dotenv | 1.0.1 | YES | No change |

### Required Actions

1. **Pin upper bounds** in `requirements.txt`:
   ```
   fastapi>=0.115.0,<0.130.0
   pandas>=2.2.3,<2.3.0
   ```
2. **Add `from __future__ import annotations`** to 15 missing files (all are `__init__.py` or simple modules -- trivial)
3. **Verify no runtime annotation evaluation** -- already confirmed: 0 uses of `get_type_hints()` without `include_extras`, 0 `isinstance` with `|`
4. **Test on Python 3.9** in CI or local venv before deploying to cloud server

---

## Dark Mode Implementation Strategy

**Approach: Ant Design 5 `darkAlgorithm` -- zero new dependencies**
**Confidence: HIGH**

### How It Works

Ant Design 5's `ConfigProvider` accepts a `theme.algorithm` prop. Switching between `theme.defaultAlgorithm` and `theme.darkAlgorithm` regenerates ALL component tokens (backgrounds, text colors, borders, shadows) automatically from seed tokens.

### Integration Plan

Current `frontend/src/theme/index.ts` defines hardcoded light colors. The refactor:

1. **Extract seed tokens** (keep): `colorPrimary: '#3370FF'` (Feishu blue), `borderRadius: 8`, `fontSize: 14`
2. **Remove derived tokens** (let algorithm generate): `colorBgContainer`, `colorBgLayout`, `colorBgElevated`, `colorText`, `colorTextSecondary`, `colorBorder` -- these should be algorithm-derived
3. **Component tokens**: Some (like `Layout.siderBg: '#1F2329'`) may need conditional values -- dark sidebar in light mode, darker sidebar in dark mode
4. **CSS modules**: Any hardcoded colors in `.module.css` files need to use `var(--ant-color-*)` CSS variables or `useToken()` hook
5. **State**: Single `isDark` boolean in React Context, persisted to `localStorage`

### Known Caveats

- Some AntD components (Notification, certain modals) may not fully respect dark tokens -- test all paths
- The sidebar already uses `theme="dark"` on Menu -- behavior in dark mode needs verification
- Charts/visualizations (if any) need separate dark mode handling

---

## Responsive Design Strategy

**Approach: `Grid.useBreakpoint()` -- zero new dependencies**
**Confidence: HIGH**

### Breakpoints (Ant Design defaults, matching Bootstrap 4)

| Breakpoint | Width | Target Device |
|------------|-------|---------------|
| `xs` | <576px | Phone portrait |
| `sm` | >=576px | Phone landscape |
| `md` | >=768px | Tablet |
| `lg` | >=992px | Small laptop |
| `xl` | >=1200px | Desktop (current design target) |

### Custom Hook

```typescript
import { Grid } from 'antd';
export function useResponsive() {
  const screens = Grid.useBreakpoint();
  return {
    isMobile: !screens.md,      // xs, sm
    isTablet: screens.md && !screens.lg,  // md only
    isDesktop: !!screens.lg,     // lg, xl, xxl
  };
}
```

### Key Adaptations

| Component | Desktop | Mobile |
|-----------|---------|--------|
| Sidebar | Expanded with labels | Collapsed as overlay drawer |
| Data tables | Full columns | Horizontal scroll or card view |
| Forms | Horizontal labels | Vertical stacked |
| Header | Full breadcrumb + actions | Condensed with dropdown |
| Diff panel | Side-by-side tables | Stacked vertically |

---

## Diff Comparison Panel Strategy

**Approach: Custom dual Ant Design Table -- zero new dependencies**
**Confidence: MEDIUM** (implementation complexity, not library risk)

### Why NOT a Diff Library

The v1.0 `compare_service.py` already computes numeric differences between periods. The v1.1 ask is a **visual redesign** showing two months of insurance data side by side. This is fundamentally different from code diff:

- Code diff: text lines added/removed/changed
- Our diff: **tabular numbers** -- pension went from 1200 to 1500, person added, person removed

`react-diff-viewer` would render this as text lines, losing the tabular structure that makes insurance data readable.

### Architecture

Two synchronized `antd Table` components:
- Shared row keys (matched by employee ID)
- Synced vertical scroll via `onScroll` event forwarding
- Cell-level `className` via `onCell` callback:
  - Green background: value increased
  - Red background: value decreased
  - Blue row: person added in new period
  - Gray row: person removed in new period
  - No highlight: unchanged

---

## Fusion Special Rules

**Approach: SQLite JSON storage -- zero new dependencies**
**Confidence: HIGH**

### Data Model

```python
class FusionRule(Base):
    __tablename__ = "fusion_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]                     # Display name
    employee_ids: Mapped[str]             # JSON array: ["E001", "E002"]
    field_name: Mapped[str]               # Canonical field: "pension_personal"
    override_value: Mapped[str]           # Value to apply
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]
```

Applied during aggregation, after matching, before export. No new libraries needed.

---

## Settings Search

**Approach: Static metadata array with `String.includes()`**
**Confidence: HIGH**

~15 settings items. Build a `SETTINGS_INDEX` array with `key`, `label`, `keywords[]`, `path`. Filter client-side. No search library justified for this scale.

---

## Installation Changes

```bash
# Frontend: ZERO new packages
# npm install -- nothing

# Backend: ZERO new packages
# pip install -- nothing

# Only change: pin upper bounds in requirements.txt
# fastapi>=0.115.0,<0.130.0
# pandas>=2.2.3,<2.3.0
```

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Responsive design | HIGH | AntD `useBreakpoint` is built-in, well-documented, widely used |
| Dark mode | HIGH | AntD 5 `darkAlgorithm` is a first-class feature, verified in official docs |
| Diff panel | MEDIUM | Custom build -- scroll sync and cell styling need careful implementation |
| Account management | HIGH | Standard CRUD with existing User model + existing AntD components |
| Python 3.9 compat | HIGH | All deps verified compatible at pinned versions; `__future__` annotations already pervasive |
| Settings search | HIGH | Trivial feature, <20 items, no library needed |
| Fusion rules | HIGH | Simple data model + JSON config, pure backend logic |
| Multi-select filters | HIGH | AntD `Select mode="multiple"` is built-in |
| Menu reorganization | HIGH | AntD `Menu` with `children` nesting is built-in |

---

## Sources

- [Ant Design Customize Theme -- dark algorithm docs](https://ant.design/docs/react/customize-theme/)
- [Ant Design Grid -- useBreakpoint hook](https://ant.design/components/grid/)
- [Conditional Responsive Design with useBreakpoint](https://dev.to/sarwarasik/conditional-responsive-design-with-ant-designs-usebreakpoint-hook-2lim)
- [How to Toggle Dark Theme with Ant Design 5.0](https://betterprogramming.pub/how-to-toggle-dark-theme-with-ant-design-5-0-eb68552f62b8)
- [PEP 604 -- Union Types X | Y](https://peps.python.org/pep-0604/)
- [Python type hints old and new syntaxes](https://adamj.eu/tech/2022/10/17/python-type-hints-old-and-new-syntaxes/)
- [pandas 2.2.3 release notes (Python 3.9 support)](https://pandas.pydata.org/pandas-docs/stable/whatsnew/v2.2.3.html)
- [FastAPI release notes (Python 3.9 dropped at 0.130.0)](https://fastapi.tiangolo.com/release-notes/)
- [pandas 2.3.0 drops Python 3.9](https://github.com/pandas-dev/pandas/issues/61563)
