# Phase 7: Design System & UI Foundation - Research

**Researched:** 2026-03-30
**Domain:** Ant Design 5.x migration, Feishu-inspired theme, React component library integration
**Confidence:** HIGH

## Summary

Phase 7 is a one-shot visual migration of all 17 existing pages from hand-written CSS to Ant Design 5.x components with a Feishu-inspired theme. The current frontend is React 18.3.1 + React Router v6 + Vite, with ~7000 lines of page code using custom CSS classes (`panel-card`, `dashboard-pill`, `login-shell`, etc.) and 6 custom components (`AppShell`, `PageContainer`, `SectionState`, `GlobalFeedback`, `ApiFeedbackProvider`, `SurfaceNotice`). All of these must be replaced by Ant Design equivalents.

The migration is straightforward because: (1) antd 5.x is a mature, stable library with excellent React 18 support; (2) the existing pages already follow a card-based layout pattern that maps cleanly to Ant Design components; (3) no state management or API layer changes are needed -- only the view layer is being rewritten.

**Primary recommendation:** Install `antd@5.29.3` and `@ant-design/icons@5.6.1` (v5 compatible versions), create a centralized theme config with the Feishu tokens from UI-SPEC, build the MainLayout shell first (Layout+Sider+Header+Content), then migrate pages in priority order (Login > Dashboard > SimpleAggregate > DataManagement > remaining).

**Note on antd v6:** Ant Design v6.3.5 is now available (released 2026). The CONTEXT.md locks the decision to "Ant Design 5.x". antd v6 is mostly API-compatible with v5 (React 18 minimum, CSS variables by default, some deprecated v4 APIs removed). If the team wants to use v6 instead, it would work with the same theme tokens and component APIs. This research documents v5 per the locked decision, but upgrading to v6 later would be a minor effort.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** One-shot rewrite of all pages, no progressive migration
- **D-02:** Replace gradient backgrounds with Feishu-style pure light gray background
- **D-03:** Use Ant Design Layout + Sider + Menu to replace custom sidebar
- **D-04:** Sidebar supports collapse (icons only when collapsed), Feishu standard behavior
- **D-05:** Header bar with breadcrumb + user avatar/logout on the right
- **D-06:** Feishu blue color scheme -- primary #3370FF, background #F5F6F7, cards white
- **D-07:** Compact, dense information display -- small card margins, small table row height
- **D-08:** Page transitions: fade + slight translate on content area, no full-page reload feel
- **D-09:** Table and card loading uses Ant Skeleton, transitions to actual content
- **D-10:** Use @ant-design/icons official icon library
- **D-11:** Empty states use Ant Empty component
- **D-12:** Unified Ant Table (size='small' compact mode) with built-in sort/filter/pagination/loading
- **D-13:** Success/failure uses Ant message (top toast), important notifications use Ant notification (top-right card)
- **D-14:** Replace existing GlobalFeedback custom component
- **D-15:** Unified Ant Form + Form.Item + Input/Select/DatePicker with built-in validation
- **D-16:** Use Ant Upload.Dragger to replace custom drag-upload area
- **D-17:** Confirm/warning dialogs use Ant Modal, complex form editing (e.g., employee edit) uses Ant Drawer

### Claude's Discretion
- Ant Design ConfigProvider theme token specific value tuning
- Per-page Ant component selection details (Statistic, Descriptions, Tag, etc.)
- CSS-in-JS vs CSS Modules styling approach choice
- Responsive breakpoint specific settings

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | All pages use Ant Design 5.x components (no legacy custom components remain) | Standard Stack section (antd 5.29.3), Component Inventory in UI-SPEC, migration pattern for each custom component |
| UI-02 | Feishu-inspired visual theme (card-based layout, clean typography, professional color palette) | Theme token config in UI-SPEC, Architecture Patterns (MainLayout, page content pattern) |
| UI-03 | Page transitions and key interactions have smooth animations | Animation Contract in UI-SPEC, Code Examples (page transition CSS) |
| UI-04 | Background, spacing, and scrolling have intentional design details | Spacing scale, color palette, card shadow, padding values all defined in UI-SPEC |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| antd | 5.29.3 | UI component library | Locked decision (D-01 through D-17). Latest v5 stable. |
| @ant-design/icons | 5.6.1 | Icon library | Locked decision (D-10). Must match antd v5 major version. |

