# Phase 14: 样式 Token 化与暗黑模式 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-05
**Phase:** 14-style-tokens-dark-mode
**Areas discussed:** Token 替换方式、暗黑模式切换方式、暗黑模式下的品牌色、自定义组件的暗模支持、localStorage/FOUC/图表颜色、暗模 UI 细节

---

## Token 替换方式

| Option | Description | Selected |
|--------|-------------|----------|
| theme.useToken() hook 按需读取 | 每个组件单独调用 hook，零额外配置 | |
| CSS 变量 (--colorPrimary) | AntD cssVar: true 开启，性能最佳 | |
| 语义色常量模块 (推荐) | 创建 semanticColors.ts，集中管理 | ✓ |

**User's choice:** 语义色常量模块
**Notes:** 采用 hook 版本 useSemanticColors() + 独立 chartColors.ts 模块（常量 + getChartColors(isDark) 函数）

---

| Option | Description | Selected |
|--------|-------------|----------|
| 用 AntD 扩展 token (colorWarningBg) | AntD 内置背景色 token | |
| 将自定义颜色归到语义色常量 (推荐) | HIGHLIGHT_BG 语义名集中管理 | ✓ |

**User's choice:** 归到语义色常量

---

| Option | Description | Selected |
|--------|-------------|----------|
| 逐一匹配到 AntD 文本色 (推荐) | colorTextTertiary/colorFillQuaternary 等 | ✓ |
| 全部归类到语义色常量 | 统一但可能重复 | |

**User's choice:** 逐一匹配到 AntD 文本色

---

## 暗黑模式切换方式

| Option | Description | Selected |
|--------|-------------|----------|
| Header 右上角用户头像旁 (推荐) | 飞书/Linear/Notion 标配 | ✓ |
| 设置页面中 | 天然集中管理但不够快 | |
| 两者都支持 | 实现成本高 | |

**User's choice:** Header 右上角用户头像旁

---

| Option | Description | Selected |
|--------|-------------|----------|
| 跟随系统偏好 (推荐) | prefers-color-scheme 检测 | ✓ |
| 默认亮模 | 最简单 | |
| 默认暗模 | 数据密集型标配但与 Phase 7 亮模基础不符 | |

**User's choice:** 跟随系统偏好

---

| Option | Description | Selected |
|--------|-------------|----------|
| 瞬间切换，不加动画 (推荐) | Linear/Notion 做法 | ✓ |
| 200ms 淡入淡出过渡 | 更优雅但可能有性能开销 | |

**User's choice:** 瞬间切换，不加动画

---

## 暗黑模式下的品牌色

| Option | Description | Selected |
|--------|-------------|----------|
| AntD darkAlgorithm 自动计算 (推荐) | 零维护成本 | ✓ |
| 手动定义暗模专用主色 | 更精确 | |

**User's choice:** AntD darkAlgorithm 自动计算

---

| Option | Description | Selected |
|--------|-------------|----------|
| AntD darkAlgorithm 自动适配 (推荐) | 统一风格 | ✓ |
| 手动提高暗模亢度 | 更明显但高成本 | |

**User's choice:** AntD darkAlgorithm 自动适配

---

| Option | Description | Selected |
|--------|-------------|----------|
| 继续深色 (统一 #1F2329) | 飞书风格标志 | ✓ |
| 跟随整体暗模调整 | 更融合 | |

**User's choice:** 统一深色

---

## 自定义组件暗模支持

| Option | Description | Selected |
|--------|-------------|----------|
| 同 Layout 主背景 (推荐) | 用 colorBgLayout 保持一致 | ✓ |
| 亮模使用横向背景，暗模使用纯色 | 突出差异 | |

**User's choice:** 同 Layout 主背景

---

| Option | Description | Selected |
|--------|-------------|----------|
| 全部换成 AntD token化 (推荐) | 统一治理 | ✓ |
| 保留特定风格 | 特殊处理 | |

**User's choice:** 全部换成 token化

---

| Option | Description | Selected |
|--------|-------------|----------|
| Card状态色 封装为独立 hook (推荐) | useCardStatusColors() | ✓ |
| 直接用 useSemanticColors() | 更简单直接 | |

**User's choice:** 独立 hook

---

## 探索的额外区域

### localStorage 键名

| Option | Description | Selected |
|--------|-------------|----------|
| 'theme-mode' (推荐) | 简洁明了 | ✓ |
| 'ui.darkMode' | 命名空间前缀 | |
| 'user-preferences' 对象 | 未来扩展 | |

**User's choice:** 'theme-mode'

---

### FOUC 预防

| Option | Description | Selected |
|--------|-------------|----------|
| index.html 同步脚本 (推荐) | 零 FOUC | ✓ |
| 接受瞬间 FOUC | 最简单 | |

**User's choice:** index.html 同步脚本

---

### 跨期对比的差异高亮色

| Option | Description | Selected |
|--------|-------------|----------|
| 复用 useSemanticColors() (推荐) | 增加=warning, 减少=error, 新增=primary | ✓ |
| 专门封装 getDiffColors | 图表专用 | |

**User's choice:** 复用 useSemanticColors()

---

### Alert 暗模背景

| Option | Description | Selected |
|--------|-------------|----------|
| AntD darkAlgorithm 默认 (推荐) | 深色半透明 | ✓ |
| 深色实心背景 | 更醒目 | |

**User's choice:** AntD darkAlgorithm 默认

---

### Table hover 暗模

| Option | Description | Selected |
|--------|-------------|----------|
| AntD darkAlgorithm 自动适配 (推荐) | 深色微透明 | ✓ |
| 定制暗模 hover 背景 | 更多控制 | |

**User's choice:** AntD darkAlgorithm 自动适配

---

### Workspace/Portal 大图标

| Option | Description | Selected |
|--------|-------------|----------|
| darkAlgorithm + token化 (推荐) | BRAND 语义色 | ✓ |
| 暗模白色图标 | 更突出 | |

**User's choice:** darkAlgorithm + token化

---

## Claude's Discretion

- useSemanticColors hook 返回对象字段命名
- chartColors 模块具体导出接口
- useCardStatusColors hook 实现细节
- index.html FOUC 脚本代码
- 切换按钮图标选型（SunOutlined/MoonOutlined）

## Deferred Ideas

- 用户可自定义主题色（未来独立 phase）
- 跟随系统偏好的实时响应
- 更细粒度的颜色偏好（对比度调节 - 未来无障碍 phase）
