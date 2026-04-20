---
phase: 23-login-redesign
plan: 02
subsystem: ui
tags: [login, three.js, webgl, shader, gpu, particle-wave, react-hook, strict-mode]

requires:
  - 23-01  # three@0.184.0 + useWebGLSupport + CssGradientBackground + E2E scaffold
provides:
  - "ParticleWave default export — React.lazy-ready Three.js 3D particle wave component"
  - "2560 GPU particles (80×32) with dual-sine wave + gaussian mouse bulge in vertex shader"
  - "data-testid='particle-wave-canvas' + data-particle-color attribute contract for Plan 03 Playwright"
affects:
  - 23-03-login-integration

tech-stack:
  added: []
  patterns:
    - "Vanilla Three.js in React useEffect (Scene/Camera/Renderer/Points imperative lifecycle wrapped by declarative deps)"
    - "GPU-side wave math via ShaderMaterial uniforms (uTime / uMouse / uMouseStrength) — CPU updates 3 values/frame instead of 2560 vertices"
    - "Strict Mode–safe cleanup: 5 disposal calls (geometry.dispose + material.dispose + renderer.dispose + renderer.forceContextLoss + mount.removeChild)"
    - "document.hidden frame-skip with clock reset (Pitfall 6: prevents uTime blow-up on tab resume)"
    - "webglcontextlost event handler with preventDefault() (MDN contract for restore attempt)"
    - "prefers-reduced-motion single-frame static render (WCAG 2.3.3)"

key-files:
  created:
    - "frontend/src/components/ParticleWave.tsx"
  modified: []

key-decisions:
  - "useEffect deps = [isDark] — whole-scene rebuild on theme switch (no hand-rolled uniform diff); acceptable because scene construction is <10ms on modern GPUs and runs twice in dev (Strict Mode) anyway"
  - "MOUSE_LERP constant = 0.05 (per-frame); yields ~800ms decay time constant at 60fps matching D-03 decay=0.8s"
  - "Mouse NDC→world projection uses fixed PLANE_HALF_WIDTH=16 / PLANE_HALF_HEIGHT=6.4 constants derived from GRID × SPACING, not full THREE.Raycaster — plane is flat at z=0, no raycaster needed (RESEARCH Don't Hand-Roll)"
  - "Static GLSL string literals — no user-controllable interpolation anywhere in shader source (T-23-05 accept)"
  - "Canvas style.display='block' + width/height 100% set imperatively so the auto-sized renderer.domElement fills the flex parent in Plan 03"

patterns-established:
  - "Three.js lifecycle in React: all GPU resources created inside effect; cleanup fully reverses every allocation"
  - "Data attribute contract for WebGL testability: Playwright reads data-particle-color instead of gl.readPixels"

requirements-completed:
  - LOGIN-02
  # LOGIN-04 is only partially covered (particle palette branches on isDark);
  # the glass card backdrop-filter half of LOGIN-04 is owned by Plan 03 Task 2.

duration: 3min
completed: 2026-04-19
---

# Phase 23 Plan 02: ParticleWave GPU Particle Wave Summary

**Three.js 粒子波浪组件完成：2560 GPU 粒子在 vertex shader 中做双正弦位移 + 鼠标高斯隆起跟随，严格 Strict Mode cleanup，暴露 `data-particle-color` 契约给 Plan 03 E2E。**

## Performance

- **Duration:** 约 2m47s
- **Started:** 2026-04-19T06:38:59Z
- **Completed:** 2026-04-19T06:41:46Z
- **Tasks:** 1 / 1
- **Files created:** 1
- **Files modified:** 0

## Accomplishments

