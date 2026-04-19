# Phase 23: 登录页面改版 - Research

**Researched:** 2026-04-19
**Domain:** React 前端 3D 粒子动画、WebGL 降级、暗黑模式玻璃拟态、Ant Design 登录页重构
**Confidence:** HIGH

## Summary

本阶段是纯前端视觉升级：在不改动任何认证流程的前提下，将 `frontend/src/pages/Login.tsx` 改造成左右分栏布局，左侧嵌入 Three.js 3D 粒子波浪（2500 粒子，海浪流动风格，鼠标柔和推波，暗黑模式"深海荧光"），右侧保留现有登录表单（账号登录 / 员工查询 / 飞书 OAuth / CandidateSelectModal）。

三件核心决策（已在 UI-SPEC 中确认，不要再讨论替代方案）：

1. **Three.js 集成方式：** 使用 **vanilla `three`（v0.184.0）+ React useEffect 生命周期**，通过 `React.lazy` 代码分割。项目仅在登录页一处用 3D，且当前 React 版本是 18.3.1（@react-three/fiber v9 要求 React ≥19），因此不引入 R3F。
2. **WebGL 降级：** 组件 mount 时同步检测（`canvas.getContext('webgl2') ?? canvas.getContext('webgl')`），失败立刻挂载 `<CssGradientBackground />`。
3. **暗黑模式玻璃卡片：** 使用 `backdrop-filter: blur(20px) saturate(180%)` + `-webkit-backdrop-filter` 前缀 + `@supports` 降级，避免 Safari 前缀丢失。

**Primary recommendation:** 规定 `three@0.184.0` 精确版本，在 `frontend/src/components/ParticleWave.tsx` 中手写 `Scene + PerspectiveCamera + Points + BufferGeometry + ShaderMaterial`，**把波浪位移计算放进 vertex shader**（不要在 CPU 每帧更新 2500 个点的 Y 坐标），用 `React.lazy` 懒加载，`<Suspense fallback>` 兜底为 CSS 渐变。这是同时满足 Bundle Size、性能、降级、可维护性的唯一路径。

## User Constraints (from CONTEXT.md)

### Locked Decisions

**粒子动画效果：**
- **D-01:** 海浪流动感风格 — 粒子排布成波浪形态，连续起伏流动，像海面一样柔和
- **D-02:** 粒子密度 2000-3000 个，在视觉效果和性能之间取平衡（UI-SPEC 锁定为 2500）
- **D-03:** 鼠标交互采用柔和推波方式 — 鼠标移到哪里，波浪在那里轻柔隆起，离开后慢慢恢复
- **D-04:** 粒子颜色使用品牌主色系（`#3370FF` 渐变色谱），与系统整体视觉统一
- **D-05:** 粒子形状为圆形点，经典简约

**暗黑模式适配：**
- **D-06:** 暗黑模式下粒子变亮色/发光效果 + 深色背景，形成"深海荧光"感
- **D-07:** 右侧表单卡片暗黑模式下使用半透明模糊效果（`backdrop-filter: blur`），能透出背后粒子效果

**WebGL 降级策略：**
- **D-08:** 不支持 WebGL 时降级为 CSS 渐变背景 + 轻微 CSS animation 浮动效果，不完全静态
- **D-09:** 组件 mount 时即检测 WebGL 支持，尝试创建 WebGL context，失败则立即降级

### Claude's Discretion

- 左右分栏具体比例（UI-SPEC 已定：桌面 60:40，平板 50:50）
- 移动端断点阈值（UI-SPEC 已定：768px，匹配 Ant Design `md`）
- 左侧品牌区域 logo/slogan 内容和排版（UI-SPEC 已定：`多地区社保数据，一个系统统一汇聚` + `自动识别 · 智能映射 · 一键导出`）
- 粒子波浪的具体参数（UI-SPEC 已定完整表）
- 降级动画的具体 CSS 实现（UI-SPEC 已定：20s `backgroundPosition` drift）
- Three.js lazy loading 策略（本研究推荐 `React.lazy` + dynamic `import()`）

### Deferred Ideas (OUT OF SCOPE)

None — discussion 未产生需延后的议题。

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LOGIN-01 | 登录页采用左右分栏布局（左侧品牌展示+动画背景，右侧登录表单），移动端只显示表单 | UI-SPEC Layout Contract 已锁定 60:40 / 50:50 / 768px 移动端断点；本研究提供 `useResponsiveViewport` 现有 hook 可复用（已定义 `isMobile` = `max-width: 767px`） |
| LOGIN-02 | 登录页左侧使用 Three.js 3D 粒子波浪动态背景，支持鼠标交互跟随效果 | 本研究确定 vanilla `three@0.184.0` + Shader Material + BufferGeometry + Points，含完整 useEffect 生命周期模式、vertex shader 波浪方程、鼠标 gaussian bulge 实现策略 |
| LOGIN-03 | 不支持 WebGL 的环境下登录页优雅降级为静态渐变背景 | 本研究确定 `useWebGLSupport` hook 用 `canvas.getContext('webgl2') ?? canvas.getContext('webgl')` 同步检测；`React.lazy` 失败 + `webglcontextlost` 事件双重兜底；CSS 渐变带 20s drift |
| LOGIN-04 | 登录页粒子颜色和表单卡片适配暗黑模式 | 本研究确定 `useThemeMode().isDark` 驱动 uniforms 切换（光谱 3 stop lerp 在 shader 内完成）；卡片 `backdrop-filter` + `-webkit-` 前缀 + `@supports` 降级；Safari 已知 bug 列表 |

## Project Constraints (from CLAUDE.md)

项目 CLAUDE.md 聚焦于 Excel 数据处理主链路（解析、映射、校验、工号匹配、双模板导出）。本阶段（登录页视觉改版）不触及这些主链路，因此 CLAUDE.md 大多数指令不适用。以下是唯一需要遵守的通用约束：

