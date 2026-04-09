---
phase: 18
slug: responsive-adaptation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-09
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | ESLint + TypeScript/Vite build |
| **Config file** | `frontend/package.json`, `frontend/tsconfig.json` |
| **Quick run command** | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/layouts/MainLayout.tsx src/components/WorkflowSteps.tsx src/pages/EmployeeSelfService.tsx src/pages/DataManagement.tsx src/pages/Employees.tsx src/pages/AuditLogs.tsx src/pages/SimpleAggregate.tsx src/pages/Results.tsx src/pages/Exports.tsx src/pages/Imports.tsx src/pages/ImportBatchDetail.tsx src/pages/Dashboard.tsx src/pages/Compare.tsx src/pages/PeriodCompare.tsx src/pages/Mappings.tsx src/pages/FeishuSync.tsx src/pages/FeishuSettings.tsx` |
| **Full suite command** | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint && npm run build` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run the targeted lint command for the files touched by that task
- **After every plan wave:** Run `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint && npm run build`
- **Before `/gsd-verify-work`:** Full suite must be green + manual viewport verification completed
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | UX-03 | T-18-01 | Mobile nav still honors role-filtered menu items only | lint | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/layouts/MainLayout.tsx src/layouts/MainLayout.module.css` | ✅ | ⬜ pending |
| 18-01-02 | 01 | 1 | UX-03 | T-18-02 | Sticky CTA never duplicates a destructive secondary action in fixed bar | lint | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/components/WorkflowSteps.tsx src/components/MobileStickyActionBar.tsx` | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 2 | UX-03 | T-18-03 | Employee page continues to show masked identity data only | lint | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/pages/EmployeeSelfService.tsx` | ✅ | ⬜ pending |
| 18-03-01 | 03 | 2 | UX-03 | T-18-04 | Filter drawer uses draft state and does not auto-query on every change | lint | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/pages/DataManagement.tsx src/pages/Employees.tsx src/pages/AuditLogs.tsx src/components/ResponsiveFilterDrawer.tsx` | ❌ W0 | ⬜ pending |
| 18-03-02 | 03 | 2 | UX-03 | — | Wide tables keep left identity column + horizontal scroll | lint | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/pages/DataManagement.tsx src/pages/Employees.tsx src/pages/AuditLogs.tsx` | ✅ | ⬜ pending |
| 18-04-01 | 04 | 3 | UX-03 | T-18-05 | Mobile pages expose only one fixed primary action and preserve disabled guards | lint | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/pages/SimpleAggregate.tsx src/pages/Results.tsx src/pages/Exports.tsx src/components/MobileStickyActionBar.tsx` | ❌ W0 | ⬜ pending |
| 18-04-02 | 04 | 3 | UX-03 | — | Import pages remain navigable on mobile with preview tables still scrollable | lint | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run lint -- src/pages/Imports.tsx src/pages/ImportBatchDetail.tsx` | ✅ | ⬜ pending |
| 18-05-01 | 05 | 4 | UX-03 | — | Sweep pages keep responsive shell/table contracts without route regressions | build | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/components/MobileStickyActionBar.tsx` — shared mobile sticky CTA component for workflow pages
- [ ] `frontend/src/components/ResponsiveFilterDrawer.tsx` — shared draft/apply/clear filter drawer wrapper for filter-heavy pages

*Existing lint/build infrastructure covers all phase requirements once the shared components exist.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mobile drawer nav opens and closes on route change | UX-03 | Requires viewport + routing interaction | 1. Open app at `<768px` 2. Tap hamburger 3. Choose any menu item 4. Verify drawer closes after navigation |
| Mobile header hides breadcrumb and keeps page title visible | UX-03 | Visual layout behavior | 1. Resize to `375x812` 2. Open `Dashboard`, `Results`, `EmployeeSelfService` 3. Verify breadcrumb absent and title truncates cleanly |
| Employee self-service card flow and latest-month-first history | UX-03 | No frontend E2E framework | 1. Open `/employee/query` on phone width 2. Verify profile + current month cards appear before history 3. Verify latest month expanded and older months collapsed |
| Filter drawer draft/apply/clear semantics | UX-03 | Requires interaction state validation | 1. Open `DataManagement` or `Employees` below `992px` 2. Change filters in drawer 3. Close without applying and verify list unchanged 4. Reopen and apply 5. Verify query updates |
| Sticky primary CTA on mobile workflow pages | UX-03 | Visual + interaction behavior | 1. Open `SimpleAggregate`, `Results`, `Exports` below `768px` 2. Verify bottom bar exists with one primary button only 3. Confirm secondary actions remain inside page content |
| Desktop/tablet fallback does not regress | UX-03 | Responsive regressions need visual confirmation | 1. Resize to `1280px` and `1024px` 2. Verify desktop pages keep inline filters and no forced mobile sticky bar |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 25s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