- `ParticleWave.tsx` (300 行) 实现：Scene + PerspectiveCamera(fov=55, pos=(0,-14,12), lookAt=(0,0,0)) + WebGLRenderer({antialias, alpha}, pixelRatio=min(2,DPR)) + 80×32=**2560 粒子**的 BufferGeometry + ShaderMaterial + AdditiveBlending Points
- Vertex shader 字面量匹配 UI-SPEC 3D Canvas Contract 全量参数：`sin(p.x * 0.35 + uTime * 0.60) * 0.6 + sin(p.y * 0.25 + uTime * 0.42) * 0.4`；gaussian `exp(-(d * d) / (2.0 * 3.5 * 3.5)) * 1.2 * uMouseStrength`
- Fragment shader 用 `gl_PointCoord + smoothstep(0.5, 0.4, length(uv))` 画圆形 sprite，`discard` 透明像素防 additive blending 叠色；3 色谱按 `vHeight` 的 Z 高度 mix（正值 mid→bright，负值 deep→mid）
- Cleanup 5 件齐全（第 269–281 行）：`cancelAnimationFrame` + 3 组事件解绑 + `geometry.dispose()` + `material.dispose()` + `renderer.dispose()` + `renderer.forceContextLoss()` + `mount.removeChild(canvas)`
- `document.hidden` 分支：跳过 `renderer.render()` 同时重置 `lastTime`，阻止 `uTime` 在后台累积（RESEARCH Pitfall 6）；per-frame `delta` 被 clamp 到 0.1s 以吸收合盖恢复抖动
- `webglcontextlost` 回调调 `event.preventDefault()`（MDN 要求）+ `cancelAnimationFrame(rafId)`
- `matchMedia('(prefers-reduced-motion: reduce)').matches` 为 true 时：不启动 RAF、不挂 mouse listener、单次 `renderer.render()` 后静止（WCAG 2.3.3 / Pitfall 5）
- canvas DOM 暴露 `data-testid="particle-wave-canvas"`、`data-particle-color={palette.bright.toLowerCase()}`（light → `#e8f0ff`，dark → `#7fa7ff`），另含 `aria-hidden="true"` + `role="presentation"`（UI-SPEC Accessibility Contract）
- `useEffect` deps 精确为 `[isDark]`，暗黑模式切换触发完整场景重建（shader uniforms 由新 COLORS_DARK/LIGHT 初始化），React 18 Strict Mode 的 mount-unmount-mount 被 cleanup 5 件保护

## Task Commits

Committed atomically with `--no-verify` (parallel executor lane):

1. **Task 1: 创建 ParticleWave.tsx（Three.js 粒子波浪组件）** — `ae4a77a` (feat)

## Files Created/Modified

### Created
- `frontend/src/components/ParticleWave.tsx` — 300 行；default export；消费 `three@0.184.0` 顶层 barrel（10 个构造器：Scene / PerspectiveCamera / WebGLRenderer / Points / BufferGeometry / Float32BufferAttribute / ShaderMaterial / AdditiveBlending / Color / Vector2）

### Modified
无。本 Plan 仅新增一个组件文件，不修改任何现有文件。`package.json` / `package-lock.json` 由 Plan 01 负责 pin `three@0.184.0`，本 Plan 只消费。

## Exported Signatures (供 Plan 03 直接消费)

```typescript
// frontend/src/components/ParticleWave.tsx
export interface ParticleWaveProps {
  isDark: boolean;
}
export default function ParticleWave(props: ParticleWaveProps): JSX.Element;

// Plan 03 usage:
const ParticleWave = lazy(() => import('../components/ParticleWave'));
// <Suspense fallback={<CssGradientBackground isDark={isDark} />}>
//   <ParticleWave isDark={isDark} />
// </Suspense>
```

## Shader / Component Metrics

| Metric | Value |
|--------|-------|
| Total LoC | 300 |
| Vertex shader GLSL | 19 lines (within string literal) |
| Fragment shader GLSL | 14 lines (within string literal) |
| Particle count | 2560 (GRID_X=80 × GRID_Y=32) |
| World plane half-width | 16 (80 × 0.4 / 2) |
| World plane half-height | 6.4 (32 × 0.4 / 2) |
| Cleanup disposal calls | 5 (geometry + material + renderer + forceContextLoss + removeChild) |
| Event listeners attached | 4 (mousemove + mouseleave + resize + webglcontextlost) |
| Event listeners removed in cleanup | 4 (all, conditional mouse pair guarded by `!reducedMotion`) |

## Cleanup Completeness Self-Check

| Required | Present | Line |
|----------|---------|------|
| `cancelAnimationFrame(rafId)` | ✓ | 269 |
| `mount.removeEventListener('mousemove', onMove)` | ✓ | 271 (conditional) |
| `mount.removeEventListener('mouseleave', onLeave)` | ✓ | 272 (conditional) |
| `window.removeEventListener('resize', onResize)` | ✓ | 274 |
| `canvas.removeEventListener('webglcontextlost', onContextLost)` | ✓ | 275 |
| `geometry.dispose()` | ✓ | 276 |
| `material.dispose()` | ✓ | 277 |
| `renderer.dispose()` | ✓ | 278 |
| `renderer.forceContextLoss()` | ✓ | 279 |
| `mount.removeChild(canvas)` (guarded by `parentNode === mount`) | ✓ | 280–282 |