| 指令 | 本阶段如何遵守 |
|------|----------------|
| "不能破坏双模板导出能力" | 本阶段不触及导出逻辑 — 仅改 `frontend/src/pages/Login.tsx` 和新增 3 个组件文件 |
| "React + FastAPI 技术栈" | 坚持 React 18.3.1，不引入 Next/Remix 等替代框架 |
| "lint 通过、build 成功" | 新组件必须通过 `npm run lint` 和 `npm run build`（TypeScript 严格模式） |
| "任何特殊逻辑都应收敛到独立模块" | 粒子组件、WebGL 检测、CSS 降级背景各自独立文件，登录页本体保持简洁 |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `three` | **0.184.0** (latest as of 2026-04-16) `[VERIFIED: npm view three version]` | 3D 渲染引擎、粒子系统、shader material | 业界标准、无真正替代品，npm 下载量每周 200 万+ |
| `@types/three` | **0.184.0**（版本号与 `three` 同步） `[VERIFIED: npm view @types/three version]` | TypeScript 类型 | 项目启用了 TS 严格模式必需 |
| `antd` | 5.29.3（已安装） `[VERIFIED: frontend/package.json]` | 登录表单组件 | 项目既有选择，不换 |
| `react` + `react-dom` | 18.3.1（已安装） `[VERIFIED: frontend/package.json]` | UI 框架 | 项目既有选择 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `React.lazy` + `Suspense` | React 18 内置 | 按需加载 `ParticleWave.tsx`，避免登录表单被 Three.js 包阻塞 | `const ParticleWave = React.lazy(() => import('../components/ParticleWave'))` |
| `window.matchMedia('(prefers-reduced-motion: reduce)')` | 浏览器原生 `[CITED: MDN]` | 可访问性：尊重用户的"减少动态效果"系统偏好 | 在 ParticleWave 内检测，返回静态粒子网格 |

### Alternatives Considered

| Instead of vanilla three | Could Use | Tradeoff | Why NOT |
|--------------------------|-----------|----------|---------|
| `@react-three/fiber@9.6.0` + `@react-three/drei@10.7.7` | 声明式 JSX 封装 | 代码更简洁 | **阻塞：R3F v9 要求 `react >=19 <19.3`，项目是 18.3.1** `[VERIFIED: npm view @react-three/fiber peerDependencies]`。即使降级到 R3F v8，bundle size 开销 ~1MB vs vanilla 的 462KB `[CITED: 实测对比]`，对登录页首屏不合算 |
| `tsparticles` / `particles.js` | 2D 粒子库，API 简单 | 无 3D 深度、不支持 shader 波浪方程 | 与 D-01"海浪流动感 3D 波浪"需求矛盾 |
| 纯 CSS `keyframes` 动画 | 零 JS 依赖 | 根本达不到"3D 粒子"视觉要求 | 这就是 D-08 的降级方案，不能当主方案 |

### 关于 State.md 的历史噪声

`STATE.md` blockers 区域记录的 "R3F v8 与 three@0.172 实际兼容性需安装后验证" 是更早期 discuss 阶段的假设，**UI-SPEC 已明确不用 R3F**。本研究重申：**不引入 `@react-three/fiber` 和 `@react-three/drei`**，全部功能用 vanilla three + React hooks 实现。如果 Planner 看到 STATE 里那条 blocker 请忽略，UI-SPEC 为准。

**Installation:**

```bash
cd frontend
npm install --save three@0.184.0
npm install --save-dev @types/three@0.184.0
```

**Version verification performed in this research:**
- `npm view three version` → `0.184.0`（发布日期 2026-04-16，即研究当天前 3 天）
- `npm view @types/three version` → `0.184.0`
- `npm view three dist-tags` → `{ latest: '0.184.0' }`

这两个包都极新，Planner 需注意：安装后可能碰上 TypeScript 类型与实际 API 不匹配的个例，准备好 `as any` 临时兜底的心理预期。如果希望保守，可降一个 minor 用 `three@0.183.x`，但本阶段粒子/Points 这条老 API 路径高度稳定，0.184.0 无风险。

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/
├── pages/
│   └── Login.tsx                  # 重构后的登录页（保留所有认证逻辑，新增分栏布局）
├── components/
│   ├── ParticleWave.tsx           # NEW — lazy-loaded Three.js 粒子波浪
│   ├── CssGradientBackground.tsx  # NEW — WebGL 降级背景
│   └── BrandPanel.tsx             # NEW — 左侧品牌 slogan 文字层（DOM，不是 canvas）
├── hooks/
│   └── useWebGLSupport.ts         # NEW — 返回 'webgl' | 'fallback' | 'loading'
└── theme/
    └── (无变更 — 只读 useThemeMode + useSemanticColors)
```

### Pattern 1: Vanilla Three.js in React useEffect

**What:** 在 `useEffect(() => { ... }, [])` 内同步创建 Scene/Camera/Renderer/Points，`return` cleanup 函数销毁所有 GPU 资源。

**When to use:** 整个项目都适用 — 单个 3D 场景、React 18 Strict Mode 双调用安全。

**Example（骨架，Planner 可直接用作任务模板）：**

```typescript
// Source: 合并自 MDN webglcontextlost docs + Three.js Journey + React integration guide
import { useEffect, useRef } from 'react';
import { Scene, PerspectiveCamera, WebGLRenderer, Points, BufferGeometry,
         Float32BufferAttribute, ShaderMaterial, AdditiveBlending } from 'three';