### Supporting (already installed, no changes)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react | ^18.3.1 | Core framework | Already installed |
| react-router-dom | ^6.30.0 | Routing | Already installed, no changes |
| axios | ^1.8.4 | HTTP client | Already installed, no changes |
| vite | ^6.2.1 | Build tool | Already installed, no changes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| antd 5.29.3 | antd 6.3.5 | v6 is latest but CONTEXT.md locks to v5.x. v6 migration is minor if desired later. |
| CSS Modules | styled-components / emotion | CSS Modules chosen (UI-SPEC decision) -- no runtime cost, antd handles 90%+ via tokens |

**Installation:**
```bash
cd frontend && npm install antd@5.29.3 @ant-design/icons@5.6.1
```

**Version verification:**
- antd: 5.29.3 (latest v5, verified via `npm view antd@5 version` on 2026-03-30)
- @ant-design/icons: 5.6.1 needs verification -- the v5-compatible icons package

**IMPORTANT:** `@ant-design/icons` v6.x is NOT compatible with antd v5. Must install v5.x of icons package.

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
  theme/
    index.ts              # ThemeConfig export (all Feishu tokens)
    animations.module.css # Page transition CSS classes
  layouts/
    MainLayout.tsx        # Layout + Sider + Header + Content
    MainLayout.module.css # Layout-specific overrides
  components/
    AuthProvider.tsx       # KEEP - no changes needed
    index.ts              # Updated exports (remove old, add new)
  pages/
    [all 17 pages]        # Rewritten to use Ant components
  hooks/                  # KEEP - no changes needed
  services/               # KEEP - no changes needed
  main.tsx                # Updated: wrap with Ant ConfigProvider + App
```

### Pattern 1: App Bootstrap with Ant Design
**What:** Wrap the entire app with Ant Design's ConfigProvider and App component for global theme + message/notification access.
**When to use:** main.tsx -- the single entry point
**Example:**
```typescript
// main.tsx
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { theme } from './theme';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider theme={theme} componentSize="small" locale={zhCN}>
      <AntApp>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>
);
```

### Pattern 2: MainLayout Shell (replaces AppShell)
**What:** Ant Design Layout with dark Sider, white Header, and gray Content area.
**When to use:** The single layout wrapper for all authenticated pages.
**Key points:**
- `Layout.Sider` with `theme="dark"`, `collapsible`, `width={220}`, `collapsedWidth={64}`
- `Menu` with `theme="dark"`, `items` array (not children -- v5 recommended pattern)
- Navigation items migrated from `AppShell.tsx` with role filtering preserved
- `Layout.Header` with `Breadcrumb` on left, user info + logout on right
- `Layout.Content` with page transition wrapper

### Pattern 3: Page Transition Animation
**What:** CSS-based fade+translate on route change.
**When to use:** Content area wrapping the routed page.
**Example:**
```typescript
// Inside MainLayout Content area
import { useLocation } from 'react-router-dom';

