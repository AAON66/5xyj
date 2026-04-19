---
phase: 23-login-redesign
plan: 01
subsystem: ui
tags: [login, three.js, webgl, fallback, css-gradient, playwright, e2e-scaffold, react-hook]

requires: []
provides:
  - "three@0.184.0 精确版本依赖（无 ^ 前缀）"
  - "@types/three@0.184.0 精确版本 devDependency"
  - "useWebGLSupport hook，返回 'loading' | 'webgl' | 'fallback'"
  - "CssGradientBackground 组件（双色谱 + 20s 浮动 + reduced-motion 降级）"
  - "login-redesign.spec.ts Wave 0 E2E 脚手架（5 个测试 / 4 个 testid / 3 次 addInitScript）"
affects:
  - 23-02-particle-wave
  - 23-03-login-integration

tech-stack:
  added:
    - "three@0.184.0 (dependency)"
    - "@types/three@0.184.0 (devDependency)"
  patterns:
    - "WebGL probe + 立即 loseContext 释放（iOS Safari slot 预算保护）"
    - "CSS 渐变降级使用内联 <style> 注入 keyframes（无 CSS-in-JS 库）"
    - "Playwright addInitScript 在页面脚本前 stub getContext / seed localStorage"

key-files:
  created:
    - "frontend/src/hooks/useWebGLSupport.ts"
    - "frontend/src/components/CssGradientBackground.tsx"
    - "frontend/tests/e2e/login-redesign.spec.ts"
  modified:
    - "frontend/package.json"
    - "frontend/package-lock.json"

key-decisions:
  - "three 使用 --save-exact 锁定精确版本 0.184.0（供应链 T-23-02 mitigation）"
  - "useWebGLSupport 初始 state 为 'loading' 而非 'fallback'，避免 SSR/首屏 flash"
  - "CssGradientBackground 使用 `<style>` JSX 形式注入 keyframes，禁用 dangerouslySetInnerHTML（T-23-03 mitigation）"
  - "E2E 测试 dark-mode 使用 localStorage key 'theme-mode'（与 ThemeModeProvider.tsx:14 STORAGE_KEY 一致）"
  - "beforeEach 清 'social-security-auth-session' 以绕过 Login.tsx:118-120 早返回陷阱"

patterns-established:
  - "精确版本 pin 新依赖：`npm install --save-exact pkg@x.y.z`"
  - "WebGL 检测 hook 在 effect 内探测 + 立即释放 probe context"
  - "视觉 fallback 组件暴露 data-testid 供 Playwright 断言（而非 CSS 选择器）"

requirements-completed:
  - LOGIN-03

duration: 8min
completed: 2026-04-19
---

# Phase 23 Plan 01: Login-Redesign Foundation Summary

**Three.js 精确版本 pin + useWebGLSupport 能力检测 hook + CssGradientBackground 降级组件 + Wave 0 E2E 红灯脚手架，为 Plan 02/03 建立视觉/测试/降级契约。**

## Performance

- **Duration:** 约 8 分钟
- **Started:** 2026-04-19T06:27:56Z
- **Completed:** 2026-04-19T06:35:31Z
- **Tasks:** 3 / 3
- **Files created:** 3
- **Files modified:** 2

## Accomplishments

- `three@0.184.0` 与 `@types/three@0.184.0` 均以精确版本（无 `^` 前缀）装入 `package.json`，`package-lock.json` 记录 integrity hash，`npm audit --audit-level=high` 退出码 0
- `useWebGLSupport` hook 返回 `'loading' | 'webgl' | 'fallback'` 三态；mount 时依序探测 `webgl2` → `webgl` → `experimental-webgl`，成功后立即 `WEBGL_lose_context.loseContext()` 释放 probe context，避免与 Plan 02 ParticleWave 叠加 iOS Safari WebGL slot
- `CssGradientBackground` 组件双色谱（亮 `#E8F0FF / #3370FF / #1D4AC7`、暗 `#1B2B4D / #3370FF / #7FA7FF`）+ `cssGradientDrift 20s ease-in-out infinite` + `prefers-reduced-motion: reduce` 降级；`aria-hidden="true"` 纯装饰
- Wave 0 E2E 脚手架 `login-redesign.spec.ts`：5 个 test、4 个 testid（`brand-panel` / `particle-wave-canvas` / `css-gradient-background` / `login-form-card`）、3 次 `addInitScript`；theme localStorage key = `'theme-mode'`，auth 清理 key = `'social-security-auth-session'`

## Task Commits

Each task was committed atomically with `--no-verify` (parallel executor):