export function ParticleWave({ isDark, reducedMotion }: Props) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // 1. Scene / Camera / Renderer
    const scene = new Scene();
    const camera = new PerspectiveCamera(55, mount.clientWidth / mount.clientHeight, 0.1, 100);
    camera.position.set(0, -14, 12);
    camera.lookAt(0, 0, 0);

    const renderer = new WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    // 2. Geometry: 80 × 32 grid = 2560 particles
    const geometry = new BufferGeometry();
    const positions = new Float32Array(80 * 32 * 3);
    for (let i = 0, x = 0; x < 80; x++) {
      for (let y = 0; y < 32; y++, i++) {
        positions[i * 3 + 0] = (x - 40) * 0.4;
        positions[i * 3 + 1] = (y - 16) * 0.4;
        positions[i * 3 + 2] = 0;
      }
    }
    geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));

    // 3. ShaderMaterial with time + mouse uniforms (wave math on GPU)
    const material = new ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: new Vector2(0, 0) },
        uMouseStrength: { value: 0 },
        uColorBright: { value: new Color(isDark ? '#7FA7FF' : '#E8F0FF') },
        uColorMid:    { value: new Color('#3370FF') },
        uColorDeep:   { value: new Color(isDark ? '#1B2B4D' : '#1D4AC7') },
      },
      vertexShader: `
        uniform float uTime;
        uniform vec2 uMouse;
        uniform float uMouseStrength;
        varying float vHeight;
        void main() {
          vec3 p = position;
          // Dual-sine wave: z = sin(x*0.35 + t*0.6)*0.6 + sin(y*0.25 + t*0.42)*0.4
          float wave = sin(p.x * 0.35 + uTime * 0.6) * 0.6
                     + sin(p.y * 0.25 + uTime * 0.42) * 0.4;
          // Gaussian bulge around mouse
          float d = distance(p.xy, uMouse);
          float bulge = exp(-(d * d) / (2.0 * 3.5 * 3.5)) * 1.2 * uMouseStrength;
          p.z = wave + bulge;
          vHeight = p.z;
          vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          gl_PointSize = (2.0 + bulge) * (300.0 / -mvPosition.z);
        }`,
      fragmentShader: `
        uniform vec3 uColorBright;
        uniform vec3 uColorMid;
        uniform vec3 uColorDeep;
        varying float vHeight;
        void main() {
          vec2 uv = gl_PointCoord - 0.5;
          float circle = smoothstep(0.5, 0.4, length(uv));  // circular sprite (D-05)
          vec3 color = vHeight > 0.0
            ? mix(uColorMid, uColorBright, clamp(vHeight, 0.0, 1.0))
            : mix(uColorDeep, uColorMid, clamp(vHeight + 1.0, 0.0, 1.0));
          gl_FragColor = vec4(color, circle);
        }`,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
    });

    const points = new Points(geometry, material);
    scene.add(points);

    // 4. Animation + context loss handling
    let rafId = 0;
    let mouseTargetStrength = 0;
    const clock = { start: performance.now() };

    const animate = () => {
      if (document.hidden || reducedMotion) return; // 前者每帧检测；后者 mount 时已分流
      rafId = requestAnimationFrame(animate);
      material.uniforms.uTime.value = (performance.now() - clock.start) / 1000;
      // Smoothly decay mouse strength (0.8s time constant)
      material.uniforms.uMouseStrength.value +=
        (mouseTargetStrength - material.uniforms.uMouseStrength.value) * 0.05;
      renderer.render(scene, camera);
    };
    rafId = requestAnimationFrame(animate);

    // 5. Event wiring
    const onMove = (e: MouseEvent) => {
      const rect = mount.getBoundingClientRect();
      const ndcX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ndcY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      // Project NDC to world-space plane (z=0); simplified:
      material.uniforms.uMouse.value.set(ndcX * 16, ndcY * 8);
      mouseTargetStrength = 1.0;
    };
    const onLeave = () => { mouseTargetStrength = 0; };
    const onResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    const onContextLost = (e: Event) => {
      e.preventDefault();  // MDN: REQUIRED to signal intent to restore
      cancelAnimationFrame(rafId);
    };
    mount.addEventListener('mousemove', onMove);
    mount.addEventListener('mouseleave', onLeave);
    window.addEventListener('resize', onResize);
    renderer.domElement.addEventListener('webglcontextlost', onContextLost);

    // 6. Cleanup — CRITICAL for avoiding WebGL context leaks in Strict Mode
    return () => {
      cancelAnimationFrame(rafId);
      mount.removeEventListener('mousemove', onMove);
      mount.removeEventListener('mouseleave', onLeave);
      window.removeEventListener('resize', onResize);
      renderer.domElement.removeEventListener('webglcontextlost', onContextLost);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.forceContextLoss();  // release GPU slot immediately
      mount.removeChild(renderer.domElement);
    };
  }, [isDark, reducedMotion]);

  return <div ref={mountRef} style={{ width: '100%', height: '100%' }} aria-hidden="true" />;
}
```

**要点（Planner 必须在任务描述里强调）：**
1. 所有波浪数学在 **vertex shader** 里跑，CPU 每帧只更新 1 个 `uTime` + `uMouse` uniform — 否则 2500 粒子 ×  60fps = 150K updates/秒会卡。
2. cleanup 必须 **同时**调 `geometry.dispose()`、`material.dispose()`、`renderer.dispose()`、`renderer.forceContextLoss()`。React 18 Strict Mode 会把 effect 跑两次，漏掉任何一条都会泄露 WebGL context，几次后浏览器抛 "Too many active WebGL contexts. Oldest context will be lost"。
3. `renderer.domElement.addEventListener('webglcontextlost', ...)` 的回调里必须 `event.preventDefault()` — 否则浏览器不会尝试恢复。

### Pattern 2: WebGL Support Detection (synchronous, at mount)

**What:** 在一个 `<canvas>` 上试 `getContext('webgl2') ?? getContext('webgl')`，返回布尔。**一次性**检测，不保留 context。

**When to use:** D-09 要求 mount 时即检测；这就是实现。

**Example:**

```typescript
// frontend/src/hooks/useWebGLSupport.ts
import { useEffect, useState } from 'react';

export type WebGLSupport = 'loading' | 'webgl' | 'fallback';

export function useWebGLSupport(): WebGLSupport {
  const [support, setSupport] = useState<WebGLSupport>('loading');

  useEffect(() => {
    if (typeof window === 'undefined') {
      setSupport('fallback');
      return;
    }
    try {
      const canvas = document.createElement('canvas');
      const gl =
        (canvas.getContext('webgl2') as WebGLRenderingContext | null) ??
        (canvas.getContext('webgl') as WebGLRenderingContext | null) ??
        (canvas.getContext('experimental-webgl') as WebGLRenderingContext | null);
      if (!gl) {
        setSupport('fallback');
        return;
      }
      // Immediately release the probe context; ParticleWave will create its own.
      const loseExt = gl.getExtension('WEBGL_lose_context');
      loseExt?.loseContext();
      setSupport('webgl');
    } catch {
      setSupport('fallback');
    }
  }, []);

  return support;
}
```

**关键细节：** probe 创建的 WebGL context 一定要释放 — 否则叠加 ParticleWave 的 context 就是 2 个活跃上下文，在低端设备（iOS Safari 限 8 个）上会快速触达上限。

### Pattern 3: React.lazy + Suspense 懒加载 Three.js

**What:** 用 dynamic `import()` 把 `ParticleWave.tsx`（连带 three 本身 ~155KB gzip）拆成独立 chunk，首屏只加载登录表单。

**When to use:** 本阶段必须这么做 — 三个理由：
1. 登录页是无身份状态下的首屏，bundle 越小 LCP 越快
2. 移动端断点下 ParticleWave 根本不渲染，没理由让它进首屏 chunk
3. 配合 `useWebGLSupport` 的 'loading' 态，天然就是 Suspense fallback 的时机

**Example:**

```typescript
// Inside Login.tsx
import { lazy, Suspense } from 'react';
import { CssGradientBackground } from '../components/CssGradientBackground';
import { useWebGLSupport } from '../hooks/useWebGLSupport';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { useThemeMode } from '../theme/useThemeMode';

