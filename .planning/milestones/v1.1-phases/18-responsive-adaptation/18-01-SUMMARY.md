---
phase: 18-responsive-adaptation
plan: 01
title: "Phase 18 Plan 01: Responsive Primitives + Mobile Shell"
subsystem: ui
tags: [responsive, layout, drawer, mobile, react]
dependency_graph:
  requires: []
  provides: [responsive-breakpoint-hook, mobile-layout-shell, sticky-action-bar]
  affects: [main-layout, workflow-pages, responsive-pages]
tech_stack:
  added: []
  patterns: [matchmedia-breakpoints, drawer-navigation, shared-mobile-cta]
key_files:
  created:
    - frontend/src/hooks/useResponsiveViewport.ts
    - frontend/src/components/MobileStickyActionBar.tsx
  modified:
    - frontend/src/components/WorkflowSteps.tsx
    - frontend/src/hooks/index.ts
    - frontend/src/layouts/MainLayout.tsx
    - frontend/src/layouts/MainLayout.module.css
decisions:
  - "响应式断点统一收敛到 useResponsiveViewport，避免页面各自读取 window.innerWidth"
  - "手机端导航改为 Drawer，平板和紧凑桌面继续复用现有侧栏体系"
metrics:
  duration: "n/a"
  completed: "2026-04-09T11:33:47+08:00"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
requirements:
  - UX-03
---

# Phase 18 Plan 01: Responsive Primitives + Mobile Shell Summary

共享响应式断点、移动端固定主操作条和 Drawer 导航壳层已经落地，为后续页面适配提供统一基础设施。

## What Was Done

### Task 1: 建立共享响应式原语
- 新增 `useResponsiveViewport`，统一提供 `isMobile`、`isTablet`、`isCompactDesktop`、`isDesktopWide`
- 新增 `MobileStickyActionBar`，支持底部安全区 padding 和单主操作模式
- 调整 `WorkflowSteps`，小屏改为横向滚动且禁用 AntD 内置 responsive 压缩

### Task 2: 重构 MainLayout 移动壳层
- `MainLayout` 在 `<768px` 切换为 Drawer 导航，Header 改为移动紧凑模式
- 路由变化时自动关闭移动抽屉，避免导航后残留遮罩
- Content padding 按断点分层，移除固定视口高度约束

## Verification Results

- `cd frontend && ./node_modules/.bin/eslint src/hooks/useResponsiveViewport.ts src/components/MobileStickyActionBar.tsx src/components/WorkflowSteps.tsx src/layouts/MainLayout.tsx`
- 通过，退出码 0

## Deviations from Plan

None - plan executed exactly as written.

## Commits

Deferred. Phase 18 is waiting on human responsive UAT, so no completion commit was created in this run.

## Self-Check: PASSED

- Shared hook and sticky CTA component exist on disk
- MainLayout contains Drawer, hamburger trigger, and route-close behavior
- WorkflowSteps preserves step readability on small screens
