# Phase 8: Page Rebuild & UX Flow - Research

**Researched:** 2026-03-31
**Domain:** React / Ant Design 5 front-end -- responsive layout, i18n, role navigation, workflow UX
**Confidence:** HIGH

## Summary

Phase 8 builds on the Ant Design 5 foundation established in Phase 7. The four requirements (UI-05 through UI-08) are primarily front-end-only changes to existing pages and layouts. The existing codebase already has strong foundations: role-aware menu filtering in `buildMenuItems`, `ConfigProvider locale={zhCN}` already applied in `main.tsx`, and a working `RoleRoute` guard system. The remaining work is incremental: adding responsive breakpoint logic to the sidebar, creating a shared WorkflowSteps component, adding scroll/fixed-column configurations to tables, building an error code-to-Chinese message mapping, and verifying completeness of all these behaviors.

The risk level is low. No new libraries are needed. All required Ant Design features (Steps, Sider breakpoint/collapsed, Table scroll/fixed, ConfigProvider locale) are well-documented first-party capabilities of antd 5.x already installed at ^5.29.3.

**Primary recommendation:** Split into 4 focused plans: (1) responsive layout + sidebar auto-collapse, (2) WorkflowSteps shared component + integration into 4 pages, (3) error message Chinese mapping + API interceptor enhancement, (4) verification sweep for untranslated strings and role navigation correctness.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 保持现有方式——同一个 MainLayout 侧边栏，根据角色过滤菜单项（buildMenuItems 逻辑）。不做分角色布局
- **D-02:** 员工角色登录后直接跳转到 /employee/query 查询页，不需要工作台首页
- **D-03:** 用户访问无权限页面时静默跳转回该角色的默认页面（当前 RoleRoute 已有此行为，保持不变）
- **D-04:** 屏幕宽度 <=1440px 时侧边栏自动折叠为图标模式（64px），利用现有 Sider collapsible 功能加断点触发
- **D-05:** 表格列溢出时使用 Ant Table scroll={{ x: true }} 水平滚动，固定左侧关键列（姓名/工号）
- **D-06:** 使用 Ant Design ConfigProvider locale={zhCN} 解决组件内置文案（分页、日期选择器等），业务文案继续硬编码中文。不引入 i18n 框架
- **D-07:** 在前端 API 客户端层统一拦截错误，根据 HTTP 状态码和后端 error code 映射为中文错误提示。后端继续返回英文 error code
- **D-08:** 在"快速融合""处理看板""校验匹配""导出结果"四个页面顶部显示统一的 Ant Steps 组件（上传 -> 解析 -> 校验 -> 导出），高亮当前所在步骤，点击可跳转
- **D-09:** Steps 组件利用 status 属性反馈步骤状态：完成=绿色对号，进行中=蓝色旋转，有警告=橙色感叹号，失败=红色叉号

### Claude's Discretion
- 具体断点数值的微调（1440px 是否需要微调）
- Steps 组件的具体样式调整（水平/垂直、size 大小）
- 错误码映射表的具体条目设计
- 各页面 Table 固定列的具体选择

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-05 | 角色感知路由（不同角色看到不同导航菜单） | Already 90% implemented via `buildMenuItems` in MainLayout.tsx and `RoleRoute` in App.tsx. Need verification pass and minor tweaks. |
| UI-06 | 响应式布局适配主流分辨率 | Ant Sider collapsible already in place; need `window.matchMedia` breakpoint at 1440px + table scroll/fixed-column audit across all pages |
| UI-07 | 中文本地化完整 | `ConfigProvider locale={zhCN}` already configured in main.tsx; need error message mapping file + API interceptor enhancement + string sweep |
| UI-08 | 上传/解析/导出流程操作逻辑顺畅 | Need new WorkflowSteps shared component integrated into 4 workflow pages, reading state from useAggregateSession |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Frontend: React + Ant Design 5 (established)
- Backend: FastAPI (no backend changes needed this phase)
- All business text must be in Chinese
- No i18n framework
- Must not break existing dual-template export flow
- Rules-first approach (no LLM involved in this phase)
- Test with `npm run lint` and `npm run build`

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| antd | ^5.29.3 (latest: 5.6.3+) | UI component library | Already installed, Phase 7 foundation |
| @ant-design/icons | ^5.6.1 | Icon set | Already installed |
| react | ^18.3.1 | UI framework | Already installed |
| react-router-dom | ^6.30.0 | Client routing | Already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| antd/locale/zh_CN | (bundled with antd) | Chinese locale for Ant components | Already imported in main.tsx |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom matchMedia hook | Ant Sider `breakpoint` prop | Sider breakpoint only supports standard breakpoints (xs/sm/md/lg/xl/xxl); xl=1200px is too small vs D-04's 1440px. Custom matchMedia is required. |
| react-intl / i18next | Hardcoded Chinese | D-06 explicitly forbids i18n framework. Hardcoded is correct. |