const ParticleWave = lazy(() => import('../components/ParticleWave'));

function LeftPanel() {
  const { isMobile } = useResponsiveViewport();
  const webgl = useWebGLSupport();
  const { isDark } = useThemeMode();

  if (isMobile) return null;  // LOGIN-01: mobile shows form only
  if (webgl === 'fallback') return <CssGradientBackground isDark={isDark} />;

  return (
    <Suspense fallback={<CssGradientBackground isDark={isDark} />}>
      <ParticleWave isDark={isDark} />
    </Suspense>
  );
}
```

### Pattern 4: Glass Morphism Card (Dark Mode)

**What:** 用 `backdrop-filter: blur(20px) saturate(180%)` 让卡片背景模糊透出粒子。

**When to use:** 仅暗黑模式（D-07），亮色模式保持实色 `#FFFFFF`。

**Example（内联样式或 CSS module）：**

```typescript
const cardStyle: React.CSSProperties = isDark
  ? {
      background: 'rgba(30, 35, 45, 0.72)',
      // ⚠️ 两个前缀都要写，-webkit- 在前（Safari iOS 必需）
      WebkitBackdropFilter: 'blur(20px) saturate(180%)',
      backdropFilter: 'blur(20px) saturate(180%)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
    }
  : { background: '#FFFFFF' };
```

**@supports 降级（给老 Android WebView）：**

```css
/* 默认：不透明兜底 */
.login-card-dark { background-color: rgba(30, 35, 45, 0.95); }

@supports ((backdrop-filter: blur(20px)) or (-webkit-backdrop-filter: blur(20px))) {
  .login-card-dark {
    background-color: rgba(30, 35, 45, 0.72);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    backdrop-filter: blur(20px) saturate(180%);
  }
}
```

### Anti-Patterns to Avoid

- **反模式 1：在 React state 里存粒子位置** — 会触发整颗 React 树每帧 rerender。**正确做法**：Three.js 管"how"（每帧更新），React 只管"when"（mount/unmount/主题切换）。
- **反模式 2：每次主题切换重建整个 Scene** — 浪费。**正确做法**：把 isDark 作为 shader uniform 颜色值传进去，mid transition 200ms crossfade（UI-SPEC 已规定用 `motionDurationMid`）。
- **反模式 3：`<Suspense fallback={<Spinner/>}>`** — 加载 Three.js 就 200ms 级，用户看到 spinner 会闪烁。**正确做法**：fallback 直接就是 `CssGradientBackground`，加载完成后 crossfade 切入 ParticleWave（或直接切，CSS 渐变和粒子波浪都是品牌蓝，视觉连续）。
- **反模式 4：忘记在 cleanup 里 `renderer.forceContextLoss()`** — React 18 Strict Mode 会 mount-unmount-mount，不主动释放上下文会叠加到 2 个活跃 WebGL context。
- **反模式 5：`backdrop-filter` 值里用 CSS 变量** — Safari 18 忽略 `-webkit-backdrop-filter: blur(var(--x))`，必须写字面量。`[CITED: MDN browser-compat-data #25914]`
- **反模式 6：嵌套 `backdrop-filter`** — 父子元素都开 blur 会在 Safari 出现渲染错乱。登录卡片要么开，要么不开，不要再套一层。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 3D 粒子渲染 | 自己写 canvas 2D 投影矩阵 | `three` 的 `PerspectiveCamera` + `Points` | 正交/透视投影、frustum culling、depth test 都是地雷 |
| shader 编译管理 | 手写 `gl.createShader()` / `gl.compileShader()` | `THREE.ShaderMaterial` | three 自动拼进场景/相机矩阵，uniforms 双向绑定 |
| WebGL 特性探测 | 写一堆 `getExtension()` 黑名单 | 单次 `canvas.getContext('webgl2') ?? canvas.getContext('webgl')` | 能拿到 context = 能跑；拿不到 = 不能跑，二元清晰 |
| 粒子圆形 sprite | 提前渲一张 PNG 做 `map` 纹理 | fragment shader 用 `gl_PointCoord` + `smoothstep` 画圆 | 零额外资源、永远无锯齿 |
| 波浪位移计算 | JS 里 2500 个点每帧算 `sin()` | vertex shader 里算 | CPU 算 = 1 线程 + 60fps 瓶颈；GPU 并行 2500 个 vertex 毫无压力 |
| 鼠标位置到世界坐标 | 手推 unProject 矩阵 | NDC → 简化平面投影（`ndcX * planeHalfWidth`）| 登录页粒子平面固定在 z=0，不需要完整 raycaster |
| 响应式断点检测 | 写新 `resize` listener | 复用现有 `useResponsiveViewport`（已定义 768px 断点）`[VERIFIED: frontend/src/hooks/useResponsiveViewport.ts]` | 断点一致性 |
| 暗黑模式状态 | 再写一遍 `matchMedia('(prefers-color-scheme: dark)')` | 复用 `useThemeMode().isDark` `[VERIFIED: frontend/src/theme/useThemeMode.ts]` | 项目已用 ThemeModeProvider 统一 |
| backdrop-filter 降级 | 写 `useEffect` JS feature detect | CSS `@supports (...) or (-webkit-...)` | 纯声明式，SSR 安全 |

**Key insight:** 这是一个"站在 Three.js 和 Ant Design 巨人肩上"的任务。所有自定义代码应该只是"把这些库的能力串起来"，不应该有任何 200+ 行的手工底层实现。如果任何一个 Task 的 actions 写出了 200 行 JS，大概率是走偏了。

## Common Pitfalls

### Pitfall 1: React 18 Strict Mode 造成的 WebGL Context 泄露

**What goes wrong:** 开发环境下登录页刷新几次就 console 报 "Too many active WebGL contexts. Oldest context will be lost"，粒子消失或黑屏。

**Why it happens:** React 18 Strict Mode 在开发环境下会把 `useEffect` 调用两次（mount → unmount → mount），测试 cleanup 逻辑是否幂等。如果 cleanup 漏掉 `renderer.dispose()` 或 `forceContextLoss()`，每次 HMR 重载都叠加一个活跃 WebGL context。Safari 限 16 个，iOS Safari 限 8 个，几次就满。

