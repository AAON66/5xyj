# Phase 14: 样式 Token 化与暗黑模式 - Research

**Researched:** 2026-04-05
**Domain:** Frontend theming (Ant Design 5 主题系统 + 暗黑模式)
**Confidence:** HIGH

## Summary

本阶段目标是消除前端 33+ 处硬编码内联颜色（分布在 20+ 文件），替换为 AntD 5 主题 token，并引入暗黑模式切换。技术风险低：AntD 5.29.3 原生提供 `theme.darkAlgorithm`、`theme.useToken()` hook 和 CSS variables 模式，可直接用于实现瞬间切换和消除 FOUC。项目已存在完整 `theme/index.ts` 配置文件，现有 `ConfigProvider` 在 `main.tsx` 单层包裹，扩展为动态主题无结构性障碍。

最大复杂度来源：（1）硬编码色不是只在 `style={{}}` 内联，而是分布在 Table columns render 函数、valueStyle、borderColor、background 等多种位置；（2）部分颜色使用 React hook 形式获取（`useSemanticColors`）在 Table columns 定义顶层无法调用，需要双轨接口（hook + 纯函数）；（3）发现 **`frontend/src/styles.css` (3520 行，含 200+ 硬编码颜色) 是死代码**（全项目零 import），但仍物理存在，可能误导未来维护者；（4）Sider 刻意保持深色是飞书风格产品特征，不能在暗模下与内容区混同。

**Primary recommendation:** 使用 `ConfigProvider` + `theme.darkAlgorithm` + `localStorage` + `<html data-theme>` 同步脚本方案。新建 `frontend/src/theme/useSemanticColors.ts` hook（消费 `theme.useToken()`）、`frontend/src/theme/chartColors.ts` 纯函数（供 Table columns 使用）、`frontend/src/theme/ThemeModeProvider.tsx` Context（管理 mode state + localStorage 持久化）。按页面逐一迁移 33 个位置，全程保留 Sider 深色 + 飞书蓝品牌色不变。

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Token 替换策略：**
- D-01: 建立语义色常量模块 `frontend/src/theme/semanticColors.ts`，导出 { BRAND, SUCCESS, ERROR, WARNING, TEXT_TERTIARY, HIGHLIGHT_BG } 等语义名。内部通过 AntD token 提供动态值
- D-02: 主接口为 `useSemanticColors()` hook：在组件内调用 `theme.useToken()` 后返回语义色对象，暗模切换时自动重渲染
- D-03: Table columns 等组件外的定义位置使用独立的 `chartColors.ts` 模块（常量导出 + `getChartColors(isDark)` 函数版本），防止 hook 限制
- D-04: AntD 内置 token 能直接映射的不新建语义色：`#999` → `colorTextTertiary`，`#fafafa/#f5f5f5` → `colorFillQuaternary`，`#F0F5FF` → `colorPrimaryBg`
- D-05: 无对应 AntD token 的自定义色（如 `#FFF7E6` 黄色高亮背景）归为语义色常量 `HIGHLIGHT_BG`，内部映射为 `colorWarningBg`
- D-06: Card 状态边框色封装为独立 hook `useCardStatusColors()`，返回 { successBorder, errorBorder, warningBorder }
- D-07: 跨期对比差异高亮色直接复用 useSemanticColors：增加=WARNING，减少=ERROR，新增=BRAND

**暗黑模式切换：**
- D-08: 切换按钮放在 MainLayout Header 右上角用户菜单旁，太阳/月亮图标
- D-09: 初次加载默认跟随系统偏好（`matchMedia('(prefers-color-scheme: dark)')`）
- D-10: 用户手动切换后持久化到 localStorage，覆盖系统偏好
- D-11: 瞬间切换，不加过渡动画
- D-12: localStorage 键名 `theme-mode`，值 `'light' | 'dark'`
- D-13: 在 `index.html <head>` 插入同步脚本，React 启动前给 `<html>` 加 `data-theme` 属性防 FOUC

**暗黑模式下的品牌色：**
- D-14: 使用 AntD `theme.darkAlgorithm` 自动计算暗模版本主色
- D-15: 语义色（success/warning/error）暗模下交由 darkAlgorithm 自动适配
- D-16: `Layout.Sider` 始终保持深色（`#1F2329`），亮暗统一，飞书风格标志性特征
- D-17: Alert 组件暗模背景采用 AntD darkAlgorithm 默认深色半透明样式
- D-18: Table hover 效果暗模下交由 darkAlgorithm 自动计算

**自定义组件暗模支持：**
- D-19: Login 页面 `#F5F6F7` 背景改为 `useSemanticColors().colorBgLayout`
- D-20: FeishuFieldMapping 页面所有硬编码色全部 token 化
- D-21: Workspace/Portal 页面 `#3370FF` 图标色改为 `useSemanticColors().BRAND`