**Installation:**
```bash
# No new packages needed -- all dependencies already installed
```

## Architecture Patterns

### Recommended Project Structure (changes only)
```
frontend/src/
  components/
    WorkflowSteps.tsx          # NEW: shared Steps navigation bar
  constants/
    errorMessages.ts           # NEW: HTTP status/error code -> Chinese message map
  layouts/
    MainLayout.tsx             # MODIFY: add responsive breakpoint hook
  services/
    api.ts                     # MODIFY: enhance error interceptor with Chinese mapping
  pages/
    SimpleAggregate.tsx        # MODIFY: add WorkflowSteps
    Dashboard.tsx              # MODIFY: add WorkflowSteps
    Results.tsx                # MODIFY: add WorkflowSteps
    Exports.tsx                # MODIFY: add WorkflowSteps
```

### Pattern 1: Responsive Sidebar with matchMedia Hook
**What:** Custom hook using `window.matchMedia('(max-width: 1440px)')` to auto-collapse the Sider
**When to use:** D-04 requires 1440px breakpoint which does not align with Ant's built-in breakpoints
**Example:**
```typescript
// In MainLayout.tsx
function useResponsiveCollapse(breakpoint: number = 1440): boolean {
  const [shouldCollapse, setShouldCollapse] = useState(
    () => window.innerWidth <= breakpoint
  );

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const handler = (e: MediaQueryListEvent) => setShouldCollapse(e.matches);
    mql.addEventListener('change', handler);
    setShouldCollapse(mql.matches);
    return () => mql.removeEventListener('change', handler);
  }, [breakpoint]);

  return shouldCollapse;
}

// Usage in MainLayout:
const autoCollapsed = useResponsiveCollapse(1440);
// Merge with manual collapse state -- auto sets default, user can override
```

**Confidence:** HIGH -- matchMedia is standard Web API, well-supported.

### Pattern 2: Shared WorkflowSteps Component
**What:** A single Steps component consumed by 4 workflow pages
**When to use:** D-08/D-09 require consistent step navigation across pages
**Example:**
```typescript
// WorkflowSteps.tsx
import { Steps } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';

const WORKFLOW_STEPS = [
  { title: '上传文件', path: '/aggregate', icon: <UploadOutlined /> },
  { title: '解析处理', path: '/dashboard', icon: <DashboardOutlined /> },
  { title: '校验匹配', path: '/results', icon: <CheckCircleOutlined /> },
  { title: '导出结果', path: '/exports', icon: <ExportOutlined /> },
];

// Determine current step from location.pathname
// Determine step status from useAggregateSession state
```

**Confidence:** HIGH -- Ant Steps `onChange` + `current` + `status` is standard usage.

### Pattern 3: Error Message Mapping Interceptor
**What:** Central error code -> Chinese message map, consumed by API response interceptor
**When to use:** D-07 requires Chinese error messages from English backend error codes
**Example:**
```typescript
// constants/errorMessages.ts
export const ERROR_MESSAGES: Record<string, string> = {
  validation_error: '请求参数有误，请检查输入内容',
  token_expired: '登录已过期，请重新登录',
  invalid_credentials: '用户名或密码错误',
  forbidden: '您没有权限执行此操作',
  // ... etc per UI-SPEC table
};

export const HTTP_STATUS_MESSAGES: Record<number, string> = {
  400: '请求参数有误，请检查输入内容',
  403: '您没有权限执行此操作',
  404: '请求的资源不存在',
  500: '服务器内部错误，请稍后重试',
  // ... etc
};

export function getChineseErrorMessage(statusCode?: number, errorCode?: string): string {
  if (errorCode && ERROR_MESSAGES[errorCode]) return ERROR_MESSAGES[errorCode];
  if (statusCode && HTTP_STATUS_MESSAGES[statusCode]) return HTTP_STATUS_MESSAGES[statusCode];
  return `操作失败，请稍后重试${errorCode ? `（错误码：${errorCode}）` : ''}`;
}
```

**Confidence:** HIGH -- straightforward key-value mapping.