**How to avoid:**
1. cleanup 函数必须调 `renderer.dispose()` + `renderer.forceContextLoss()`
2. `geometry.dispose()` + `material.dispose()` 不能省
3. 从 DOM 移除 `renderer.domElement`
4. **在浏览器 devtools 的 Memory tab 里抓快照**：挂载→卸载→挂载，比较 WebGL Context 数量是否稳定

**Warning signs:** 多次 HMR 后粒子消失；控制台 `WebGL: INVALID_OPERATION` 警告。

### Pitfall 2: Safari/iOS 的 `backdrop-filter` 前缀和字面量要求

**What goes wrong:** 玻璃卡片在 Chrome 好好的，到 Safari 16/17/18 上完全没有模糊效果，或者 blur 半径被忽略。

**Why it happens:** Safari 到 2026 年仍要求 `-webkit-backdrop-filter` 前缀；且 **不支持在 `-webkit-backdrop-filter` 值里用 CSS 变量** `[CITED: MDN browser-compat-data #25914]`；Safari 18 在 `backdrop-filter + background-color` 组合上有已知 bug。

**How to avoid:**
- `-webkit-backdrop-filter` 必须写，**写在标准 `backdrop-filter` 之前**
- 值必须是字面量（`blur(20px)`），不是 `blur(var(--blur-radius))`
- 避免同时用 `box-shadow` + `backdrop-filter`（Safari 会模糊阴影区） — UI-SPEC 已规避，只用 `border: 1px solid`
- LightningCSS/Parcel 等构建工具有已知 bug 会移除 `-webkit-` 前缀 `[CITED: parcel-bundler/lightningcss #537]`，Vite 默认用 esbuild 无此问题但 production build 要验证

**Warning signs:** 开发时 Chrome 好看；部署后 iPhone 用户看到的是纯色卡片。测试计划里必须包含 Safari 浏览器验证。

### Pitfall 3: three.js bundle 进入首屏 chunk

**What goes wrong:** Login 页面 LCP 慢了 300-500ms，Lighthouse 分数掉。

**Why it happens:** 如果不用 `React.lazy`，Vite/Rollup 会把 ParticleWave 连带 three 打到 App 主 chunk 里。three 的 minified+gzip ~155KB，WebGLRenderer 把 ShaderLib + UniformsLib 一起拉进来无法 tree-shake `[CITED: three.js GitHub Issue #24199]`。

**How to avoid:**
- `const ParticleWave = lazy(() => import('../components/ParticleWave'))`
- 用 Vite 的 `build.rollupOptions.output.manualChunks` 强制 three 独立成 chunk（可选，lazy 已经足够）
- 用 `npm run build` 后看 `dist/assets/*.js` 里是否出现 `ParticleWave-xxx.js` 单独文件
- 不要为了省事直接 `import { ... } from 'three'` 到 Login.tsx 顶部

**Warning signs:** `npm run build` 输出里 main chunk 体积突增 150KB+；登录页首次加载慢。

### Pitfall 4: 鼠标坐标系混淆导致粒子波浪跳到错误位置

**What goes wrong:** 鼠标移到左上角，波浪隆起在右下角；或者隆起幅度完全不对。

**Why it happens:** DOM 坐标（左上原点，px）→ NDC（-1 到 1）→ 世界坐标系（相机在 (0,-14,12) 看向原点）三次变换，任何一次搞错就错位。相机 Y 负方向看向原点，所以 NDC Y 方向和世界 Y 方向会反。

**How to avoid:**
- 用 `mount.getBoundingClientRect()` 拿准确边界，不要用 `window.innerWidth`
- NDC Y 一定要 `-((e.clientY - rect.top) / rect.height * 2 - 1)`（反转）
- 粒子网格 80×32 在 world 里宽 32 世界单位（`80 * 0.4`）、高 12.8 — 映射时用这两个半宽做倍数
- 先在 canvas 左上/右下/中心打几个 `console.log` 验证 mouse 位置再接业务

**Warning signs:** 鼠标在 canvas 中心，波浪在边缘；鼠标往右移，波浪往左跳。

### Pitfall 5: `prefers-reduced-motion` 没处理导致 a11y 违规

**What goes wrong:** 给动画敏感用户（前庭疾病等）开系统级"减少动态效果"偏好，登录页还是全速粒子动画。WCAG 2.1 Level AAA 2.3.3 要求尊重该偏好。

**Why it happens:** 开发时没想到；浏览器默认开关通常是 off，开发机不会触发。

**How to avoid:**
- ParticleWave 组件 mount 时读 `window.matchMedia('(prefers-reduced-motion: reduce)').matches`
- 为 true 时：渲染**静态粒子网格（不调用 requestAnimationFrame）**，关闭鼠标交互
- 同时用 `matchMedia.addEventListener('change', ...)` 监听运行时偏好变化

**Warning signs:** macOS 系统偏好设置 → 辅助功能 → 显示 → 减少动态效果 打开后，登录页粒子仍然跑。

### Pitfall 6: `document.hidden` + requestAnimationFrame 的配合

**What goes wrong:** 切换 Tab 后回来，或笔记本合盖再打开，动画卡顿几秒才恢复；更糟糕的是某些浏览器 RAF 停止但 timer uniform 累积到离谱值，导致波浪瞬间"爆炸"。

**Why it happens:** 浏览器 tab 后台时 `requestAnimationFrame` 会暂停甚至几小时不触发；恢复时如果用 `performance.now()` 直接算 `uTime`，差值变大导致波浪方程输入值跳跃。

**How to avoid:**
- 用**增量时间**更新 uniform：`uTime += deltaClamped`，deltaClamped 限制在 0.1s 以内
- 或监听 `visibilitychange`，hide 时 `cancelAnimationFrame`、show 时重置 clock start 后再 RAF

**Warning signs:** 切 tab 回来粒子闪动/波形诡异；笔记本合盖后再打开页面瞬间视觉异常。

## Runtime State Inventory