1. **Task 1: 安装 three 依赖 + 创建 useWebGLSupport hook** — `533791e` (feat)
2. **Task 2: 创建 CssGradientBackground 组件** — `3442d06` (feat)
3. **Task 3: Wave 0 E2E 脚手架** — `c7d1f53` (test)

## Files Created/Modified

### Created
- `frontend/src/hooks/useWebGLSupport.ts` — WebGL 能力检测 hook，返回三态；SSR 安全（`typeof window === 'undefined'` → `'fallback'`）；probe 后立即释放 context
- `frontend/src/components/CssGradientBackground.tsx` — WebGL 降级 CSS 渐变背景，双色谱 + 20s 动画 + reduced-motion 降级；named export，无 default
- `frontend/tests/e2e/login-redesign.spec.ts` — 5 个 Playwright test，覆盖 LOGIN-01..04 Wave 0 验收断言

### Modified
- `frontend/package.json` — 新增 `"three": "0.184.0"` (deps) 与 `"@types/three": "0.184.0"` (devDeps)，均为精确版本
- `frontend/package-lock.json` — 同步 three + 其传递依赖的 integrity hash

## Dependency Integrity (package-lock.json)

```
three@0.184.0
  integrity=sha512-wtTRjG92pM5eUg/KuUnHsqSAlPM296brTOcLgMRqEeylYTh/CdtvKUvCyyCQTzFuStieWxvZb8mVTMvdPyUpxg==
@types/three@0.184.0
  integrity=sha512-4mY2tZAu0y0B0567w7013BBXSpsP0+Z48NJvmNo4Y/Pf76yCyz6Jw4P3tUVs10WuYNXXZ+wmHyGWpCek3amJxA==
```

## Exported Signatures (供 Plan 02/03 直接消费)

```typescript
// frontend/src/hooks/useWebGLSupport.ts
export type WebGLSupport = 'loading' | 'webgl' | 'fallback';
export function useWebGLSupport(): WebGLSupport;

// frontend/src/components/CssGradientBackground.tsx
export interface CssGradientBackgroundProps { isDark: boolean; }
export function CssGradientBackground(props: CssGradientBackgroundProps): JSX.Element;
```

## npm audit Summary

```
cd frontend && npm audit --audit-level=high --omit=dev
→ EXIT 0
→ 2 moderate vulnerabilities (axios 1.0.0-1.14.0 NO_PROXY / follow-redirects <=1.15.11)
→ 0 high, 0 critical
```

axios 与 follow-redirects 的 moderate 漏洞均为 **pre-existing**（本 Plan 未引入，三个新依赖均无自身漏洞），不阻塞 high-gate。可在后续 Phase 的维护窗口跑 `npm audit fix`。

## E2E Test Status

```
cd frontend && npm run test:e2e -- tests/e2e/login-redesign.spec.ts
→ 预期 5/5 RED（Wave 0 脚手架 TDD 预期）
```

5 个测试当前均会失败，原因符合预期：
- `layout — desktop split` / `layout — mobile form-only`: Plan 03 尚未加 `data-testid="brand-panel"`
- `particle — canvas renders`: Plan 02 尚未实现 `ParticleWave` 组件 / `data-testid="particle-wave-canvas"`
- `webgl fallback — ...`: Plan 03 尚未把 `CssGradientBackground` 接入 Login.tsx
- `dark mode — ...`: Plan 03 尚未为表单卡片加 `data-testid="login-form-card"` 与 `backdrop-filter`；Plan 02 尚未暴露 `data-particle-color`

Plan 03 Task 2 全部 5 条 assertion 应于其结束后转绿。

## Decisions Made

- **精确版本 pin（非 `^` 前缀）**：Three.js 作为新依赖按 RESEARCH A1 建议 pin 到确切版本，避免在尚未有 R3F 封装/错误边界前出现 minor 漂移
- **初始 state = `'loading'`**：避免 SSR 与 client 首屏渲染不一致；两行之内就会 settle 到最终态
- **`<style>` JSX 注入 keyframes**：项目无 CSS-in-JS 库；CSS module 会引入额外配置；全局 CSS 污染；`<style>` 是最小改动且自包含
- **localStorage key 严格对齐 `ThemeModeProvider.tsx:14`**：避免社区常见陷阱（写 `'social-security-theme-mode'` 但实际 STORAGE_KEY 是 `'theme-mode'`），测试直写现场已核实的字面量

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] JSDoc 注释字面量触发 CssGradientBackground verify 的 negation grep**
- **Found during:** Task 2（verify 阶段）
- **Issue:** 首版注释里写了 "does NOT use `dangerouslySetInnerHTML`"（本意是声明不使用），但 Plan automated grep 的断言是 `! grep -q 'dangerouslySetInnerHTML' ...`，该字面量不论出现在代码还是注释中都会让 grep 命中、使 verify 退出 1
- **Fix:** 把注释改为 "no raw HTML injection API is used (see security audit T-23-03)"，保持含义一致但避开 grep 触发词
- **Files modified:** `frontend/src/components/CssGradientBackground.tsx`
- **Verification:** 重新运行 Task 2 verify 命令，所有 grep 通过，tsc EXIT=0
- **Committed in:** `3442d06`（与 Task 2 合并提交，未另开 commit 以保持每任务一提交）

