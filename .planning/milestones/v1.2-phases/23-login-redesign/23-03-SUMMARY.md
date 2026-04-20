---
phase: 23-login-redesign
plan: 03
subsystem: ui
tags: [login, react-lazy, suspense, matchmedia, backdrop-filter, particle-wave, glass-card, brand-panel, human-verify]

requires:
  - phase: 23-01
    provides: "useWebGLSupport hook + CssGradientBackground fallback + Wave 0 E2E scaffolding"
  - phase: 23-02
    provides: "ParticleWave default export (React.lazy-ready) + data-particle-color testability contract"
provides:
  - "BrandPanel named component — 左侧品牌文字层（wordmark / slogan / sub-slogan / copyright）"
  - "Reassembled Login.tsx with split-layout (60:40 desktop / 50:50 tablet / single-column mobile)"
  - "React.lazy + Suspense chunk splitting for ParticleWave (frees main bundle from three-js weight)"
  - "Dark-mode glass card via backdrop-filter (blur 20px + saturate 180%) with double-prefix for Safari"
  - "Independent `window.matchMedia('(min-width: 1024px)')` driver for UI-SPEC 1024 breakpoint"
  - "Theme toggle button on login page (post-checkpoint polish)"
  - "Feishu login loading spinner + disabled-while-pending (post-checkpoint polish)"
  - "Backend Feishu OAuth httpx timeout bump + error wrapping (post-checkpoint polish)"
affects: []

tech-stack:
  added: []
  patterns:
    - "React.lazy at module top-level (NOT inside component) to prevent re-creating the lazy wrapper on every render"
    - "Suspense fallback === WebGL fallback component (single UI source of truth — no white flash during chunk load)"
    - "Independent matchMedia state for UI-SPEC 1024 breakpoint, orthogonal to the 992 breakpoint owned by useResponsiveViewport"
    - "Preserved-byte-for-byte refactor: wrap existing auth/form JSX in new layout shell instead of rewriting handlers"
    - "Double-prefix backdrop-filter (WebkitBackdropFilter + backdropFilter) with boxShadow:'none' for Safari compat"
    - "httpx.AsyncClient timeout granularity: separate connect / read / write / pool + error wrapping into domain exception"

key-files:
  created:
    - "frontend/src/components/BrandPanel.tsx"
    - ".planning/phases/23-login-redesign/deferred-items.md"
  modified:
    - "frontend/src/pages/Login.tsx"
    - "backend/app/services/feishu_oauth_service.py"
    - ".planning/ROADMAP.md"

key-decisions:
  - "UI-SPEC 1024px 桌面断点由独立 window.matchMedia 驱动，不复用 useResponsiveViewport 的 992 边界（checker ISS-04）"
  - "LeftCanvas: webgl='fallback' 直接渲染 CssGradientBackground；webgl='webgl'/'loading' 走 Suspense(fallback=CssGradientBackground) + ParticleWave，避免 loading 态 50ms 闪白"
  - "React.lazy 声明必须在 module top-level — 组件内声明会每次 render 重建 lazy wrapper，破坏 chunk 缓存"
  - "暗模式玻璃态同时写 WebkitBackdropFilter 和 backdropFilter 两个前缀；boxShadow 故意为 'none'（Safari bug：backdrop-filter 与 box-shadow 共用会失效）"
  - "人工验证发现左右面板背景不一致造成视觉分割感 -> 左面板改用共享 BG_LAYOUT（去除 '#FFFFFF vs colors' 的硬边）"
  - "飞书登录加入 loading 状态 + disabled（原先点击后无反馈直接跳转）"
  - "后端 httpx 超时 connect=15s / read=20s（原默认 5s 过短），并把 TimeoutException / HTTPError 包装成 FeishuOAuthError 返回友好 400"

patterns-established:
  - "Pattern 1: React.lazy 声明位置规则 — `const X = lazy(() => import(...))` 必须在组件函数外"
  - "Pattern 2: Suspense fallback 复用降级组件 — 让 loading 过程无视觉噪声"
  - "Pattern 3: 独立断点 matchMedia 与 hook 并存 — 不强行修改已有 hook 来追赶 UI-SPEC 边界"
  - "Pattern 4: httpx 错误域化 — TimeoutException/HTTPError -> FeishuOAuthError，不让 httpx 异常泄漏到 API 层"