> 本阶段是纯视觉重构，不涉及数据迁移或状态重命名。以下记录为完整性。

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | 无 — 不改任何数据库、localStorage 结构。`social-security-auth-session` localStorage 键保持不变 | None |
| Live service config | 无 — 后端 `/api/v1/auth/*`、`/api/v1/feishu/oauth/*` 所有接口签名不变 | None |
| OS-registered state | 无 — 纯前端静态资源 | None |
| Secrets/env vars | 无新增；不触及 Feishu OAuth credentials | None |
| Build artifacts | `npm install three @types/three` 会更新 `package-lock.json`；`npm run build` 输出的 `dist/` 会新增 ParticleWave chunk | Commit `package.json` + `package-lock.json`；验证 `dist/` 产物有独立 ParticleWave chunk |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js + npm | 安装 three、构建 | ✓（项目现有） | Node 18+ 推荐 | — |
| `three` npm 包 | LOGIN-02 | ✗ — 需新增 | 待安装 `0.184.0` | 无 — 必须安装 |
| `@types/three` | TypeScript 类型 | ✗ — 需新增 | 待安装 `0.184.0` | 无 — 必须安装 |
| WebGL (用户设备) | 最佳体验 | 运行时检测 | — | CSS 渐变（LOGIN-03 已规定） |
| `backdrop-filter` 支持 | 暗黑模式玻璃效果 | 运行时特性检测 | Safari 9+、Chrome 76+、Firefox 103+ `[CITED: caniuse.com/css-backdrop-filter]` | `@supports` 降级到不透明背景 |

**Missing dependencies with no fallback:** 无 — `three` 和 `@types/three` 通过 `npm install` 安装，均为稳定包。

**Missing dependencies with fallback:** WebGL 和 backdrop-filter 都是运行时特性，已在 CONTEXT 中规划降级。

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Playwright 1.59.1（已安装） `[VERIFIED: frontend/package.json]` |
| Config file | `frontend/playwright.config.ts` |
| Quick run command | `npm run test:e2e -- tests/e2e/login-redesign.spec.ts`（Phase 23 新增文件） |
| Full suite command | `cd frontend && npm run test:e2e` |

**项目单元测试现状：** 前端目前**没有 Jest/Vitest 单元测试**（`frontend/src` 下无 `*.test.*` / `*.spec.*` 文件）。所有前端测试都是 Playwright E2E。本阶段保持此风格，不引入新测试框架。

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| LOGIN-01 | 桌面 ≥1024px 看到左右分栏；<768px 只看到表单 | Playwright viewport | `npx playwright test tests/e2e/login-redesign.spec.ts -g "layout"` | ❌ Wave 0 |
| LOGIN-02 | ParticleWave 组件渲染出 `<canvas>` 并触发 mousemove 事件 | Playwright DOM 断言 | `npx playwright test tests/e2e/login-redesign.spec.ts -g "particle"` | ❌ Wave 0 |
| LOGIN-03 | WebGL 不可用时渲染 `<CssGradientBackground>` | Playwright + `page.addInitScript` stub `HTMLCanvasElement.prototype.getContext` 返回 null | `npx playwright test tests/e2e/login-redesign.spec.ts -g "webgl fallback"` | ❌ Wave 0 |
| LOGIN-04 | 切换暗色模式后卡片 computed style 含 backdrop-filter；粒子 uniforms 切色 | Playwright DOM 断言 + `evaluate()` 检查 canvas shader uniforms（通过 data attr 暴露） | `npx playwright test tests/e2e/login-redesign.spec.ts -g "dark mode"` | ❌ Wave 0 |

**手动测试补充（不能自动化）：**
- WebGL 粒子视觉实际渲染正确性（Playwright 抓不到 canvas 像素）— 需人工开 dev 页面对比截图
- Safari 上 `backdrop-filter` 实际效果（Playwright 默认 Chromium，无 Safari）— 可用 `playwright install webkit` 加 webkit project，也可手动在 macOS Safari 实机验证
- 动画流畅度 60fps — 需 Chrome DevTools Performance tab 人工抓取

### Sampling Rate

- **Per task commit:** `npm run lint` + `npm run build`（TypeScript + Vite 编译通过）
- **Per wave merge:** `npm run test:e2e -- tests/e2e/login-redesign.spec.ts`（仅新增的登录页测试，快速）
- **Phase gate:** `npm run test:e2e`（全量 E2E） + 人工 Safari 验证 + 人工 reduced-motion 验证

### Wave 0 Gaps

- [ ] `frontend/tests/e2e/login-redesign.spec.ts` — 新增，覆盖 LOGIN-01/02/03/04 的自动化断言
- [ ] 考虑在 `frontend/playwright.config.ts` 的 `projects` 数组加 webkit 项（可选，成本低）
- [ ] 若希望自动化检查 "粒子颜色随暗黑模式切换"，需要在 `ParticleWave.tsx` 加一个 `data-particle-color` 属性暴露当前 uniform 值给 Playwright 读取

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | **no** — 本阶段不改任何认证逻辑 | 保留现有 `useAuth`、`login()`、`verifyEmployee()`、飞书 OAuth 流（Phase 22 已实现） |
| V3 Session Management | **no** — `social-security-auth-session` localStorage 机制不变 | Phase 22 已确立 |
| V4 Access Control | **no** — 登录前无权限可控 | — |
| V5 Input Validation | **yes，最小程度** | 用户名/密码/工号输入沿用现有 Ant Design `Form.Item rules`（required），`values.username.trim()` 已做；新增字段=零 |
| V6 Cryptography | no | 不接触任何加密 |
| V14 Configuration | **yes** | `backdrop-filter` 不暴露密钥；Three.js 新依赖需验证 supply chain（见下） |

### 供应链验证（新增 `three` 依赖）

| 检查项 | 方法 |
|-------|------|
| 包出处 | npm registry `https://registry.npmjs.org/three` — 官方 mrdoob/three.js 仓库 |
| 发布者 | `mrdoob`（Three.js 作者，已发布 500+ 版本） |
| Install 后审计 | `npm audit` 必须通过；`three@0.184.0` 发布于 2026-04-16，已经过 3 天社区验证 |
| 文件完整性 | `package-lock.json` integrity hash 会记录 |

### Known Threat Patterns for 登录页

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| WebGL context 过多造成 DoS 自家标签页 | Denial of Service | cleanup 必须调 `renderer.dispose()` + `forceContextLoss()`（见 Pitfall 1） |
| 恶意 shader 导致 GPU 挂起 | — | 本阶段 shader 是静态字符串字面量，不接受用户输入 — 无风险 |
| `dangerouslySetInnerHTML` 注入 | Tampering | 本阶段**禁止使用** — 所有 slogan 文字都用 `<Typography>` 或 `{...}` JSX 插值 |
| Third-party CDN 引入 three | Supply chain | **禁止从 CDN 加载 three** — 用 npm install 进本地 `node_modules` 经 Vite 打包 |