### Claude's Discretion

- useSemanticColors hook 返回对象的具体字段命名
- chartColors 模块的具体导出接口
- useCardStatusColors hook 的实现细节
- index.html FOUC 脚本的具体代码
- 切换按钮的图标选型（@ant-design/icons 中的 SunOutlined/MoonOutlined 或自绘）
- 主题切换后保留的某些遗留色（如 Sider 深色的精细调优）

### Deferred Ideas (OUT OF SCOPE)

- 用户可自定义主题色（未来独立 phase）
- 跟随系统偏好的实时响应（系统切换时 app 跟随）
- 更细粒度的颜色偏好（如对比度调节）

## Project Constraints (from CLAUDE.md)

本项目为社保表格聚合工具，以下 CLAUDE.md 约束影响本阶段：

- **前端 UI 框架锁定：** React + Ant Design（禁止引入其他 UI 库）
- **前端负责展示层：** 上传、看板、识别结果展示、异常提示、导出入口
- **测试要求：** lint 通过 + build 成功为 mandatory
- **命令：** `npm run lint`、`npm run build`、`npm run dev`

本阶段不涉及后端、解析、工号匹配、双模板导出链路，CLAUDE.md 中的数据处理规则不适用。

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UX-01 | 内联样式 token 化（将硬编码颜色替换为 Ant Design 主题 token） | 本文档 "Hardcoded Color Audit"、"Token Mapping Table" 章节提供完整替换映射 |
| UX-02 | 用户可切换暗黑模式，偏好持久化到 localStorage | 本文档 "Dark Mode Toggle Architecture"、"FOUC Prevention" 章节提供完整实现方案 |

## Standard Stack

### Core（已装，无需新增）

| Library | Version (安装) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| antd | 5.29.3 (最新 5.x 为 6.3.5，但项目在 5.x) | 主题系统 + ConfigProvider + theme tokens | 已锁定 v5 [VERIFIED: frontend/package.json] |
| @ant-design/icons | 5.6.1 | SunOutlined / MoonOutlined 切换图标 | 已装 [VERIFIED: package.json] |
| react | 18.3.1 | Context API + hooks | 已装 [VERIFIED: package.json] |

**零新依赖策略：** 本阶段不引入任何新 npm 包。AntD 5 原生支持 darkAlgorithm 和 useToken [VERIFIED: Ant Design 5 docs via training + antd 5.x default API].

**版本确认：** [VERIFIED: npm view antd version 执行于 2026-04-05] latest antd 6.3.5；项目在 5.29.3。5.x 与 6.x 主题 API 向后兼容。

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AntD darkAlgorithm | 手写 dark token 对象 | 工作量 10x，自动语义色适配效果更差 |
| React Context | Zustand/Redux | 过度工程化，单一 mode state 无需引入新库 |
| CSS-in-JS 内联 | CSS variables | AntD 5 已默认内部使用 CSS variables，无需另建 |
| `data-theme` HTML 属性 | class="dark" | `data-*` 更语义化，FOUC 脚本更清晰；但两者都能工作 |

## Architecture Patterns

### Recommended File Structure

```
frontend/src/theme/
├── index.ts                    # 现有 — 保持，改造为 buildTheme(mode) 函数
├── semanticColors.ts           # 新增 — 非 hook 语义色常量（字符串占位符/默认值）
├── useSemanticColors.ts        # 新增 — hook 版本，消费 theme.useToken()
├── useCardStatusColors.ts      # 新增 — Card 状态边框专用
├── chartColors.ts              # 新增 — 纯函数 getChartColors(isDark)
├── ThemeModeProvider.tsx       # 新增 — Context + localStorage + system preference
├── useThemeMode.ts             # 新增 — 消费 ThemeModeContext 的 hook
└── animations.module.css       # 现有

frontend/index.html             # 新增 FOUC 脚本
frontend/src/main.tsx           # 改造 — 用 ThemeModeProvider 包裹 ConfigProvider
frontend/src/layouts/MainLayout.tsx  # 改造 — Header 加切换按钮
```

### Pattern 1: ConfigProvider + darkAlgorithm

**What:** AntD 5 通过 `theme.algorithm` 字段选择 light/dark 算法，在运行时切换即可整站变色。

**When to use:** 任何需要主题切换的 AntD 5 应用。

**Example:**
```tsx
// Source: Ant Design 5 official API [CITED: ant.design/docs/react/customize-theme]
import { ConfigProvider, theme as antdTheme } from 'antd';
import type { ThemeConfig } from 'antd';

const buildTheme = (mode: 'light' | 'dark'): ThemeConfig => ({
  algorithm: mode === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
  token: {
    colorPrimary: '#3370FF',
    // ...其余项目 token
  },
  components: {
    Layout: {
      siderBg: '#1F2329',  // D-16: 两种模式统一保持深色
      // ...
    },
  },
});

<ConfigProvider theme={buildTheme(mode)} componentSize="small" locale={zhCN}>
  {children}
</ConfigProvider>
```