function AnimatedContent({ children }: PropsWithChildren) {
  const location = useLocation();
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(false);
    const timer = requestAnimationFrame(() => setShow(true));
    return () => cancelAnimationFrame(timer);
  }, [location.pathname]);

  return (
    <div className={show ? 'page-enter-active' : 'page-enter'}>
      {children}
    </div>
  );
}
```

### Pattern 4: Ant App.useApp() for Messages (replaces GlobalFeedback)
**What:** Use Ant Design's `App.useApp()` hook to get `message` and `notification` instances that respect ConfigProvider context.
**When to use:** Any component that needs to show success/error toasts.
**Key point:** The `App` component must wrap the app tree. Then any child can call `const { message, notification } = App.useApp()`.
**Migration note:** The existing `ApiFeedbackProvider` intercepts API errors globally. This can be replaced by using `App.useApp()` inside a similar provider that calls `message.error()` on API errors.

### Pattern 5: Ant Table Standardization
**What:** Replace all custom `<table>` elements with `<Table>` component.
**When to use:** Every page that shows tabular data (Dashboard, DataManagement, Employees, Imports, etc.).
**Key points:**
- `size="small"` is set globally via ConfigProvider `componentSize="small"`
- Define `columns` array with `dataIndex`, `title`, `sorter`, `filters` as needed
- Use `loading` prop with Skeleton (D-09)
- Use `pagination` prop for built-in pagination

### Anti-Patterns to Avoid
- **Mixing old CSS classes with Ant components:** Do NOT keep any `panel-card`, `dashboard-pill`, `preview-table`, `login-shell` classes. Every HTML element must come from Ant components.
- **Importing individual Ant component CSS:** antd v5 uses CSS-in-JS internally -- do NOT import `antd/dist/antd.css` or individual CSS files. Just import components directly.
- **Using `children` pattern for Menu/Breadcrumb:** antd v5 recommends `items` prop for Menu and Breadcrumb. Do NOT use `<Menu.Item>` or `<Breadcrumb.Item>` children syntax (deprecated in v5, removed in v6).
- **Creating wrapper components around Ant components:** Do NOT create `<MyTable>`, `<MyButton>` wrappers. Use Ant components directly with props.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data tables | Custom `<table>` with sorting/filtering | `Table` component | Built-in sort, filter, pagination, loading, empty state, row selection |
| Form validation | Manual `useState` + validation logic | `Form` + `Form.Item` with `rules` | Built-in validation, error display, layout, submit handling |
| Toasts/notifications | Custom feedback banners | `App.useApp().message` / `.notification` | Stacking, auto-dismiss, consistent styling, accessibility |
| Loading states | Custom skeleton/spinner | `Skeleton` / `Spin` | Automatic sizing, shimmer animation, content replacement |
| Empty states | Custom "no data" divs | `Empty` component | Consistent illustration, configurable description |
| Error results | Custom error divs | `Result` (status="error") | Standard layout with icon, title, subtitle, action buttons |
| Modals/confirms | Custom dialog components | `Modal` / `Modal.confirm` | Focus trap, escape handling, overlay, animation |
| Sidebar/drawer edit forms | In-page edit panels | `Drawer` | Slide animation, overlay, close handling |
| Upload drag-drop | Custom drag-and-drop zone | `Upload.Dragger` | File validation, progress, multiple file support |
| Breadcrumb navigation | Manual path splitting | `Breadcrumb` with `items` | Route-aware, separator handling |
| Statistics display | Custom `<strong>` with labels | `Statistic` component | Number formatting, prefix/suffix, loading state |

**Key insight:** The existing codebase has ~7000 lines of page code that manually builds UI patterns (tables, cards, forms, loading states, error states) that Ant Design provides out of the box. Post-migration, code volume should decrease significantly because Ant components encapsulate layout, styling, state management, and accessibility.

## Common Pitfalls

### Pitfall 1: antd CSS-in-JS Bundle Size
**What goes wrong:** First load is slow because antd v5 generates styles at runtime.
**Why it happens:** antd v5 uses `@ant-design/cssinjs` which generates CSS on first render.
**How to avoid:** This is acceptable for an internal business tool. If needed later, use `extractStyle` for SSR or consider v6's zero-runtime mode.
**Warning signs:** >500ms first contentful paint on slow networks.

### Pitfall 2: Menu `items` vs Children API
**What goes wrong:** Using deprecated `<Menu.Item>` children pattern that will break on v6 upgrade.
**Why it happens:** Many tutorials and examples still show the children pattern.
**How to avoid:** Always use `items` prop: `<Menu items={[{ key: '1', label: 'Nav', icon: <Icon /> }]} />`.
**Warning signs:** Console deprecation warnings.

### Pitfall 3: ConfigProvider Nesting
**What goes wrong:** Multiple ConfigProvider wrappers override each other's themes.
**Why it happens:** Developers wrap individual sections with different themes.
**How to avoid:** Single top-level ConfigProvider in main.tsx. Only nest for genuine local overrides (e.g., a dark-themed section).
**Warning signs:** Components showing wrong colors or sizes.

### Pitfall 4: Form.Item Name Conflicts
**What goes wrong:** Form field values not updating or submitting correctly.
**Why it happens:** `Form.Item` `name` prop must match the data model exactly; nested names use arrays.
**How to avoid:** Always define `name` prop matching the API field name. Test form submission with console.log before API call.
**Warning signs:** Form.getFieldsValue() returns undefined for some fields.

### Pitfall 5: Table Key Prop
**What goes wrong:** React warnings, wrong row selected, stale data after re-render.
**Why it happens:** Ant Table requires `rowKey` prop or each `dataSource` item to have a unique `key`.
**How to avoid:** Always set `rowKey` prop: `<Table rowKey="id" />` or `rowKey={(record) => record.batch_id}`.
**Warning signs:** Console "Each child should have a unique key" warnings.

### Pitfall 6: Removing styles.css Too Early
**What goes wrong:** Pages break visually during migration because old CSS is deleted before all pages are rewritten.
**Why it happens:** Temptation to "clean up" the old CSS file before all pages are migrated.
**How to avoid:** Since this is a one-shot rewrite (D-01), the old `styles.css` should be deleted only AFTER all pages are rewritten. Alternatively, delete it first and accept temporary visual breakage since all pages will be rewritten in this phase.
**Warning signs:** Unstyled pages during development.

### Pitfall 7: Losing Navigation Role Filtering Logic
**What goes wrong:** All users see all navigation items regardless of role.
**Why it happens:** The existing `AppShell.tsx` has role-based filtering logic (`roles` array, `adminOnly` flag) that must be preserved in the new Ant Menu `items` array.
**How to avoid:** Build the Menu items dynamically based on `user.role`, filtering the same way as the current implementation.
**Warning signs:** Employee role seeing admin pages in sidebar.

### Pitfall 8: Aggregate Session Feedback Banner Lost
**What goes wrong:** Users no longer see the aggregate progress/status banner after migration.
**Why it happens:** `GlobalFeedback.tsx` contains aggregate session state display that is NOT just error/success messages -- it also shows running aggregate progress.
**How to avoid:** The aggregate session banner must be preserved in the new layout. Use Ant `Alert` component or a custom banner inside the Content area. This is NOT replaced by `message`/`notification` -- it's persistent UI, not a toast.
**Warning signs:** No visible feedback when aggregate is running.

## Code Examples

### Theme Configuration (theme/index.ts)
```typescript
// Source: UI-SPEC.md theme tokens
import type { ThemeConfig } from 'antd';

