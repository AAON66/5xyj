# Phase 23: 登录页面改版 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 23-login-redesign
**Areas discussed:** 粒子动画效果, 暗黑模式适配, WebGL 降级策略

---

## 粒子动画效果

### 视觉风格

| Option | Description | Selected |
|--------|-------------|----------|
| 海浪流动感 | 粒子排布成波浪形态，连续起伏流动，像海面一样柔和。鼠标移动时波浪被"推开"。最经典的 3D 粒子效果 | ✓ |
| 星空网络感 | 粒子浮游 + 连线，像星座图。鼠标附近粒子被吸引靠拢。科技感强但比较常见 | |
| 抽象地形感 | 粒子形成 3D 山脉/地形，鼠标可旋转视角。视觉冲击力最强但实现最复杂 | |

**User's choice:** 海浪流动感

### 粒子密度

| Option | Description | Selected |
|--------|-------------|----------|
| 密集细腻（5000+） | 视觉效果最好，但低端设备可能卡顿。需要动态调整粒子数 | |
| 适中平衡（2000-3000） | 视觉和性能的最佳平衡点，大多数设备流畅（推荐） | ✓ |
| 简约稀疏（<1000） | 确保所有设备流畅，但视觉效果会较弱 | |

**User's choice:** 适中平衡（2000-3000）

### 鼠标交互

| Option | Description | Selected |
|--------|-------------|----------|
| 柔和推波 | 鼠标移到哪里，波浪就在那里轻柔隆起，离开后慢慢恢复。优雅不分散注意力（推荐） | ✓ |
| 明显吸引 | 鼠标附近粒子被明显吸引过来，形成漩涡效果。视觉冲击强但可能分散注意力 | |
| 你来决定 | 让 Claude 根据整体效果选择合适的交互方式 | |

**User's choice:** 柔和推波

### 粒子颜色

| Option | Description | Selected |
|--------|-------------|----------|
| 品牌主色系 | 使用项目主色 #3370FF 的渐变色谱，与系统整体视觉统一 | ✓ |
| 海洋蓝绿渐变 | 从深蓝到青绿的渐变，配合海浪主题，视觉更自然 | |
| 你来决定 | 让 Claude 根据整体设计选择合适的配色 | |

**User's choice:** 品牌主色系

### 粒子形状

| Option | Description | Selected |
|--------|-------------|----------|
| 圆形点 | 经典粒子效果，清洁简约（推荐） | ✓ |
| 光晕球体 | 带发光效果的球体，更有氛围感但性能开销更大 | |
| 你来决定 | 让 Claude 根据效果选择 | |

**User's choice:** 圆形点

---

## 暗黑模式适配

### 暗色粒子处理

| Option | Description | Selected |
|--------|-------------|----------|
| 变亮粒子 + 深色背景 | 背景变深色，粒子变亮色/发光效果，形成"深海荧光"感（推荐） | ✓ |
| 统一降低明度 | 粒子和背景都降低明度，整体变暗但保持相同配色结构 | |
| 你来决定 | 让 Claude 根据整体设计来处理 | |

**User's choice:** 变亮粒子 + 深色背景

### 暗色卡片样式

| Option | Description | Selected |
|--------|-------------|----------|
| 半透明模糊 | 卡片背景半透明 + backdrop-filter 模糊，能透出背后粒子效果，科技感强 | ✓ |
| 实色暗色卡片 | 跟随 Ant Design 暗黑主题默认样式，不透明。简单一致但没有融合感 | |
| 你来决定 | 让 Claude 根据实际效果选择 | |

**User's choice:** 半透明模糊

---

## WebGL 降级策略

### 降级背景样式

| Option | Description | Selected |
|--------|-------------|----------|
| CSS 渐变 + 微动效 | 用 CSS linear-gradient 做品牌色渐变背景，加轻微的 CSS animation 浮动效果，不完全静态（推荐） | ✓ |
| 纯静态渐变 | 仅 CSS 渐变背景，完全静态。最简单但视觉上差距较大 | |
| 你来决定 | 让 Claude 根据实际效果选择 | |

**User's choice:** CSS 渐变 + 微动效

### 检测时机

| Option | Description | Selected |
|--------|-------------|----------|
| 组件加载时检测 | 组件 mount 时尝试创建 WebGL context，失败则立即降级（推荐） | ✓ |
| 懒加载 Three.js | 先显示降级背景，后台加载 Three.js，成功后切换。首屏更快但会闪烁 | |

**User's choice:** 组件加载时检测

---

## Claude's Discretion

- 左右分栏比例
- 移动端断点
- 左侧品牌区域内容排版
- 粒子波浪具体参数
- 降级动画 CSS 实现
- Three.js lazy loading 策略

## Deferred Ideas

None