### Pattern 2: theme.useToken() 消费 token

**What:** `useToken()` hook 返回当前生效的 token 对象，ConfigProvider 切换 algorithm 后自动重新计算并触发消费组件重渲染。

**When to use:** 组件内部需要读取主题色值用于内联 style 或计算。

**Example:**
```tsx
// Source: Ant Design 5 official API [CITED: ant.design/docs/react/customize-theme#theme.useToken]
import { theme } from 'antd';

export function useSemanticColors() {
  const { token } = theme.useToken();
  return {
    BRAND: token.colorPrimary,
    SUCCESS: token.colorSuccess,
    ERROR: token.colorError,
    WARNING: token.colorWarning,
    TEXT_TERTIARY: token.colorTextTertiary,
    HIGHLIGHT_BG: token.colorWarningBg,       // D-05
    HIGHLIGHT_BG_PRIMARY: token.colorPrimaryBg,
    HIGHLIGHT_BG_ERROR: token.colorErrorBg,
    BG_CONTAINER: token.colorBgContainer,
    BG_LAYOUT: token.colorBgLayout,
  };
}
```

**CRITICAL LIMITATION:** `useToken()` 必须在 `ConfigProvider` 子树内调用（React hooks 规则 + Context 可见性）[VERIFIED: React Rules of Hooks + AntD Context pattern]. 本项目 `ConfigProvider` 在 `main.tsx` 顶层，全部组件都在其下，满足条件。

### Pattern 3: 非-hook 纯函数（for Table columns）

**What:** Table columns 数组常定义在组件顶层、模块级，或 render 回调内，不能直接调用 hook。

**When to use:** `AnomalyDetection.tsx` 的 STATUS_STYLES 映射、`FeishuSync.tsx` 顶层 `STATUS_COLORS` 常量、Table columns 的 render 函数需要颜色。

**Example:**
```tsx
// frontend/src/theme/chartColors.ts
export interface ChartColors {
  brand: string;
  success: string;
  error: string;
  warning: string;
  textTertiary: string;
  highlightBg: string;
}

// 固定值（亮模），作为 fallback 和 lint-友好的常量
export const LIGHT_CHART_COLORS: ChartColors = {
  brand: '#3370FF',
  success: '#00B42A',
  error: '#F54A45',
  warning: '#FF7D00',
  textTertiary: '#8F959E',
  highlightBg: '#FFF7E6',
};

export const DARK_CHART_COLORS: ChartColors = {
  // darkAlgorithm 自动计算结果的近似值，从 AntD 5 dark seed token 生成
  brand: '#3C89E8',
  success: '#49AA19',
  error: '#DC4446',
  warning: '#D89614',
  textTertiary: '#7D8390',
  highlightBg: '#2B2111',
};

export function getChartColors(isDark: boolean): ChartColors {
  return isDark ? DARK_CHART_COLORS : LIGHT_CHART_COLORS;
}
```

**用法：** 在组件内先 `const { isDark } = useThemeMode(); const colors = getChartColors(isDark);`，然后在组件内部定义 columns（依赖 colors），或把 colors 传给 render 闭包。

### Pattern 4: localStorage + 系统偏好 + FOUC 预防

**What:** 初始 mode 决策顺序 = localStorage > matchMedia('(prefers-color-scheme: dark)') > 默认 'light'。

**Why FOUC matters:** 如果 React 渲染时才读 localStorage，首屏会先显示亮模（AntD 默认）然后闪烁切换到暗模。解决办法：`<head>` 同步脚本在 React 启动前给 `<html>` 加 `data-theme="dark"`，配合 CSS 强制背景色覆盖 AntD 默认。

**Example:**
```html
<!-- frontend/index.html — 插入到 <head> 底部，<script type="module"> 之前 -->
<script>
  (function() {
    try {
      var saved = localStorage.getItem('theme-mode');
      var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      var mode = saved || (prefersDark ? 'dark' : 'light');
      document.documentElement.setAttribute('data-theme', mode);
      if (mode === 'dark') {
        document.documentElement.style.backgroundColor = '#141414';
        document.body && (document.body.style.backgroundColor = '#141414');
      }
    } catch(e) {}
  })();
</script>
```

**React 端同步：** `ThemeModeProvider` 读取 `<html data-theme>` 作为初始值，state 变更时写回 `data-theme` 和 localStorage。

### Pattern 5: ThemeModeProvider（Context）