requirements-completed:
  - LOGIN-01
  - LOGIN-02
  - LOGIN-03
  - LOGIN-04

duration: ~75min (含 checkpoint 验证 + polish)
completed: 2026-04-19
---

# Phase 23 Plan 03: Login-Redesign Integration Summary

**将 Plan 01/02 的降级 hook + 粒子组件装配到 Login.tsx：左右分栏（matchMedia 1024）+ React.lazy 粒子背景 + Suspense 降级 + 暗黑玻璃卡片 + 独立 BrandPanel 文字层，保留原认证逻辑零回归；人工 checkpoint 通过后追加飞书 loading、主题切换按钮、后端 httpx 超时修复四项 polish。**

## Performance

- **Duration:** ~75 分钟（含 human-verify checkpoint 与 polish 回路）
- **Started:** 2026-04-19T06:48:48Z（Task 1 commit 时间）
- **Completed:** 2026-04-19T08:03:50Z（polish commit 时间）
- **Tasks:** 3 / 3（2 自动 + 1 human-verify checkpoint）
- **Files created:** 2（BrandPanel.tsx + deferred-items.md）
- **Files modified:** 3（Login.tsx + feishu_oauth_service.py + ROADMAP.md）

## Accomplishments

- `BrandPanel.tsx`（111 行）承载 4 条 UI-SPEC 锁定文案（`社保公积金管理系统` / `多地区社保数据，一个系统统一汇聚` / `自动识别 · 智能映射 · 一键导出` / `© 社保公积金管理系统`），仅使用 3 个字号字面量（20 / 28 / 14）与 2 个字重（400 / 600），`pointerEvents: none` + `zIndex: 2` 保障粒子 mousemove 事件穿透
- `Login.tsx`（184 行重构，150 行新增 / 34 行删除）引入 React.lazy(ParticleWave) + Suspense + LeftCanvas 分流；暗模式 Card `rgba(30, 35, 45, 0.72)` + `blur(20px) saturate(180%)` 双前缀玻璃态；`window.matchMedia('(min-width: 1024px)')` 精确驱动桌面/平板断点，不强行降级为 useResponsiveViewport 的 992
- 原认证逻辑完整保留（11 条 grep 全部命中）：`handleCredentialSubmit` / `handleEmployeeSubmit` / `handleFeishuLogin` / `handleCandidateSelect` / `feishuOAuthCallback` / `CandidateSelectModal` / `DEFAULT_WORKSPACE_BY_ROLE` / `isAuthenticated` 早返回 / `writeAuthSession` / `pending_candidates` / `bind:` 分支转发
- Wave 0 E2E 5 个测试从 Plan 01 的 RED（testid 未存在）→ Plan 03 Task 2 的 GREEN（5/5 PASS in chromium）
- `dist/assets/` 下 `ParticleWave-*.js` chunk 成功从主 bundle 中切出（Task 2 acceptance gate 记录：499KB / gzip 127KB）
- Human-verify checkpoint 6 项（桌面 WebGL / 暗模式 Safari / 响应式 375-820-1024 / WebGL 降级 / reduced-motion / 认证回归）全部签字通过
- 人工验证发现的 5 项问题全部在 polish commit `1c8faae` 内修复（主题切换按钮、左面板背景一致化、飞书登录 loading、BrandPanel 亮模式可读性、后端 httpx 超时）

## Task Commits

每个任务与 polish 均独立原子提交（`--no-verify` 对齐 parallel executor lane 规范）：

1. **Task 1: 创建 BrandPanel 组件（左侧品牌文字层）** — `03e9c3c` (feat)
2. **Task 2: 重构 Login.tsx — 分栏 + lazy ParticleWave + 玻璃卡片** — `0fcd765` (feat)
3. **Task 2 ancillary: 登记 13 个 pre-existing E2E 失败为 deferred items** — `9f1af25` (docs)
4. **Post-checkpoint polish（人工验证反馈合并）** — `1c8faae` (feat)
5. **Task 3 checkpoint 签字（human-verify approved）** — `494844d` (docs)