### Anti-Patterns to Avoid
- **Sider breakpoint="xl" for 1440px:** Ant's xl breakpoint is 1200px, not 1440px. Must use custom matchMedia.
- **Adding locale={zhCN} to App.tsx:** Already configured in main.tsx. Adding it again would be redundant.
- **Separate Steps state store:** Do not create a new global store for workflow step status. Read from existing `useAggregateSession` hook + route-based detection.
- **Hardcoding step index by page:** Use `location.pathname` to derive current step dynamically, not a prop passed from each page.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Responsive breakpoint detection | Custom resize event listener with debounce | `window.matchMedia` API | matchMedia is more performant (event-driven, no polling) and handles edge cases |
| Step navigation progress bar | Custom div-based progress indicator | Ant `Steps` component | Steps has built-in status colors, click handling, accessibility |
| Chinese locale for Ant internals | Manual translation of pagination/datepicker strings | `antd/locale/zh_CN` | Already complete, maintained by Ant team |
| Error toast display | Custom toast system | Ant `App.useApp().message` | Already integrated via ApiFeedbackProvider |

## Common Pitfalls

### Pitfall 1: Sider Collapse State Conflict
**What goes wrong:** Auto-collapse from breakpoint fights with user's manual collapse toggle, causing flickering or stuck state.
**Why it happens:** Two sources of truth for `collapsed` -- the matchMedia breakpoint and the user's click on the collapse trigger.
**How to avoid:** Use auto-collapse only to set the *default* collapsed state. Once the user manually toggles, let manual state take precedence until the next breakpoint crossing resets it.
**Warning signs:** Sidebar flickers between expanded/collapsed states during window resize.

### Pitfall 2: Steps Status Derivation Complexity
**What goes wrong:** Step status logic becomes overly complex trying to track every possible aggregate session state.
**Why it happens:** The aggregate session has many intermediate states (uploading, parsing, validating, matching, exporting, failed, etc).
**How to avoid:** Map session stages to step indices simply. If the session's `stage` is past a step's stage, that step is `finish`. If it matches, it's `process`. If session has error at that stage, it's `error`. If not reached, it's `wait`.
**Warning signs:** Steps showing incorrect status when session is in intermediate states.

### Pitfall 3: Table Fixed Columns Without Width
**What goes wrong:** Fixed columns without explicit `width` cause layout thrashing or columns overlapping.
**Why it happens:** Ant Table requires fixed columns to have a set width for proper offset calculation.
**How to avoid:** Always set `width` on columns that have `fixed: 'left'` or `fixed: 'right'`.
**Warning signs:** Horizontal scroll causes columns to overlap or disappear.

### Pitfall 4: Error Interceptor Double-Displaying Errors
**What goes wrong:** Both the API interceptor (via `onError` callback in ApiFeedbackProvider) and individual page catch blocks display the same error.
**Why it happens:** The interceptor already calls `message.error()` via ApiFeedbackProvider, then the page's catch block also shows an error.
**How to avoid:** The interceptor should set the error on the feedback context (which it already does). Pages should not redundantly call `message.error()` for API errors that are already intercepted. Review pages that currently have explicit error message calls.
**Warning signs:** Same error toast appears twice.

### Pitfall 5: Ant Sider breakpoint Prop Misleading
**What goes wrong:** Using Sider's built-in `breakpoint` prop expecting 1440px behavior.
**Why it happens:** Sider `breakpoint` only supports standard Ant breakpoints: xs(480), sm(576), md(768), lg(992), xl(1200), xxl(1600). None maps to 1440px.
**How to avoid:** Use custom `matchMedia` hook as described in Pattern 1.
**Warning signs:** Sidebar collapses at wrong resolution.

## Code Examples

### Ant Steps with Status and Click Navigation
```typescript
// Source: Ant Design 5 Steps component API
import { Steps } from 'antd';

<Steps
  size="small"
  current={currentStepIndex}
  onChange={(stepIndex) => navigate(WORKFLOW_STEPS[stepIndex].path)}
  items={WORKFLOW_STEPS.map((step, index) => ({
    title: step.title,
    icon: step.icon,
    status: getStepStatus(index, sessionState),
  }))}
/>
```

### Ant Table with Fixed Columns and Scroll
```typescript
// Source: Ant Design 5 Table scroll API
<Table
  columns={columns}
  dataSource={data}
  scroll={{ x: true }}
  // First column example with fixed left:
  // { title: '姓名', dataIndex: 'name', fixed: 'left', width: 120 }
/>
```

### matchMedia Responsive Hook
```typescript
// Standard Web API pattern
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(
    () => window.matchMedia(query).matches
  );

  useEffect(() => {
    const mql = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [query]);

  return matches;
}
```

## Existing Code Analysis

### Already Complete (no work needed)
| Feature | Evidence | Status |
|---------|----------|--------|
| `ConfigProvider locale={zhCN}` | `main.tsx` line 13 | Already configured |
| Role-based menu filtering | `MainLayout.tsx` buildMenuItems with roles array | Already working |
| RoleRoute guard | `App.tsx` lines 84-96 | Already working |
| Employee redirect to /employee/query | `App.tsx` DEFAULT_WORKSPACE_BY_ROLE | Already configured |
| Unauthorized redirect to default page | `App.tsx` RoleRoute component | Already working |