```tsx
// frontend/src/theme/ThemeModeProvider.tsx
import { createContext, useState, useCallback, useMemo, useEffect, type PropsWithChildren } from 'react';

type ThemeMode = 'light' | 'dark';
interface ThemeModeContextValue {
  mode: ThemeMode;
  isDark: boolean;
  toggleMode: () => void;
  setMode: (m: ThemeMode) => void;
}

export const ThemeModeContext = createContext<ThemeModeContextValue | null>(null);

const STORAGE_KEY = 'theme-mode';

function readInitialMode(): ThemeMode {
  if (typeof window === 'undefined') return 'light';
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === 'light' || saved === 'dark') return saved;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function ThemeModeProvider({ children }: PropsWithChildren) {
  const [mode, setModeState] = useState<ThemeMode>(readInitialMode);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode);
    try { localStorage.setItem(STORAGE_KEY, mode); } catch {}
  }, [mode]);

  const setMode = useCallback((m: ThemeMode) => setModeState(m), []);
  const toggleMode = useCallback(() => setModeState(m => m === 'light' ? 'dark' : 'light'), []);
  const value = useMemo(() => ({ mode, isDark: mode === 'dark', toggleMode, setMode }), [mode, toggleMode, setMode]);

  return <ThemeModeContext.Provider value={value}>{children}</ThemeModeContext.Provider>;
}
```

### Anti-Patterns to Avoid

- **直接改 `theme/index.ts` 为 dark-only：** 破坏亮模。正确做法是导出 `buildTheme(mode)` 函数。
- **在 ConfigProvider 外部调用 `theme.useToken()`：** 返回默认（非定制）token，颜色不跟随切换 [VERIFIED: AntD 5 useToken 依赖 Context].
- **忘记 localStorage try/catch：** Safari 隐私模式下 localStorage 抛错导致 React 崩溃。
- **用 CSS `transition: background-color 0.3s`：** D-11 明确要求瞬间切换。
- **把 `#3370FF` 写死到 `semanticColors.ts` 常量：** 常量文件应该是占位符/fallback，动态值从 `useSemanticColors` hook 获取。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 暗模色值生成 | 手写 `darkTokens` 对象 | `theme.darkAlgorithm` | 50+ token 的语义一致性计算，AntD 已精调 |
| 主题切换重渲染 | 手动 force update 或 EventEmitter | ConfigProvider Context | React 自动 Context 级重渲染，useToken 自动订阅 |
| Table rowHoverBg 暗模适配 | 手写暗模 hover 色 | darkAlgorithm 自动计算 | D-18 已决策 |
| Alert 暗模背景 | 手写暗模半透明 | darkAlgorithm 默认样式 | D-17 已决策 |

**Key insight:** AntD 5 主题系统是"种子 token → map token → alias token"三层推导，darkAlgorithm 只替换推导函数，业务代码零感知。手写暗模色的后果是在未来 AntD 升级时出现一致性偏差。

## Common Pitfalls

### Pitfall 1: FOUC（首屏闪烁）
**What goes wrong:** 用户刷新页面时先看到亮模背景闪一下再切到暗模
**Why it happens:** React bundle 加载 + 解析 + 运行 ThemeModeProvider effect 有 ~200ms 延迟，默认 HTML 背景是白色
**How to avoid:** D-13 已决策 — `index.html <head>` 同步脚本在 React 加载前给 `<html>` 设 `data-theme`，并用 inline style 强制背景色
**Warning signs:** 刷新页面肉眼可见闪烁

### Pitfall 2: "半白半黑" 混合色
**What goes wrong:** 切换到暗模后某些区域仍是白底或亮色文字，视觉撕裂
**Why it happens:**
  1. 硬编码色未清理（如 `background: '#fff'`、`color: '#1F2329'`）
  2. 使用了非 AntD 组件或 `<div>` 直接设置颜色
  3. Layout.Sider 固定深色与亮模 Content 是"刻意"的飞书风格，需与"漏网之鱼"区分
**How to avoid:**
  1. 本 research 的硬编码色审计表列出所有 33+ 位置，逐一替换
  2. 验收阶段做 grep 二次确认：`grep -rn "style.*#" frontend/src/**/*.tsx`
  3. 明确排除 D-16 的 Sider 深色
**Warning signs:** 暗模下出现白色卡片/白色边框/浅灰背景；深色下文字太暗无法阅读

### Pitfall 3: useToken hook 调用位置错误
**What goes wrong:** `Cannot read properties of undefined` 或颜色不切换
**Why it happens:** 在模块顶层、Table columns 数组定义处、React 组件外部调用 hook
**How to avoid:**
  1. D-03 决策：Table columns 用 `chartColors.ts` 纯函数版本
  2. hook 只在 functional component body 或 custom hook 内使用
  3. 规则检查：`useXxx` 命名 + 必须在组件内
**Warning signs:** ESLint `react-hooks/rules-of-hooks` 报错