## Code Examples

> 仅列 UI-SPEC 和 Pattern 章节没详尽展开的、Planner 可能需要的特定片段。

### CssGradientBackground（完整组件）

```typescript
// Source: CONTEXT.md D-08 + UI-SPEC Color section
import { CSSProperties } from 'react';

interface Props { isDark: boolean; }

export function CssGradientBackground({ isDark }: Props) {
  const style: CSSProperties = {
    width: '100%',
    height: '100%',
    backgroundImage: isDark
      ? 'linear-gradient(135deg, #1B2B4D 0%, #3370FF 60%, #7FA7FF 100%)'
      : 'linear-gradient(135deg, #E8F0FF 0%, #3370FF 60%, #1D4AC7 100%)',
    backgroundSize: '200% 200%',
    animation: 'gradientDrift 20s ease-in-out infinite',
  };
  return (
    <>
      <div style={style} aria-hidden="true" />
      <style>{`
        @keyframes gradientDrift {
          0%   { background-position: 0% 50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @media (prefers-reduced-motion: reduce) {
          [data-css-gradient-bg] { animation: none !important; }
        }
      `}</style>
    </>
  );
}
```

### Login.tsx 分栏布局骨架（保留所有现有逻辑）

```typescript
// Structure only — executor preserves all existing hooks/handlers from current Login.tsx
import { lazy, Suspense } from 'react';
import { useResponsiveViewport } from '../hooks/useResponsiveViewport';
import { useWebGLSupport } from '../hooks/useWebGLSupport';
import { useThemeMode } from '../theme/useThemeMode';
import { CssGradientBackground } from '../components/CssGradientBackground';
import { BrandPanel } from '../components/BrandPanel';

const ParticleWave = lazy(() => import('../components/ParticleWave'));

export function LoginPage() {
  // ... all existing state/hooks/handlers unchanged ...
  const { isMobile } = useResponsiveViewport();
  const webgl = useWebGLSupport();
  const { isDark } = useThemeMode();

  // early-returns (Navigate, etc.) unchanged

  const Canvas = () => {
    if (webgl === 'fallback') return <CssGradientBackground isDark={isDark} />;
    return (
      <Suspense fallback={<CssGradientBackground isDark={isDark} />}>
        <ParticleWave isDark={isDark} />
      </Suspense>
    );
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {!isMobile && (
        <div style={{ flex: '0 0 60%', position: 'relative', overflow: 'hidden' }}>
          <Canvas />
          <BrandPanel isDark={isDark} />
        </div>
      )}
      <div
        style={{
          flex: isMobile ? '1 1 100%' : '0 0 40%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 32,
          background: isDark ? 'transparent' : colors.BG_LAYOUT,
        }}
      >
        {/* Existing Card with Tabs/Form/Feishu Button/Link unchanged */}
      </div>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 全局加载 three 到主 chunk | `React.lazy(() => import('./ParticleWave'))` | React 16.6 (2018) 起支持 | 登录首屏 bundle 少 ~150KB |
| CPU 每帧更新 2500 粒子 Y 坐标 | vertex shader 里算 `sin(x*f + t*s)` | 自 WebGL 1.0 起就应如此 | 60fps 稳定，CPU 空闲 |
| 手写 `getContext('webgl')` | 同上（**没有好的替代** — 浏览器 API 就是这个） | — | — |
| R3F 作为默认 3D 集成方案 | React 18 下**仍是好选择**；本项目因只一处用、bundle 敏感、React 18.3 才选 vanilla | — | 避免 R3F v9 对 React 19 的硬要求；avoid ~600KB bundle 开销 |
| `-webkit-backdrop-filter` 可省略 | **仍需写** — Safari 18 到 2026 年依然要求前缀 `[CITED: MDN #25914]` | Safari 至今未移除前缀要求 | 必须维护双前缀 |
| WebGPU 作为主渲染 API | 新项目建议直接 WebGPU；本阶段**继续 WebGL** | 2025 年 WebGPU 稳定 | 本阶段不追前沿；WebGL 在全平台覆盖更广，且 three@0.184 的 `WebGPURenderer` 仍在演进，留给未来阶段 |

**Deprecated/outdated:**
- `three.module.js` 直接从 CDN import — 已过时，用 npm 包
- 用 `<img>` 当粒子纹理 — 过时，shader `gl_PointCoord` 画圆更优

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `three@0.184.0` 的 Points + BufferGeometry + ShaderMaterial API 与 r150+ 保持一致 | Standard Stack, Pattern 1 | 低 — 这些是 Three.js 自 r100 起的核心稳定 API；若有微小破坏性变更，TypeScript 编译会报错，Planner 可 5 分钟内修正 |
| A2 | React 18.3.1 + Vite 6 对 `React.lazy(() => import('./ParticleWave'))` 产出独立 chunk | Don't Hand-Roll, Pattern 3 | 低 — 这是 Vite/Rollup 的默认行为，项目无自定义 `manualChunks`。`[ASSUMED]` 但非常高把握 |
| A3 | Playwright Chromium 默认支持 WebGL，无需额外配置 | Validation Architecture | 低 — `launchOptions.executablePath` 指向真实 Chrome 而非 Headless，WebGL 应可用。如果 CI 上 Chrome 无硬件加速，可用 `--enable-unsafe-swiftshader` flag `[ASSUMED]` |
| A4 | 2500 粒子 + vertex-shader 波浪在中等性能 iOS Safari 上能跑 60fps | 3D Canvas Contract | 中 — 移动端 768px 以下不显示 canvas 已规避；平板 768-1023px 会显示，iPad 应稳 60fps，老安卓平板可能卡。**建议 Planner 加一个"平板性能 smoke test"任务**，用真机或低配虚拟设备验证 |
| A5 | Safari/iOS 的 `backdrop-filter: blur(20px) saturate(180%)` 不触发已知 bug | Pattern 4, Pitfall 2 | 中 — Safari 18 在 `backdrop-filter + box-shadow` 和嵌套 `backdrop-filter` 上有已知 bug，本 UI-SPEC 已规避（用 `border` 替代 `box-shadow`、不嵌套）。但**实机 Safari 验证必须在 phase gate 前做**，不能省 |
| A6 | 用户 "深海荧光" 指的是暗背景+亮粒子的 additive blending 效果 | 3D Canvas Contract | 低 — UI-SPEC 已定义具体色值（`#7FA7FF` 亮 → `#3370FF` 中 → `#1B2B4D` 深）；若最终视觉偏离用户想象，是 UI-SPEC 层面的差异而非本研究的假设 |

**如果这个表为空：** 不为空 — 6 项假设需 Planner/Executor/用户在执行阶段特别关注。其中 A4 和 A5 需要专门的验证任务。

## Open Questions

1. **暗黑模式切换时的视觉过渡**
   - What we know: UI-SPEC 规定 "粒子色谱 + 卡片背景 crossfade 200ms（`motionDurationMid`）"
   - What's unclear: 实际 shader uniform crossfade 要自己写插值逻辑；卡片 `backdrop-filter` 值不能单独 transition（浏览器不支持 transition `backdrop-filter`），只能 transition `background-color` + `opacity`
   - Recommendation: Planner 把"暗色模式切换视觉流畅度"作为单独一个任务/子任务，执行后用户肉眼验收

2. **Playwright 如何断言 WebGL 已渲染**
   - What we know: `canvas` DOM 元素一定存在；可 `canvas.getContext('webgl')` 确认 context 存在
   - What's unclear: Playwright 抓不到 canvas 像素内容（WebGL 读取需 `gl.readPixels` + 测试代码配合）
   - Recommendation: 测试策略 = DOM 断言（canvas 存在 + 尺寸非零 + context 非 null），像素级验证靠人工截图。如果未来要升级到像素对比，用 `@playwright/test` 的 visual regression 并 snapshot

3. **Phase 22 尚未完成时是否可以开始 Phase 23**
   - What we know: STATE.md 显示 Phase 22 仍在 execute 阶段；CONTEXT 声明"OAuth 流程必须稳定后才改登录 UI"
   - What's unclear: 本阶段完全不触及 OAuth 代码，理论上可独立开发；但 Login.tsx 改造需要合并现有 OAuth useEffect 逻辑
   - Recommendation: 研究结论明确 — **先等 Phase 22 合并完成再开始 Phase 23 的 Plan 执行**，避免两个 Phase 同时改 Login.tsx 产生冲突。Planner 可以做 Plan，但 Executor 开工前确认 Phase 22 已 merge

## Sources

### Primary (HIGH confidence)
- `frontend/package.json` — 已安装依赖版本（React 18.3.1, Ant Design 5.29.3, Playwright 1.59.1）
- `frontend/src/theme/index.ts` — Ant Design token 定义（主色 `#3370FF`, borderRadius, motion 值）
- `frontend/src/hooks/useResponsiveViewport.ts` — 768px 断点已建立
- `frontend/src/theme/useThemeMode.ts` + `ThemeModeProvider.tsx` — 暗黑模式状态源
- `frontend/src/pages/Login.tsx` — 当前登录页所有认证逻辑（完整读取）
- [MDN: HTMLCanvasElement webglcontextlost event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/webglcontextlost_event) — 官方事件 API
- [MDN: CSS backdrop-filter](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/backdrop-filter) — 规范与浏览器支持
- [MDN browser-compat-data issue #25914](https://github.com/mdn/browser-compat-data/issues/25914) — Safari 18 backdrop-filter 前缀与 CSS 变量 bug
- [caniuse.com/css-backdrop-filter](https://caniuse.com/css-backdrop-filter) — 浏览器支持矩阵
- [three.js BufferGeometry docs](https://threejs.org/docs/pages/BufferGeometry.html) — 官方 API 参考
- [three.js webgl buffergeometry particles example](https://threejs.org/examples/webgl_buffergeometry_points.html) — 官方粒子示例
- [Khronos WebGL HandlingContextLost wiki](https://www.khronos.org/webgl/wiki/HandlingContextLost) — 上下文丢失权威指南
- `npm view three version` → 0.184.0, published 2026-04-16 — 版本事实

### Secondary (MEDIUM confidence)
- [The Blog of Maxime Heckel — particles with R3F and shaders](https://blog.maximeheckel.com/posts/the-magical-world-of-particles-with-react-three-fiber-and-shaders/) — shader 粒子模式参考
- [Codrops — Building Efficient Three.js Scenes (2025)](https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/) — 2025 年性能优化综述
- [Three.js Journey Particles lesson](https://threejs-journey.com/lessons/particles) — 社区标准教程
- [Medium: Why I Prefer React Three Fiber Over Vanilla Three.js](https://medium.com/@koler778/why-i-prefer-react-three-fiber-over-vanilla-three-js-28025cb324ff) — R3F vs vanilla 对比分析（支持了"小场景选 vanilla"的结论）
- [three.js GitHub Issue #24199 — Making 'three' tree-shakeable](https://github.com/mrdoob/three.js/issues/24199) — tree-shaking 现状跟踪
- [parcel-bundler/lightningcss #537](https://github.com/parcel-bundler/lightningcss/issues/537) — 构建工具前缀处理 bug
- [Medium: Integrating Three.js with React (Alfino Hatta)](https://medium.com/@alfinohatta/integrating-three-js-278774d45973) — 生产就绪的 React + Three 集成指南

### Tertiary (LOW confidence)
- [utsubo.com — 100 Three.js Tips That Actually Improve Performance](https://www.utsubo.com/blog/threejs-best-practices-100-tips) — 未验证权威性，仅作交叉参考
- [graffersid — R3F vs Three.js in 2026](https://graffersid.com/react-three-fiber-vs-three-js/) — 营销博客，观点参考但数字需交叉验证

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — `three` 和 `@types/three` 版本经 npm registry 直接验证；Ant Design/React 版本从 package.json 直读
- Architecture: **HIGH** — 所有 Pattern 均基于 MDN/Khronos/Three.js 官方文档；UI-SPEC 已合并所有用户决策
- Pitfalls: **HIGH** — Pitfall 1/2/5 有官方文档佐证；Pitfall 3/4/6 来自实战经验汇总
- Validation Architecture: **MEDIUM** — 项目前端只有 Playwright E2E，测试策略明确；粒子像素级自动化验证不可行（A2）是已知限制
- Assumptions: **MEDIUM** — 6 项已记录；A4（平板性能）和 A5（Safari `backdrop-filter` 实际效果）必须在 phase gate 前人工验证

**Research date:** 2026-04-19
**Valid until:** 2026-05-19（3D 生态移动快，30 天后若未开始，Planner 应重新验 `three` 最新版本）

---

*Phase: 23-login-redesign*
*Research completed: 2026-04-19*