Plan metadata（本 SUMMARY）：orchestrator 另开 commit。

## Files Created/Modified

### Created
- `frontend/src/components/BrandPanel.tsx` — 111 行；named export `BrandPanel`；Ant Design `Typography.Text` 包裹顶部 wordmark 与底部 copyright；4 条 UI-SPEC 锁定文案；`data-testid="brand-panel"`；亮/暗模式颜色分支（polish 后亮模式改为深蓝文本以适配浅色粒子背景）
- `.planning/phases/23-login-redesign/deferred-items.md` — 33 行；记录 acceptance gate 期间发现的 13 个 pre-existing E2E 失败（stash-and-rerun 方法验证均为 Phase 23 前已存在），建议后续"Responsive + post-auth route regression"专项处理

### Modified
- `frontend/src/pages/Login.tsx` — 184 行差（+150 / -34）；引入 `lazy` / `Suspense` / `useEffect` / `useState` / `useWebGLSupport` / `useThemeMode` / `useResponsiveViewport.isMobile`；新增 `LeftCanvas` 内部组件分流降级；卡片样式双分支（亮实色白 / 暗玻璃态）；外层 flex 容器 + `isMobile` 条件渲染左侧；polish 追加右上角 `ThemeToggleButton`、飞书按钮 `loading`/`disabled`、左面板 `bgLeftPanel = colors.BG_LAYOUT`
- `backend/app/services/feishu_oauth_service.py` — 52 行差（+30 / -22）；`httpx.Timeout(connect=15, read=20, write=10, pool=5)`；`try/except httpx.TimeoutException / httpx.HTTPError` 统一包装为 `FeishuOAuthError` 并附带可友好展示的 message；API 层 400 响应而非 500 泄漏 httpx stacktrace
- `.planning/ROADMAP.md` — 6 行差；phase 23 行进度同步

## Decisions Made

### Architectural

- **React.lazy 声明放 module top-level**：首次写法曾尝试在 `LoginPage` 函数体内 `const ParticleWave = lazy(...)`，会在每次 `LoginPage` 重渲染时重建 lazy wrapper，导致 chunk 无法缓存且 Suspense 每次 fallback 都重走一遍 pending。最终声明在 `import` 语句之后、函数之前。
- **LeftCanvas 三态分流**：`webgl === 'fallback'` 直接挂 `CssGradientBackground`（不触发懒加载 chunk）；`'webgl'` / `'loading'` 都挂 `<Suspense fallback={CssGradientBackground}><ParticleWave /></Suspense>`。理由：`loading` 态只持续 0-50ms（hook 初始 flush 前），让 Suspense fallback 接管避免渲染抖动。
- **UI-SPEC 1024 独立 matchMedia**：Plan checker ISS-04 已明确不允许把 UI-SPEC 的 1024 桌面断点降级为 useResponsiveViewport 的 992。解决方案是加一个独立的 `isDesktop1024` useState + 一次性 matchMedia effect，legacy Safari 兜底用 `addListener`。
- **暗模式 glass card boxShadow='none'**：Safari 已知 bug — `backdrop-filter` 与 `box-shadow` 共用会让 backdrop-filter 在某些合成层失效；UI-SPEC 明确要求玻璃态时关闭阴影。

### Post-checkpoint polish

- **左面板背景改用共享 BG_LAYOUT**：人工验证时发现 `white` 左面板 vs `colors.BG_LAYOUT` 右面板造成视觉"硬边"分割感。改为两侧背景一致后视觉更整体，粒子/渐变在同色背景上渐隐过渡更自然。
- **飞书登录加 loading**：原实现点击后立即 `window.location.href =` 跳转，但 OAuth state 生成有 ~200-500ms 往返，期间按钮无反馈，用户容易以为"点了没反应"会再点。加 `loading={feishuPending}` + `disabled` 后解决。
- **后端 httpx 超时**：原使用默认 5s，人工验证时飞书 `access_token` 端点偶现 8-12s 响应，触发 ReadTimeout 抛 500。提升为 connect=15 / read=20 并把异常收敛到 `FeishuOAuthError`，让 API 层返回友好的 400 + 中文错误。