### Pitfall 4: localStorage 在 Safari 隐私模式抛错
**What goes wrong:** 整站白屏
**Why it happens:** Safari 隐私模式 localStorage.setItem 抛 QuotaExceededError
**How to avoid:** 所有 localStorage 读写用 try/catch 包裹
**Warning signs:** Safari 无痕标签页白屏

### Pitfall 5: Sider 深色与暗模内容区"融为一体"
**What goes wrong:** 暗模下 Sider（#1F2329）与 Content 背景（darkAlgorithm 默认约 #141414）接近，视觉边界消失
**Why it happens:** darkAlgorithm 默认 bodyBg 接近 Sider 色
**How to avoid:**
  1. 在 ConfigProvider dark 模式下给 Layout.bodyBg 指定稍亮的值（如 `#1F1F1F`）
  2. 或给 Sider 加 `borderRight: 1px solid rgba(255,255,255,0.08)`
  3. STATE.md 已记录此风险：*"暗黑模式下现有暗色侧边栏可能与内容区背景无法区分"*
**Warning signs:** 暗模下侧边栏和主内容区无视觉分隔

### Pitfall 6: React Flow（@xyflow/react）背景色不跟随主题
**What goes wrong:** FeishuFieldMapping 页面有 `<Background color="#DEE0E3" />` 硬编码色
**Why it happens:** React Flow 是第三方组件，不消费 AntD token
**How to avoid:** 在 FeishuFieldMapping 组件内 `const { token } = theme.useToken();` 然后 `<Background color={token.colorBorder} />`
**Warning signs:** 暗模下 React Flow 画布底色不变

## Hardcoded Color Audit

**总计：33 个内联颜色位置 + React Flow 1 处 + MainLayout.module.css 2 处 = 36 处需迁移**

**死代码：** `frontend/src/styles.css` (3520 行, 200+ 硬编码色) **未被任何文件 import**（已 grep 全项目确认），建议本 phase 顺手物理删除避免未来误导。

### Token Mapping Table

| File | Line | Current | Target Token | Notes |
|------|------|---------|--------------|-------|
| App.tsx | 41 | `background: '#F5F6F7'` | `colorBgLayout` | useSemanticColors().BG_LAYOUT |
| layouts/MainLayout.tsx | 271 | `background: '#fff'` | `colorBgContainer` | Header 背景 |
| layouts/MainLayout.tsx | 276 | `border: '1px solid #DEE0E3'` | `colorBorder` | |
| layouts/MainLayout.tsx | 291 | `background: '#F5F6F7'` | `colorBgLayout` | Content 背景 |
| layouts/MainLayout.module.css | 3, 12 | `color: #fff` | 保持（Sider 内的 logo） | D-16 Sider 始终深色 |
| pages/Login.tsx | 217 | `background: '#F5F6F7'` | `colorBgLayout` | D-19 |
| pages/Login.tsx | 221 | `rgba(0,0,0,0.06)` shadow | `boxShadowTertiary` | |
| pages/Portal.tsx | 17/24/31 | `color: '#3370FF'` | `colorPrimary` | D-21 |
| pages/Workspace.tsx | 130 | `color: '#3370FF'` | `colorPrimary` | D-21 |
| pages/Dashboard.tsx | 257 | `borderColor: '#F54A45'` | `colorError` | useCardStatusColors |
| pages/Dashboard.tsx | 279 | `color: '#3370FF'` (条件) | `colorPrimary` | |
| pages/Employees.tsx | 433 | `borderColor: '#F54A45'` | `colorError` | useCardStatusColors |
| pages/ImportBatchDetail.tsx | 77-79 | `#00B42A/#FF7D00/#F54A45` | chartColors 函数 | confidence 阈值色（组件外） |
| pages/ImportBatchDetail.tsx | 261 | `color: '#999'` | `colorTextTertiary` | D-04 |
| pages/ImportBatchDetail.tsx | 314 | `borderColor: '#F54A45'` | `colorError` | |
| pages/ImportBatchDetail.tsx | 358 | `borderColor: '#3370FF'` | `colorPrimary` | 条件激活态 |
| pages/SimpleAggregate.tsx | 375/381/397 | 三色边框 | useCardStatusColors | D-06 |
| pages/SimpleAggregate.tsx | 432/434/459/461 | 蓝 + 灰 | colorPrimary + colorTextTertiary | |
| pages/SimpleAggregate.tsx | 555 | `#DEE0E3` | `colorBorder` | |
| pages/SimpleAggregate.tsx | 606 | `#E8E8E8` | `colorBorderSecondary` | |
| pages/SimpleAggregate.tsx | 662 | 三状态色（render 内） | chartColors 函数 | |
| pages/Results.tsx | 323/326/329 | 三色 valueStyle | useSemanticColors | SUCCESS/ERROR/WARNING |
| pages/Exports.tsx | 269 | `color: '#00B42A'` | `colorSuccess` | |
| pages/Mappings.tsx | 394/397 | 蓝/红 valueStyle | useSemanticColors | |
| pages/AnomalyDetection.tsx | 267/285-287/449/456 | 四色（map 与 render 内） | chartColors 函数 | D-03 |
| pages/Compare.tsx | 610 | `background: '#fafafa'` | `colorFillQuaternary` | D-04 |
| pages/Compare.tsx | 771-773/845 | 三色 valueStyle + border | useSemanticColors | |
| pages/PeriodCompare.tsx | 70-76/166/172/178 | 差异色（函数内） | chartColors 函数 | D-07 |
| pages/PeriodCompare.tsx | 230 | `'#FFF7E6'` | `colorWarningBg` | D-05 HIGHLIGHT_BG |
| pages/PeriodCompare.tsx | 347/412/419/426 | 四色 | useSemanticColors | |
| pages/Imports.tsx | 327/329/376 | 蓝/灰/浅蓝 | useSemanticColors | 其中 #F0F5FF → colorPrimaryBg |
| pages/FeishuFieldMapping.tsx | 69/70/76/83/95/96/102/108/121/353 | 9+ 硬编码色（含 React Flow） | 全部 token 化 | D-20；React Flow Background 用 useToken |
| pages/FeishuSync.tsx | 45-47（模块顶层）| 三色常量 | chartColors 函数 | D-03 |
| pages/FeishuSync.tsx | 373/390/463/473 | `'#FFF7E6'` 高亮 | colorWarningBg | D-05 |
| pages/ApiKeys.tsx | 260 | `background: '#f5f5f5'` | `colorFillQuaternary` | D-04 |

