---
phase: 07-design-system-ui-foundation
plan: 01
subsystem: ui
tags: [antd, ant-design, react, feishu-theme, layout, css-modules]

requires:
  - phase: 05-employee-portal
    provides: auth system with role-based routing
  - phase: 06-data-management
    provides: existing page components using old AppShell
provides:
  - Ant Design 5.x installed (antd@5.29.3, @ant-design/icons@5.6.1)
  - Feishu-style ThemeConfig with all design tokens
  - MainLayout component (dark Sider + white Header + animated Content)
  - ConfigProvider wrapping with zhCN locale and compact mode
  - Page transition animation CSS module
affects: [07-02, 07-03, 08-page-rebuild]

tech-stack:
  added: [antd@5.29.3, @ant-design/icons@5.6.1]
  patterns: [ConfigProvider theme wrapping, CSS Modules for layout, App.useApp() for toast messages]

key-files:
  created:
    - frontend/src/theme/index.ts
    - frontend/src/theme/animations.module.css
    - frontend/src/layouts/MainLayout.tsx
    - frontend/src/layouts/MainLayout.module.css
  modified:
    - frontend/package.json
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - frontend/src/components/ApiFeedbackProvider.tsx
    - frontend/src/components/index.ts

key-decisions:
  - "Kept PageContainer/SectionState/SurfaceNotice barrel exports since pages still import them"
  - "ApiFeedbackProvider uses App.useApp() message for error toast integration"
  - "MainLayout includes AggregateBanner migrated from GlobalFeedback"

patterns-established:
  - "Theme tokens in theme/index.ts, all Ant components inherit via ConfigProvider"
  - "Layout components in layouts/ directory separate from page components"
  - "CSS Modules for layout-specific styles, Ant tokens for component theming"

requirements-completed: [UI-01, UI-02, UI-03, UI-04]

duration: 7min
completed: 2026-03-30
---

# Phase 7 Plan 1: Ant Design Foundation & Feishu Layout Summary

**Ant Design 5 with Feishu-style theme, dark sidebar MainLayout, ConfigProvider with zhCN compact mode, and page transition animations**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-30T11:53:23Z
- **Completed:** 2026-03-30T12:00:08Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Installed antd@5.29.3 and @ant-design/icons@5.6.1 as production dependencies
- Created complete Feishu-style ThemeConfig with color, typography, spacing, and component tokens
- Built MainLayout with collapsible dark sidebar (220px/64px), white header with breadcrumb and user dropdown, role-filtered menu, page transition animations, and aggregate session banner
- Wrapped app in ConfigProvider with compact mode and zhCN locale; integrated App.useApp() for toast messages

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies + create Feishu theme + animations** - `1857b88` (feat)
2. **Task 2: Create MainLayout + update main.tsx/App.tsx + rewrite ApiFeedbackProvider** - `e8ebc90` (feat)

## Files Created/Modified
- `frontend/src/theme/index.ts` - Feishu-style ThemeConfig with all design tokens
- `frontend/src/theme/animations.module.css` - Page transition CSS classes (pageEnter, pageEnterActive)
- `frontend/src/layouts/MainLayout.tsx` - Main layout with Sider, Header, animated Content, aggregate banner
- `frontend/src/layouts/MainLayout.module.css` - Logo styling for collapsed/expanded states
- `frontend/package.json` - Added antd and @ant-design/icons dependencies
- `frontend/src/main.tsx` - ConfigProvider + AntApp wrapping with zhCN locale
- `frontend/src/App.tsx` - Replaced AppShell with MainLayout, Spin for auth states
- `frontend/src/components/ApiFeedbackProvider.tsx` - Added App.useApp() message integration
- `frontend/src/components/index.ts` - Removed AppShell/GlobalFeedback exports, kept PageContainer/SectionState/SurfaceNotice

## Decisions Made
- Kept PageContainer, SectionState, SurfaceNotice re-exports in components/index.ts because all existing pages still import them from the barrel; removing would break compilation. These will be cleaned up when pages are migrated in Phase 8.
- Used useRef to track lastError identity in ApiFeedbackProvider to avoid duplicate message.error() calls on re-renders.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Preserved PageContainer/SectionState/SurfaceNotice barrel exports**
- **Found during:** Task 2 (components/index.ts update)
- **Issue:** Plan instructed removing these exports, but 12 page files import them from '../components' barrel
- **Fix:** Kept PageContainer, SectionState, SurfaceNotice exports; only removed AppShell and GlobalFeedback
- **Files modified:** frontend/src/components/index.ts
- **Verification:** TypeScript compilation passes, all pages compile correctly
- **Committed in:** e8ebc90 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to prevent build breakage. No scope creep; old components preserved as plan intended.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Theme foundation ready for all subsequent page migrations
- MainLayout active for all protected routes
- Pages still use old PageContainer/SectionState/SurfaceNotice components; Phase 8 will migrate them to Ant equivalents

---
*Phase: 07-design-system-ui-foundation*
*Completed: 2026-03-30*