### Needs Implementation
| Feature | Current State | Work Needed |
|---------|---------------|-------------|
| Responsive sidebar auto-collapse | Manual collapse only | Add matchMedia hook at 1440px |
| WorkflowSteps component | Does not exist | Create new shared component |
| Error message Chinese mapping | Backend errors shown raw or with ad-hoc Chinese | Create errorMessages.ts + enhance interceptor |
| Table scroll/fixed columns | Partial -- some pages have scroll, most lack fixed columns | Audit all tables, add scroll + fixed columns |
| String completeness | Business text is Chinese, but some edge cases may be English | Sweep for untranslated strings |

### Tables Requiring Scroll/Fixed Column Audit
| Page | Table Count | Current Scroll | Needs Fix |
|------|-------------|----------------|-----------|
| SimpleAggregate.tsx | 1 | None | Add scroll + fixed |
| Dashboard.tsx | 3 | None | Add scroll + fixed |
| Results.tsx | 2 | None | Add scroll + fixed |
| Exports.tsx | 1 | None | Add scroll + fixed |
| DataManagement.tsx | 3 | Has scroll={{ x: 1000/800 }} | Verify fixed columns |
| Employees.tsx | 1 | Has scroll={{ x: 900 }} | Verify fixed columns |
| Imports.tsx | 2 | Has scroll={{ x: 700/true }} | Verify fixed columns |
| ImportBatchDetail.tsx | 1 | Has scroll + fixed | Already done |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| antd locale via LocaleProvider | ConfigProvider locale prop | antd 4.x+ | Already using correct approach |
| Sider responsive via window.onresize | matchMedia API | Evergreen | More performant, no debounce needed |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None installed (no vitest/jest in frontend) |
| Config file | None |
| Quick run command | `cd frontend && npm run lint && npm run build` |
| Full suite command | `cd frontend && npm run lint && npm run build` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-05 | Role menus differ per role | manual | Visual verification at 3 roles | N/A |
| UI-06 | Pages render at 1920x1080, 1440x900, 1366x768 | manual | Browser DevTools responsive mode | N/A |
| UI-07 | All text Chinese, no untranslated strings | lint+build | `npm run build` (catches import errors) | N/A |
| UI-08 | Steps workflow navigates correctly | manual | Click through all 4 steps | N/A |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run lint && npm run build`
- **Per wave merge:** Same + manual visual check at 3 resolutions
- **Phase gate:** Full build + manual walk-through of all 4 workflow pages at each resolution

### Wave 0 Gaps
None -- no test framework for frontend. Validation is lint+build+manual. Installing a test framework is out of scope for this phase.

## Open Questions

1. **Double error display risk**
   - What we know: ApiFeedbackProvider already displays errors via `message.error(lastError.message)`. Many pages also have their own `message.error()` calls in catch blocks.
   - What's unclear: Whether enhancing the interceptor will cause duplicate toasts.
   - Recommendation: When enhancing the interceptor, ensure pages that already show errors via ApiFeedbackProvider do not also manually call `message.error()` for the same error. May need to audit and remove redundant page-level error displays.

2. **Steps state when no aggregate session exists**
   - What we know: useAggregateSession returns idle state when no session is active.
   - What's unclear: What the Steps should show when a user navigates to /dashboard or /results without having started an aggregate session (e.g., viewing old batch data).
   - Recommendation: When session is idle, show all steps as `wait` with the current page highlighted as `process`. The Steps serve as navigation even without an active session.

## Sources

### Primary (HIGH confidence)
- `frontend/src/main.tsx` -- confirmed locale={zhCN} already configured
- `frontend/src/layouts/MainLayout.tsx` -- confirmed buildMenuItems role filtering
- `frontend/src/App.tsx` -- confirmed RoleRoute, DEFAULT_WORKSPACE_BY_ROLE
- `frontend/src/services/api.ts` -- confirmed existing interceptor structure
- `08-UI-SPEC.md` -- detailed component contracts and interaction specifications
- `08-CONTEXT.md` -- locked implementation decisions D-01 through D-09

### Secondary (MEDIUM confidence)
- Ant Design 5 Steps API -- based on training data for antd 5.x, consistent with installed version
- matchMedia Web API -- standard, well-documented

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, all already installed and verified
- Architecture: HIGH -- patterns are straightforward Ant Design usage with standard React hooks
- Pitfalls: HIGH -- derived from direct codebase analysis of existing patterns

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable -- no fast-moving dependencies)