export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#3370FF',
    colorBgContainer: '#FFFFFF',
    colorBgLayout: '#F5F6F7',
    colorBgElevated: '#FFFFFF',
    colorText: '#1F2329',
    colorTextSecondary: '#646A73',
    colorTextTertiary: '#8F959E',
    colorBorder: '#DEE0E3',
    colorBorderSecondary: '#E8E8E8',
    colorError: '#F54A45',
    colorWarning: '#FF7D00',
    colorSuccess: '#00B42A',
    colorInfo: '#3370FF',
    fontFamily: '"PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 14,
    fontSizeHeading1: 24,
    fontSizeHeading2: 20,
    fontSizeHeading3: 16,
    fontSizeSM: 12,
    fontWeightStrong: 600,
    lineHeight: 1.5714,
    borderRadius: 8,
    borderRadiusSM: 4,
    borderRadiusLG: 12,
    controlHeight: 32,
    controlHeightSM: 24,
    controlHeightLG: 40,
    padding: 16,
    paddingSM: 12,
    paddingXS: 8,
    margin: 16,
    marginSM: 12,
    marginXS: 8,
    motionDurationSlow: '0.3s',
    motionDurationMid: '0.2s',
    motionDurationFast: '0.1s',
    motionEaseInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)',
  },
  components: {
    Layout: {
      siderBg: '#1F2329',
      headerBg: '#FFFFFF',
      bodyBg: '#F5F6F7',
      headerHeight: 56,
      headerPadding: '0 24px',
    },
    Menu: {
      darkItemBg: '#1F2329',
      darkItemColor: 'rgba(255, 255, 255, 0.75)',
      darkItemHoverColor: '#FFFFFF',
      darkItemSelectedBg: 'rgba(51, 112, 255, 0.15)',
      darkItemSelectedColor: '#3370FF',
      itemHeight: 40,
      iconSize: 18,
      collapsedIconSize: 20,
    },
    Table: {
      headerBg: '#F5F6F7',
      headerColor: '#1F2329',
      rowHoverBg: '#F0F5FF',
      cellPaddingBlockSM: 8,
      cellPaddingInlineSM: 12,
    },
    Card: {
      paddingLG: 20,
      borderRadiusLG: 8,
    },
    Button: {
      primaryShadow: '0 2px 0 rgba(51, 112, 255, 0.1)',
      borderRadiusSM: 4,
    },
  },
};
```

### MainLayout Shell (layouts/MainLayout.tsx)
```typescript
import { Layout, Menu, Breadcrumb, Button, Avatar, Dropdown } from 'antd';
import {
  UploadOutlined,
  DashboardOutlined,
  SwapOutlined,
  ImportOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ExportOutlined,
  TeamOutlined,
  DatabaseOutlined,
  AuditOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = Layout;

// Build menu items with role filtering
function buildMenuItems(userRole: string): MenuProps['items'] {
  const allItems = [
    { key: '/aggregate', icon: <UploadOutlined />, label: '快速融合', roles: ['admin', 'hr'] },
    { key: '/dashboard', icon: <DashboardOutlined />, label: '处理看板', roles: ['admin', 'hr'] },
    // ... etc
  ];
  return allItems
    .filter(item => item.roles.includes(userRole))
    .map(({ key, icon, label }) => ({ key, icon, label }));
}
```

### Page Transition CSS (theme/animations.module.css)
```css
.pageEnter {
  opacity: 0;
  transform: translateY(8px);
}

.pageEnterActive {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 300ms ease-in-out, transform 300ms ease-in-out;
}
```

### Table Migration Example (before/after)
```typescript
// BEFORE (custom table in Dashboard.tsx)
<table className="preview-table">
  <thead>
    <tr>
      <th>Batch Name</th>
      <th>Records</th>
    </tr>
  </thead>
  <tbody>
    {items.map(b => (
      <tr key={b.batch_id}>
        <td>{b.batch_name}</td>
        <td>{b.record_count}</td>
      </tr>
    ))}
  </tbody>
</table>

// AFTER (Ant Table)
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const columns: ColumnsType<BatchQuality> = [
  { title: '批次名称', dataIndex: 'batch_name', key: 'batch_name' },
  { title: '记录数', dataIndex: 'record_count', key: 'record_count', sorter: (a, b) => a.record_count - b.record_count },
];

<Table columns={columns} dataSource={quality.batches} rowKey="batch_id" pagination={false} />
```

### Message/Notification Migration (replaces GlobalFeedback)
```typescript
// In any component:
import { App } from 'antd';

function MyComponent() {
  const { message, notification } = App.useApp();

  const handleSuccess = () => {
    message.success('文件上传成功，共解析 42 条记录');
  };

  const handleImportantNotice = () => {
    notification.warning({
      message: '导出注意',
      description: '部分记录的工号匹配状态为未匹配，导出结果可能不完整。',
    });
  };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| antd v4 (Less themes) | antd v5 (CSS-in-JS tokens) | 2022-11 | No Less dependency, runtime styling |
| antd v5 | antd v6 (CSS variables, zero-runtime) | 2026-01 | Better performance, same API |
| Menu.Item children | Menu items prop | antd v5 | Children pattern deprecated |
| Breadcrumb.Item children | Breadcrumb items prop | antd v5 | Children pattern deprecated |
| Individual CSS imports | CSS-in-JS auto-injection | antd v5 | No CSS file imports needed |

**Deprecated/outdated:**
- `antd/dist/antd.css` import -- NOT needed in v5, styles are injected via CSS-in-JS
- `<Menu.Item>`, `<Breadcrumb.Item>` children pattern -- use `items` prop instead
- `BackTop` component -- use `FloatButton.BackTop` instead
- `Button.Group` -- use `Space.Compact` instead

## Open Questions

1. **@ant-design/icons v5 exact latest version**
   - What we know: Icons v6.x is for antd v6. We need the v5-compatible version.
   - What's unclear: Exact latest v5.x.x version (npm may default to v6 latest).
   - Recommendation: Use `npm install @ant-design/icons@^5` to get latest v5 automatically.

2. **Aggregate session banner replacement strategy**
   - What we know: `GlobalFeedback.tsx` shows persistent banners for aggregate progress, not just toasts.
   - What's unclear: Whether to use Ant `Alert` inside Content area or a custom persistent notification.
   - Recommendation: Use Ant `Alert` with `banner` prop at the top of Content area for aggregate session status. This is persistent UI, NOT a toast.

3. **CSS Modules support in Vite**
   - What we know: Vite supports CSS Modules out of the box (files ending in `.module.css`).
   - What's unclear: No additional config needed.
   - Recommendation: Just use `.module.css` files -- Vite handles it automatically.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | npm install | Assumed available | - | - |
| npm | Package install | Assumed available | - | - |
| antd | UI-01 through UI-04 | Will install | 5.29.3 | - |
| @ant-design/icons | D-10 | Will install | 5.x | - |

No external tools, databases, or services required. This phase is purely frontend code changes.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual visual testing + `npm run build` + `npm run lint` |
| Config file | `frontend/eslint.config.js` (lint), `frontend/tsconfig.json` (type check) |
| Quick run command | `cd frontend && npm run build` |
| Full suite command | `cd frontend && npm run lint && npm run build` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | All pages use Ant Design components | build + lint | `cd frontend && npm run build` | Existing |
| UI-02 | Feishu theme applied consistently | manual visual | Manual browser inspection | N/A |
| UI-03 | Page transitions smooth | manual visual | Manual browser navigation | N/A |
| UI-04 | Background/spacing details | manual visual | Manual browser inspection | N/A |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run build` (type check + bundle)
- **Per wave merge:** `cd frontend && npm run lint && npm run build`
- **Phase gate:** Full lint + build green, visual inspection of all 17 pages

### Wave 0 Gaps
None -- existing lint and build infrastructure covers automated validation. Visual validation is inherently manual for a UI phase.

## Codebase Migration Inventory

### Files to DELETE
| File | Reason |
|------|--------|
| `frontend/src/styles.css` | Entire custom CSS file replaced by Ant Design theme |
| `frontend/src/components/GlobalFeedback.tsx` | Replaced by Ant message/notification + Alert for aggregate |
| `frontend/src/components/PageContainer.tsx` | Replaced by Ant Layout Content + Breadcrumb |
| `frontend/src/components/SectionState.tsx` | Replaced by Ant Skeleton / Empty / Result |
| `frontend/src/components/SurfaceNotice.tsx` | Replaced by Ant Alert |

### Files to MODIFY
| File | Change |
|------|--------|
| `frontend/src/main.tsx` | Add ConfigProvider, AntApp wrapper, remove styles.css import, remove ApiFeedbackProvider |
| `frontend/src/App.tsx` | Replace ProtectedLayout to use new MainLayout |
| `frontend/src/components/AppShell.tsx` | DELETE and replace with `layouts/MainLayout.tsx` |
| `frontend/src/components/ApiFeedbackProvider.tsx` | Rewrite to use App.useApp() for error feedback |
| `frontend/src/components/index.ts` | Update exports |
| All 17 pages in `frontend/src/pages/` | Rewrite to use Ant components |

### Files to CREATE
| File | Purpose |
|------|---------|
| `frontend/src/theme/index.ts` | ThemeConfig with all Feishu tokens |
| `frontend/src/theme/animations.module.css` | Page transition CSS classes |
| `frontend/src/layouts/MainLayout.tsx` | Ant Layout + Sider + Header + Content |
| `frontend/src/layouts/MainLayout.module.css` | Layout-specific style overrides (minimal) |

### Page Migration Effort Estimate
| Page | Lines | Complexity | Priority |
|------|-------|-----------|----------|
| Login | 245 | Medium (form, tabs, role cards) | High |
| Dashboard | 351 | High (stats, distribution, tables, links) | High |
| SimpleAggregate | 845 | High (upload, steps, progress) | High |
| DataManagement | 529 | Medium (filters, table, search) | High |
| Employees | 790 | High (table, modal, drawer, CRUD) | Medium |
| EmployeeSelfService | 572 | Medium (form, query, display) | Medium |
| Imports | 573 | Medium (table, status tags) | Medium |
| ImportBatchDetail | 408 | Medium (descriptions, table) | Medium |
| Compare | 1165 | High (dual tables, tabs, diff view) | Low |
| Results | 318 | Medium (table, tags) | Medium |
| Exports | 299 | Low (table, buttons) | Medium |
| Mappings | 276 | Medium (table, select, tags) | Medium |
| AuditLogs | 223 | Low (table, filters) | Low |
| EmployeeCreate | 178 | Low (form) | Medium |
| Workspace (x2) | 124 | Low (cards, stats) | Low |
| Portal | 96 | Low (display) | Medium |
| NotFound | 27 | Trivial | Low |

**Total: ~7019 lines to rewrite across 17 page files + 6 component files.**

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `frontend/package.json`, `frontend/src/` -- current dependencies, structure, components
- UI-SPEC.md -- all theme tokens, component inventory, layout contract, animation contract
- CONTEXT.md -- all locked decisions D-01 through D-17
- npm registry: `npm view antd@5 version` -- confirmed 5.29.3 as latest v5

### Secondary (MEDIUM confidence)
- [Ant Design v5 to v6 Migration Guide](https://ant.design/docs/react/migration-v6/) -- breaking changes research
- [Ant Design 6.0 GitHub Issue](https://github.com/ant-design/ant-design/issues/55804) -- v6 changes summary
- [Ant Design v6 Medium Article](https://leandroaps.medium.com/migrating-from-ant-design-v5-to-v6-a-practical-guide-for-frontend-teams-12aba4df425d) -- practical migration guide

### Tertiary (LOW confidence)
- @ant-design/icons v5 exact latest version needs confirmation at install time

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - antd v5 is mature, version verified, React 18 compatible
- Architecture: HIGH - Layout/Sider/Header/Content is the canonical Ant Design pattern, well-documented
- Pitfalls: HIGH - Based on direct codebase analysis and known Ant Design patterns
- Migration scope: HIGH - Every file inventoried with line counts and complexity assessment

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (antd v5 is stable, not fast-moving)