## Deviations from Plan

### Auto-fixed Issues (Task 2 期间)

**1. [Rule 3 - Blocking] 记录 13 个 pre-existing E2E 失败为 deferred items**
- **Found during:** Task 2（acceptance gate — 全量 E2E 回归）
- **Issue:** acceptance gate 要求 `npm run test:e2e` 全量无新红。首跑 13 个失败（compare-diff / feishu-settings / fusion-aggregate / responsive 套件）。
- **Investigation:** stash Plan 03 Task 2 全部改动 → checkout `HEAD~1`（Plan 02 tip）→ 重跑 → 同样 13 个失败全部复现。结论：非 Phase 23 引入。
- **Fix:** 建立 `deferred-items.md`，逐条记录测试路径 / 行号 / 可疑原因，建议后续"Responsive + post-auth route regression"专项处理。acceptance gate 的满足条件判定为"Wave 0 5/5 绿 + build chunk splitting 确认"，符合 Plan 03 Output 契约。
- **Files modified:** `.planning/phases/23-login-redesign/deferred-items.md`（新建）
- **Verification:** stash-and-rerun 复现 13 个失败确认无关；Wave 0 5/5 PASS 继续满足 Task 2 done 条件
- **Committed in:** `9f1af25`

### Post-checkpoint polish (Task 3 验证过程中发现 → Rule 2 missing critical)

**2. [Rule 2 - Missing Critical] 飞书登录缺少 loading 反馈**
- **Found during:** Task 3 checkpoint 验证步骤 6（认证回归）
- **Issue:** 点击"使用飞书登录"按钮后立即跳转 OAuth，但 state 生成往返有 200-500ms 延迟，期间按钮无任何视觉反馈；用户会误判"点击无效"而重复点击。
- **Fix:** 新增 `feishuPending` state，`handleFeishuLogin` async 期间 `setFeishuPending(true)`，Button 加 `loading={feishuPending}` + `disabled={feishuPending}`。
- **Files modified:** `frontend/src/pages/Login.tsx`
- **Committed in:** `1c8faae`

**3. [Rule 1 - Bug] BrandPanel 亮模式文本在浅色粒子背景上不可读**
- **Found during:** Task 3 checkpoint 验证步骤 2（亮模式视觉）
- **Issue:** 亮模式粒子色谱偏白蓝（`#E8F0FF` bright），BrandPanel 原亮模式文字 `#FFFFFF` 在其上对比度不足（估算 < 3:1，低于 WCAG 4.5:1），slogan 几乎不可见。
- **Fix:** 亮模式 wordmark / slogan 改为深蓝（`#1D4AC7` 族）+ 浅色 textShadow（`rgba(255,255,255,0.4)`），暗模式保持原亮色不变。
- **Files modified:** `frontend/src/components/BrandPanel.tsx`
- **Committed in:** `1c8faae`

**4. [Rule 2 - Missing Critical] 左右面板背景不一致造成视觉分割感**
- **Found during:** Task 3 checkpoint 验证步骤 1（桌面布局）
- **Issue:** 左面板 `#FFFFFF`（亮模式） vs 右面板 `colors.BG_LAYOUT`（偏灰白），在 60:40 分割处形成硬边；粒子组件本身渲染在左面板之上，但主题切换瞬间会露出背景硬边，破坏沉浸感。
- **Fix:** 左面板容器 `background: bgLeftPanel = isDark ? '#141414' : colors.BG_LAYOUT`（与右面板一致），让粒子/渐变在同色底上渐隐过渡。
- **Files modified:** `frontend/src/pages/Login.tsx`
- **Committed in:** `1c8faae`

**5. [Rule 2 - Missing Critical] 登录页缺少主题切换入口**
- **Found during:** Task 3 checkpoint 验证步骤 2（暗模式切换）
- **Issue:** 登录页 AuthLayout 外部的 Header/ThemeSwitcher 未挂载（登录前无 Layout），用户无法在登录页直接体验/切换亮暗模式；文档 / UI-SPEC 隐含要求"登录页暗模式必须可视"。
- **Fix:** 登录页右上角新增 fixed-position 玻璃背景小按钮，调 `useThemeMode().setMode` 切换 light/dark。
- **Files modified:** `frontend/src/pages/Login.tsx`
- **Committed in:** `1c8faae`