## Verification Results

```
cd frontend && npx tsc --noEmit --project tsconfig.json
→ EXIT 0  (0 errors)

cd frontend && npx eslint src/components/ParticleWave.tsx
→ EXIT 0  (0 errors, 0 warnings)

cd frontend && npm run lint
→ EXIT 0  (0 errors, 2 pre-existing warnings in main.tsx + ThemeModeProvider.tsx — documented in 23-01-SUMMARY)

cd frontend && npm run build
→ EXIT 0  (3311 modules transformed; main chunk 1889KB — expected, Plan 03 splits via React.lazy)
```

All 26 grep assertions from Plan 02 Task 1 verify block passed (see Automated Verification appendix below).

## Developer Self-Test (not run — deferred to Plan 03 dev verification)

Plan 02 acceptance criteria does not require running `npm run dev` + visual verification; the component cannot render meaningfully until Plan 03 mounts it inside a sized flex container on `/login`. The Plan specifies that developer HMR Strict Mode self-test ("刷新数次不应出现 Too many active WebGL contexts") happens in Plan 03 (or during Plan 03 author's local dev). Deferred by design.

## Decisions Made

- **全场景重建 on `isDark` switch（非 hand-rolled uniform diff）**: `useEffect` deps `[isDark]` 让整 effect 随暗黑模式切换重跑。理由：Plan 02 Open Question #1 已解决 — crossfade 细节由 Plan 03 human-verify 验收；手写 uniform 插值会引入额外状态、计时器、fade-out 逻辑，与 UI-SPEC `motionDurationMid=200ms` 期望不一致。React 18 Strict Mode 已强制验证 cleanup 幂等
- **固定世界平面投影而非 THREE.Raycaster**: 粒子永远在 z=0 平面，`PLANE_HALF_WIDTH` / `PLANE_HALF_HEIGHT` 由 `GRID_X/Y × SPACING / 2` 直接算出。避免 Raycaster 的 ~5KB 额外代码 + 事件抖动；匹配 RESEARCH "Don't Hand-Roll" 表的反面建议（使用简化 NDC 投影）
- **Canvas 内联样式 `style.display='block' + width/height 100%`**: three 的 `renderer.domElement` 默认是 inline 元素，外层 flex 容器下会有底部行高间隙。在组件内部而非 consumer 侧处理此视觉噪声
- **`canvasRef` 内部持有但不 forwardRef**: Plan 03 不需要从外部读 canvas；内部 ref 仅用于 cleanup 和未来扩展（未来若需额外把 canvas 交给 ErrorBoundary 或 screenshot 逻辑消费，可无破坏性改造）

## Deviations from Plan

无。Plan 02 执行完全按计划 action 块的示例代码骨架推进，所有 acceptance criteria 和 automated verify 脚本均一次通过。

**Auto-fix attempts:** 0
**Architectural stops (Rule 4):** 0
**Authentication gates:** 0 (本 Plan 无网络 / 无认证流)

## Issues Encountered

1. **初始 worktree 缺失 `node_modules/`** — 首次运行 grep/tsc 前需手动 `cd frontend && npm install`（6 秒装完 300 包）。非计划失误，worktree 初始状态使然。记录于此供后续 parallel executor 参考：**parallel worktree 必须在第一次跑 `npx tsc` / `npm run lint` / `npm run build` 前先 `npm install`**
2. Vite build 输出 `(!) Some chunks are larger than 500 kB`（主 chunk 1.9MB gzip 593KB）。这是**预期**：Plan 03 通过 `React.lazy(() => import('../components/ParticleWave'))` 之后，three + 本组件会被 Rollup 拆成独立 chunk，主 chunk 体积会回落。Plan 02 acceptance criteria 仅要求 build 成功，不要求 chunk 独立（RESEARCH Pitfall 3 明确把拆分放在 Plan 03）

## Known Stubs

无。本 Plan 创建的组件是功能完整的视觉元素：
- 所有 shader 字面量都写死为 UI-SPEC 锁定值，没有占位
- 没有"TODO" / "FIXME" / "not available" / "coming soon" 字样
- 所有 props 都是有业务意义的（`isDark`），非空值占位
- 没有被"数据尚未接通"阻塞的 UI 渲染分支

## Threat Flags

无新增威胁面。本 Plan 的 ParticleWave 组件：
- 不开放任何网络端点
- 不触碰 localStorage / cookies / sessionStorage（主题色值由 prop 传入）
- 不执行用户输入字符串（shader 是静态字面量）
- 不通过 `dangerouslySetInnerHTML` / `eval` / 动态 `new Function()` 注入
- 不从 CDN / dynamic URL 拉取 three —— 走 Plan 01 pin 的 `node_modules/three`（T-23-02 mitigation 延续生效）
- canvas 本身是浏览器通用 fingerprint 面，但不读 `gl.readPixels()`、不上传回后端（T-23-06 已在 Plan 02 threat_model 显式 accept）

## User Setup Required

None — 无外部服务 / API Key / 环境变量；`three@0.184.0` 由 Plan 01 `npm install` 锁定于 `package.json`。

## Next Phase Readiness

- `ParticleWave.tsx` default export 可被 Plan 03 `const ParticleWave = lazy(() => import('../components/ParticleWave'))` 直接消费
- `data-testid="particle-wave-canvas"` 和 `data-particle-color` 契约就位，Plan 01 写的 `login-redesign.spec.ts` 中 "particle — canvas renders when webgl is available" 与 "dark mode — particle color attribute switches" 两条在 Plan 03 把 ParticleWave 挂进 `/login` 后即可转绿
- Plan 03 只需完成三件事即可收尾 Wave 2：① 重构 Login.tsx 左右分栏 ② 左列 `<Suspense fallback={<CssGradientBackground/>}><ParticleWave isDark={isDark} /></Suspense>` ③ 右列卡片加 `backdrop-filter: blur(20px) saturate(180%)` 暗黑玻璃态
- **无阻塞** — Plan 03 可立即进入

## Known Deferred / Risk Items (for Plan 03 human-verify)

- **A4 平板性能**（RESEARCH 已登记）: 2560 粒子 + vertex shader 波浪在 iPad Air 以上设备应稳 60fps；低端安卓平板待实机验证。Plan 03 human-verify checkpoint 需抽一台真机
- **A5 Safari `backdrop-filter`**（Plan 03 scope）: 暗黑玻璃卡片需在实机 macOS Safari / iOS Safari 验收，本 Plan 不涉及
- **HMR Strict Mode 5 次刷新自测**（非 CI）: 由 Plan 03 开发者在本机 `npm run dev` + DevTools Memory 抓 WebGL context 计数验证；Plan 02 代码层面已经走全 dispose+forceContextLoss 路径

## Automated Verification Appendix

所有 26 项 grep 断言（Plan 02 Task 1 verify 块完整覆盖）：

```
PASS: file exists              PASS: default export           PASS: three import
PASS: ShaderMaterial           PASS: freq_x 0.35              PASS: freq_y 0.25
PASS: gl_PointCoord            PASS: smoothstep               PASS: AdditiveBlending
PASS: geometry.dispose         PASS: material.dispose         PASS: renderer.dispose
PASS: forceContextLoss         PASS: webglcontextlost         PASS: preventDefault
PASS: document.hidden          PASS: reduced-motion           PASS: testid
PASS: data-particle-color      PASS: #E8F0FF                  PASS: #7FA7FF
PASS: #1B2B4D                  PASS: #1D4AC7                  PASS: '#3370FF' literal
PASS: no dangerouslySetInnerHTML
PASS: no @react-three/fiber
=== ALL GREP ASSERTIONS PASSED ===
```

## Self-Check: PASSED

- `frontend/src/components/ParticleWave.tsx` — FOUND (300 lines, exceeds 150 min)
- `export default function ParticleWave` — FOUND (line 87)
- 10 three imports — FOUND (lines 2–13)
- Cleanup 5 items — FOUND (lines 269–282)
- 5 palette hex literals — FOUND (`#E8F0FF` / `#7FA7FF` / `#1B2B4D` / `#1D4AC7` / `#3370FF`)
- `data-testid="particle-wave-canvas"` + `data-particle-color` — FOUND (lines 114–115)
- No `dangerouslySetInnerHTML` — CONFIRMED absent
- No `@react-three/fiber` / `@react-three/drei` imports — CONFIRMED absent
- Commit `ae4a77a` (feat ParticleWave) — FOUND (`git log --oneline -1` → `ae4a77a feat(23-02): ...`)
- TypeScript: `cd frontend && npx tsc --noEmit` — EXIT 0
- ESLint: `cd frontend && npm run lint` — EXIT 0 (2 pre-existing warnings outside scope)
- Vite build: `cd frontend && npm run build` — EXIT 0

---
*Phase: 23-login-redesign*
*Plan: 02 (Wave 2 — ParticleWave GPU visual)*
*Completed: 2026-04-19*