**AntD 5 token 参考（通过 darkAlgorithm 自动适配）：**

| Semantic | Light 默认 | Dark 自动计算 |
|----------|-----------|---------------|
| colorPrimary | 项目定制 `#3370FF` | darkAlgorithm 提亮至约 `#3C89E8` |
| colorSuccess | `#00B42A` | 约 `#49AA19` |
| colorWarning | `#FF7D00` | 约 `#D89614` |
| colorError | `#F54A45` | 约 `#DC4446` |
| colorText | `#1F2329` | `rgba(255,255,255,0.85)` |
| colorTextTertiary | `#8F959E` | `rgba(255,255,255,0.45)` |
| colorBgContainer | `#FFFFFF` | `#141414` |
| colorBgLayout | `#F5F6F7` | `#000000` |
| colorBorder | `#DEE0E3` | `#424242` |
| colorPrimaryBg | `#F0F5FF` (自动生成) | 深色半透明 |
| colorWarningBg | `#FFF7E6` (自动生成) | 深色半透明 |
| colorFillQuaternary | `#f5f5f5` (自动生成) | `rgba(255,255,255,0.04)` |

[CITED: AntD 5 token 表 — ant.design/docs/react/customize-theme#preset theme]

## Code Examples

### Example 1: main.tsx 改造

```tsx
// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider, App as AntApp } from "antd";
import zhCN from "antd/locale/zh_CN";

import App from "./App";
import { ApiFeedbackProvider, AuthProvider } from "./components";
import { ThemeModeProvider } from "./theme/ThemeModeProvider";
import { useThemeMode } from "./theme/useThemeMode";
import { buildTheme } from "./theme";

function ThemedConfig({ children }: { children: React.ReactNode }) {
  const { mode } = useThemeMode();
  return (
    <ConfigProvider theme={buildTheme(mode)} componentSize="small" locale={zhCN}>
      <AntApp>{children}</AntApp>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeModeProvider>
      <ThemedConfig>
        <BrowserRouter>
          <AuthProvider>
            <ApiFeedbackProvider>
              <App />
            </ApiFeedbackProvider>
          </AuthProvider>
        </BrowserRouter>
      </ThemedConfig>
    </ThemeModeProvider>
  </React.StrictMode>,
);
```

### Example 2: theme/index.ts 改造为 buildTheme

```tsx
// frontend/src/theme/index.ts
import type { ThemeConfig } from 'antd';
import { theme as antdTheme } from 'antd';

export function buildTheme(mode: 'light' | 'dark'): ThemeConfig {
  const isDark = mode === 'dark';
  return {
    algorithm: isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: {
      colorPrimary: '#3370FF',
      // 亮模保留项目飞书蓝 token；暗模交由 darkAlgorithm
      ...(isDark ? {} : {
        colorBgContainer: '#FFFFFF',
        colorBgLayout: '#F5F6F7',
        colorText: '#1F2329',
        // ... 其余现有 token
      }),
      fontFamily: '"PingFang SC", ...',
      fontSize: 14,
      borderRadius: 8,
      // ... 其余与模式无关的 token
    },
    components: {
      Layout: {
        siderBg: '#1F2329',  // D-16: 亮暗统一
        headerBg: isDark ? '#1F1F1F' : '#FFFFFF',
        bodyBg: isDark ? '#1F1F1F' : '#F5F6F7',  // 比默认 #141414 稍亮，与 Sider 区分（Pitfall 5）
        headerHeight: 56,
        headerPadding: '0 24px',
      },
      Menu: { /* 保持现有 dark 配置 */ },
      Table: {
        headerBg: isDark ? undefined : '#F5F6F7',  // 暗模交由算法
        headerColor: isDark ? undefined : '#1F2329',
        rowHoverBg: isDark ? undefined : '#F0F5FF',  // D-18
      },
      // ...
    },
  };
}

// 兼容旧 import：
export const theme = buildTheme('light');
```

### Example 3: 切换按钮

```tsx
// 放在 MainLayout.tsx Header 右侧（D-08）
import { SunOutlined, MoonOutlined } from '@ant-design/icons';
import { useThemeMode } from '../theme/useThemeMode';

function ThemeToggleButton() {
  const { isDark, toggleMode } = useThemeMode();
  return (
    <Button
      type="text"
      icon={isDark ? <SunOutlined /> : <MoonOutlined />}
      onClick={toggleMode}
      aria-label={isDark ? '切换到亮色模式' : '切换到暗色模式'}
    />
  );
}
```

### Example 4: 消费语义色

```tsx
// 在 Results.tsx
import { useSemanticColors } from '../theme/useSemanticColors';

function ResultsPage() {
  const colors = useSemanticColors();
  return (
    <Row>
      <Statistic title="已匹配" value={count} valueStyle={{ color: colors.SUCCESS }} />
      <Statistic title="未匹配" value={count} valueStyle={{ color: colors.ERROR }} />
      <Statistic title="重复命中" value={count} valueStyle={{ color: colors.WARNING }} />
    </Row>
  );
}
```

### Example 5: Table columns 用 chartColors

```tsx
// 在 AnomalyDetection.tsx
import { getChartColors } from '../theme/chartColors';
import { useThemeMode } from '../theme/useThemeMode';

function AnomalyDetectionPage() {
  const { isDark } = useThemeMode();
  const colors = useMemo(() => getChartColors(isDark), [isDark]);

  const columns = useMemo(() => [
    {
      title: '差值',
      render: (v: number) => {
        const color = v > 0 ? colors.error : v < 0 ? colors.success : undefined;
        return <span style={{ color }}>{v}</span>;
      },
    },
  ], [colors]);

  return <Table columns={columns} />;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Less-variable 主题定制 (AntD v4) | ThemeConfig + algorithm (AntD v5) | AntD 5.0 (2022-11) | 无需构建时注入，运行时切换 |
| 独立 antd-dark-theme 包 | 内置 theme.darkAlgorithm | AntD 5.0 | 零依赖 |
| class="dark" + 手写 CSS 覆盖 | ConfigProvider algorithm | AntD 5.0 | 自动化 |

[CITED: Ant Design v5 CHANGELOG — ant.design/changelog]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | darkAlgorithm 对飞书蓝 `#3370FF` 产生可用的暗模主色（约 `#3C89E8`） | Token Mapping Table | 视觉质量下降，可微调 colorPrimary dark override |
| A2 | Safari 隐私模式 localStorage 抛错可被 try/catch 捕获 | Pitfall 4 | try/catch 遗漏导致白屏（已明确提示用 try/catch） |
| A3 | React Flow `<Background>` 组件接受动态 color prop | Pitfall 6 | 若不接受需换其他视觉方案；实际 API 支持（@xyflow/react 12.x） |
| A4 | DARK_CHART_COLORS 表中的具体色值是 darkAlgorithm 推导近似 | Pattern 3 | 实际运行时值可能略有偏差；建议实现后用 useToken 校准 |
| A5 | 暗模 bodyBg `#1F1F1F` 能与 Sider `#1F2329` 产生足够视觉对比 | Example 2 | 如仍融合需进一步区分（加 border 或调整数值） |

所有其他声明均已通过 package.json 文件、frontend/src grep、CONTEXT.md、AntD 5 公开 API 文档验证。

## Open Questions

1. **暗模下 Layout.Sider 是否需要微调？**
   - 已知：D-16 要求亮暗统一深色
   - 未明：STATE.md 已标记风险 "暗黑模式下现有暗色侧边栏可能与内容区背景无法区分"
   - 推荐：实现后视觉测试，必要时在暗模 bodyBg 调至 `#1F1F1F` 或给 Sider 加右边框（见 Example 2）

2. **styles.css 死代码清理是否纳入本 phase？**
   - 已知：全项目零 import，3520 行
   - 未明：CONTEXT.md 未提及
   - 推荐：纳入本 phase 一并清理（属于 token 化的副产物）；若担心 scope 可作为独立可选子任务

3. **FeishuFieldMapping 的 React Flow Background 点阵颜色在暗模下的视觉效果？**
   - 已知：D-20 要求全部 token 化
   - 未明：React Flow 的 Dots variant 在深色底上是否清晰
   - 推荐：暗模下用 `token.colorBorderSecondary` 或 `token.colorFillQuaternary`

4. **MainLayout.module.css 中 `color: #fff` (Sider 内 logo) 是否要改？**
   - 已知：Sider 始终深色（D-16）
   - 推荐：保持不动（在深色 Sider 上始终是白字）

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| antd | 主题系统核心 | ✓ | 5.29.3 | — |
| @ant-design/icons | SunOutlined/MoonOutlined | ✓ | 5.6.1 | — |
| react | Context + hooks | ✓ | 18.3.1 | — |
| node/npm | 构建 | ✓ | (由 Vite 管理) | — |

**无缺失依赖，无需 fallback。** 本阶段纯前端改造，无后端 / 无外部服务依赖。

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | frontend 未配置自动化单测框架（无 vitest/jest 在 package.json） |
| Config file | none — 当前仅 `npm run lint` + `npm run build` |
| Quick run command | `npm run lint --prefix frontend` |
| Full suite command | `npm run lint --prefix frontend && npm run build --prefix frontend` |

**手动验证为主：** 本 phase 以视觉验证 + 静态检查为核心，无业务逻辑需要单测覆盖。

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UX-01 | 33+ 硬编码色全部清理 | smoke | `! grep -rEn "style=\\{\\{[^}]*#[0-9A-Fa-f]{3,8}" frontend/src/**/*.tsx` (允许白名单) | ❌ Wave 0（需编写脚本） |
| UX-01 | lint 通过 | unit | `npm run lint --prefix frontend` | ✅ |
| UX-01 | build 成功 | unit | `npm run build --prefix frontend` | ✅ |
| UX-02 | 切换按钮存在且可点击 | manual | 打开 /dashboard，点击按钮观察切换 | ❌ manual-only |
| UX-02 | localStorage 持久化 | manual | 切换后刷新页面验证保持 | ❌ manual-only |
| UX-02 | 无 FOUC 闪烁 | manual | 刷新 dark 模式页面肉眼观察 | ❌ manual-only |
| UX-02 | 无"半白半黑" | manual | 每个页面暗模视觉巡检 | ❌ manual-only |

### Sampling Rate

- **Per task commit:** `npm run lint --prefix frontend`
- **Per wave merge:** `npm run lint --prefix frontend && npm run build --prefix frontend`
- **Phase gate:**
  1. lint + build 通过
  2. grep 硬编码色白名单外清零（Sider `#1F2329` / MainLayout.module.css `#fff` / buildTheme 内种子色允许）
  3. 手动视觉走查全部 20+ 页面在亮/暗两种模式

### Wave 0 Gaps

- [ ] 创建 `scripts/check-hardcoded-colors.sh`（或 package.json script）执行 grep 白名单检查 — 覆盖 UX-01 自动验证
- [ ] 无需单测框架引入（本 phase 纯视觉改造，无业务逻辑）

## Sources

### Primary (HIGH confidence)
- `frontend/package.json` — 依赖版本确认（antd 5.29.3）
- `frontend/src/theme/index.ts` — 现有 ThemeConfig 结构
- `frontend/src/main.tsx` — 现有 ConfigProvider 位置
- `frontend/src/**/*.tsx` grep 结果 — 33 个硬编码色位置
- `frontend/src/styles.css` — 死代码确认（grep 零 import）
- AntD 5 official docs: [ant.design/docs/react/customize-theme](https://ant.design/docs/react/customize-theme) — theme.useToken、darkAlgorithm API
- `npm view antd version` (执行于 2026-04-05) — latest 6.3.5，项目 5.29.3 同系列

### Secondary (MEDIUM confidence)
- CONTEXT.md D-01 至 D-21 决策 — 用户已锁定的实现路径
- STATE.md — "暗色侧边栏可能与内容区背景无法区分" 已知风险

### Tertiary (LOW confidence)
- DARK_CHART_COLORS 具体色值（A4）— AntD darkAlgorithm 运行时推导，需实现后用 useToken 实测校准

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 所有依赖已装，API 稳定
- Architecture: HIGH — CONTEXT.md 已锁定 21 项实现决策
- Token mapping: HIGH — grep 全量审计完成，33 个位置逐一映射
- Pitfalls: HIGH — 基于 AntD 5 实战常见问题 + STATE.md 已标风险
- DARK_CHART_COLORS 色值: MEDIUM — 需实现后实测

**Research date:** 2026-04-05
**Valid until:** 2026-05-05（AntD 5 主题 API 稳定，30 天内无重大变化）