**6. [Rule 1 - Bug] 后端 httpx 超时过短 + 异常未收敛**
- **Found during:** Task 3 checkpoint 验证步骤 6（飞书 OAuth 回调）
- **Issue:** 飞书 `/access_token` 端点偶现 8-12s 响应，原 httpx 默认 5s 超时触发 `ReadTimeout`，FastAPI 返回 500 + httpx 堆栈，用户看到英文报错无法归因。
- **Fix:**（a）`httpx.Timeout(connect=15, read=20, write=10, pool=5)`；（b）`try/except httpx.TimeoutException / httpx.HTTPError` 统一包装 `FeishuOAuthError("飞书服务暂时不可用，请稍后重试。")`；（c）API 层 400 响应 + 友好中文。
- **Files modified:** `backend/app/services/feishu_oauth_service.py`
- **Committed in:** `1c8faae`

---

**Total deviations:** 6 auto-fixed（1 blocking + 3 missing critical + 2 bugs；全部为人工验证期间发现的正确性/安全性修复）
**Impact on plan:** 没有 scope creep；所有 polish 项都是 Plan 03 Output 契约内"登录页重构"职责的子集（"保留认证逻辑零回归"隐含"认证流必须在生产网络抖动下工作"）。13 个 pre-existing 失败已明确归档到 deferred-items 供后续专项处理，不拖延本 Plan 完成。

## Issues Encountered

1. **Plan 02 -> Plan 03 衔接时 `React.lazy` 位置误放**：首次把 `const ParticleWave = lazy(() => import('../components/ParticleWave'))` 放在 `LoginPage` 函数体内，Strict Mode 双渲染下每次都重新创建 lazy wrapper，Suspense fallback 出现 200ms 闪烁。`commit 0fcd765` 前已修正到 module top-level（import 之后、组件函数之前）。
2. **acceptance gate 13 个 E2E 失败复现确认**：首跑全量 E2E 13 红，需要 stash-and-rerun 才能确认与 Phase 23 无关；花了约 6 分钟做复现验证 + 文档化。产出是 `deferred-items.md`，有明确 follow-up 价值。
3. **Human-verify 发现 5 项改进**：不是单一 bug，而是多个 UX/兼容/认证细节。全部收敛到一次 polish commit 而非多个小 commit，方便审阅和 rollback。

## User Setup Required

None — 无外部服务 / API Key 新增要求。飞书 OAuth 凭据与 Phase 22 已配置的一致；httpx 超时改动仅影响客户端行为，不新增环境变量。

## Next Phase Readiness

- **Login.tsx 分栏 + 粒子 + 玻璃卡片 + 降级 + Brand 文字层** 全部就位，人工签字 approved
- **Wave 0 5 个 E2E 测试**（layout-desktop / layout-mobile / particle / webgl-fallback / dark-mode）在 chromium 下 5/5 PASS，作为后续回归 gate
- **ParticleWave chunk splitting** 确认生效（`dist/assets/ParticleWave-*.js`）
- **13 个 pre-existing E2E 失败** 已归档到 `deferred-items.md`，建议开 Phase 24 或维护 phase 专项处理
- **Phase 23 三个 Plan** 全部完成，可进入 `gsd-complete-phase` 归档流程

## Automated Verification Recap

Task 2 verify 全部 19 条 grep 断言 + tsc + lint + e2e 快速反馈已通过（详见 `0fcd765` commit body）：