**2. [Rule 3 - Blocking] `eslint-disable-next-line @typescript-eslint/no-explicit-any` 未使用警告**
- **Found during:** Task 3（eslint 阶段）
- **Issue:** 首版 webgl fallback test 在 stub `getContext` 时写了两个 disable 指令，但只有 `(orig as any)` 处真正触发 `any` 规则；上方对 `function (type: string, ...rest: unknown[])` 的 disable 是冗余指令，被 eslint 报 `Unused eslint-disable directive`
- **Fix:** 删除上方未触发规则的 disable-next-line 行，保留下方 `(orig as any).apply(...)` 前的 disable
- **Files modified:** `frontend/tests/e2e/login-redesign.spec.ts`
- **Verification:** `npx eslint tests/e2e/login-redesign.spec.ts` → 0 errors / 0 warnings
- **Committed in:** `c7d1f53`（与 Task 3 合并提交）

---

**Total deviations:** 2 auto-fixed（2 blocking，均为 grep/lint 细节）
**Impact on plan:** 都是脚本触发的细节不一致，不涉及任何功能改动；未引入计划外文件或接口；不构成 scope creep。

## Issues Encountered

- `npm audit` 首次请求因 `ECONNRESET` 失败，第二次重试成功（网络临时抖动，非持续性问题）
- `npm install --save-dev @types/three@0.184.0` 耗时约 3 分钟（安装过程中 npm 同时更新了之前 `three` 引入的 293 个传递依赖树）

## Known Stubs

无。本 Plan 创建的 hook/组件/测试均为功能完整件：
- `useWebGLSupport`：逻辑自洽，可立即返回三态之一
- `CssGradientBackground`：双色谱 + 动画 + 降级完整
- E2E 脚手架：按 TDD 原则预期 RED；所有 testid / addInitScript / localStorage key 现场已核实；没有 hardcoded 空值或 "TODO" 占位

## Threat Flags

无新增威胁面。本 Plan 仅引入前端依赖与 UI 组件，不开放网络端点、不改认证路径、不访问文件系统、不触及 schema。

## User Setup Required

None — 无外部服务配置需要；`three` 作为普通 npm 依赖已入 lock 文件。

## Next Phase Readiness

- `useWebGLSupport` 与 `CssGradientBackground` 可被 Plan 02 `ParticleWave` 与 Plan 03 `Login.tsx` 直接 import
- three 库已在 node_modules，Plan 02 可立刻 `import * as THREE from 'three'`
- Wave 0 E2E 脚手架就位，Plan 02/03 每完成一个集成点都能通过 `-g` 精确跑对应 test 做 RED→GREEN 反馈
- **无阻塞** — Plan 02/03 可进入并行开发

## Self-Check: PASSED

- `frontend/package.json` `"three": "0.184.0"` — FOUND（精确版本，无 `^`）
- `frontend/package.json` `"@types/three": "0.184.0"` — FOUND
- `frontend/package-lock.json` three integrity hash — FOUND（sha512-wtTRjG92...）
- `frontend/src/hooks/useWebGLSupport.ts` — FOUND（exports `WebGLSupport` + `useWebGLSupport`）
- `frontend/src/components/CssGradientBackground.tsx` — FOUND（named export + 6 色停点 + `prefers-reduced-motion`）
- `frontend/tests/e2e/login-redesign.spec.ts` — FOUND（5 tests / 4 testid / 3 addInitScript / `'theme-mode'` / `'social-security-auth-session'`）
- Commit `533791e` (feat three+hook) — FOUND
- Commit `3442d06` (feat CssGradientBackground) — FOUND
- Commit `c7d1f53` (test e2e scaffold) — FOUND
- Global `npm run lint` — 0 errors（2 pre-existing warnings in main.tsx / ThemeModeProvider.tsx，不在本 Plan scope）
- Global `npx tsc --noEmit` — EXIT 0
- Global `npm audit --audit-level=high --omit=dev` — EXIT 0

---
*Phase: 23-login-redesign*
*Plan: 01 (Wave 1 foundation)*
*Completed: 2026-04-19*