```
PASS: lazy(() => import('../components/ParticleWave'
PASS: useWebGLSupport                PASS: useResponsiveViewport
PASS: useThemeMode                   PASS: CssGradientBackground
PASS: BrandPanel                     PASS: Suspense
PASS: data-testid="login-form-card"  PASS: 登录 · 社保公积金管理系统
PASS: rgba(30, 35, 45, 0.72)         PASS: WebkitBackdropFilter
PASS: blur(20px) saturate(180%)      PASS: min-width: 1024px
PASS: handleCredentialSubmit         PASS: handleEmployeeSubmit
PASS: handleFeishuLogin              PASS: handleCandidateSelect
PASS: feishuOAuthCallback            PASS: CandidateSelectModal
PASS: DEFAULT_WORKSPACE_BY_ROLE      PASS: no dangerouslySetInnerHTML
PASS: npx tsc --noEmit EXIT 0        PASS: npm run lint 0 errors
PASS: npm run test:e2e login-redesign.spec.ts 5/5 GREEN
=== ALL GREP ASSERTIONS PASSED ===
```

## Human Verification Signature

**Date:** 2026-04-19
**Verifier:** User (project owner)
**Verdict:** approved

**Per-step results:**

| Step | Scope | Result | Notes |
|------|-------|--------|-------|
| 1 | Desktop WebGL (60:40, 2560 particles, mouse follow) | PASS | 无 "Too many active WebGL contexts" 警告 |
| 2 | Dark mode + macOS Safari glass card | PASS（经 polish 后）| 亮模式文本可读性经 BrandPanel 颜色修复 |
| 3 | Responsive (375 / 820 / 1024) | PASS | 1024 matchMedia 在切换瞬间即时响应 |
| 4 | WebGL 降级（DevTools Disable WebGL） | PASS | 左侧正确回落 CssGradientBackground，认证不受影响 |
| 5 | Reduced motion（macOS 减少动态效果）| PASS | 粒子静止，CSS 渐变浮动停止 |
| 6 | 认证回归（凭据登录 / 员工查询 / 飞书 OAuth）| PASS（经 polish 后）| 飞书 loading + 后端超时修复前此步曾 FAIL |

**Remaining minor visual items:** 无。Polish 已覆盖所有人工验证反馈。

## Known Stubs

无。所有组件均功能完整：BrandPanel 有真实文案与主题分支；Login.tsx 的 LeftCanvas 在三种 WebGL 态下都有确定渲染；玻璃卡片样式在亮/暗两模式都有完整数值；主题切换按钮调用真实 `useThemeMode.setMode`；飞书按钮的 `loading` 依赖真实的异步 handler pending 状态。

## Threat Flags

无新增威胁面。本 Plan 新增 / 修改的内容均在 23-03-PLAN `<threat_model>` 已覆盖范围内：
- `React.lazy()` 路径是静态字面量 `'../components/ParticleWave'`，无用户输入拼接（T-23-10 继承 accept）
- `document.title = '登录 · 社保公积金管理系统'` 仅泄露应用名（T-23-09 继承 accept）
- 飞书 OAuth 回调路径未改动（T-23-08 继承 accept，Phase 22 已验证）
- `dangerouslySetInnerHTML` 在 Task 1/2/polish 中均经 grep 验证不存在（T-23-03 mitigated）
- httpx 超时调整不改变信任边界，只是让服务端在上游抖动时返回 400 而非 500，属于可靠性改进

## Self-Check: PASSED

文件与提交存在性验证：

- `/Users/mac/PycharmProjects/5xyj/frontend/src/components/BrandPanel.tsx` — FOUND（111 行）
- `/Users/mac/PycharmProjects/5xyj/frontend/src/pages/Login.tsx` — FOUND（453 行）
- `/Users/mac/PycharmProjects/5xyj/backend/app/services/feishu_oauth_service.py` — FOUND（9387 bytes）
- `/Users/mac/PycharmProjects/5xyj/.planning/phases/23-login-redesign/deferred-items.md` — FOUND（33 行）
- Commit `03e9c3c` (feat BrandPanel) — FOUND
- Commit `0fcd765` (feat Login.tsx refactor) — FOUND
- Commit `9f1af25` (docs deferred-items) — FOUND
- Commit `1c8faae` (feat polish) — FOUND
- Commit `494844d` (docs checkpoint approval) — FOUND

---
*Phase: 23-login-redesign*
*Plan: 03 (Wave 3 — integration + human-verify)*
*Completed: 2026-04-19*
