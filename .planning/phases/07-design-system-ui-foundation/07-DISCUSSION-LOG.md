# Phase 7: Design System & UI Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 07-design-system-ui-foundation
**Areas discussed:** 迁移策略, 布局与导航, 视觉风格, 动画与交互, 图标与插图, 表格组件选型, 消息反馈统一, 表单组件统一, 文件上传组件, 模态框/抽屉统一

---

## 迁移策略

### 迁移方式

| Option | Description | Selected |
|--------|-------------|----------|
| 一次性重写 | 所有页面同时替换为 Ant Design，避免新旧混合的视觉不一致 | ✓ |
| 渐进式迁移 | 先建主题+Layout，然后逐页迁移 | |
| Claude 决定 | 根据代码复杂度和风险自行判断 | |

**User's choice:** 一次性重写

### 背景保留

| Option | Description | Selected |
|--------|-------------|----------|
| 保留并融合 | 保留现有渐变背景+网格纹理，作为 Ant Design 主题的底层装饰 | |
| 替换为飞书风格 | 全新设计背景，参考飞书的纯净浅灰风格 | ✓ |
| Claude 决定 | 根据飞书风格和现有设计自行判断 | |

**User's choice:** 替换为飞书风格

---

## 布局与导航

### 布局结构

| Option | Description | Selected |
|--------|-------------|----------|
| Ant Layout 全套 | 用 Ant Design 的 Layout + Sider + Menu 替换现有侧边栏 | ✓ |
| 侧边栏保留自定义 | 侧边栏继续用自定义组件，内容区域用 Ant Design 组件 | |

**User's choice:** Ant Layout 全套

### 侧边栏折叠

| Option | Description | Selected |
|--------|-------------|----------|
| 需要折叠 | 用户可以收起侧边栏只显示图标，节省屏幕空间 | ✓ |
| 不需要 | 侧边栏始终展开 | |

**User's choice:** 需要折叠

### Header 栏

| Option | Description | Selected |
|--------|-------------|----------|
| 需要 Header | 顶部显示面包屑导航 + 右侧用户头像/登出 | ✓ |
| 不需要 | 用户信息继续放在侧边栏底部 | |
| Claude 决定 | 根据飞书风格自行判断 | |

**User's choice:** 需要 Header

---

## 视觉风格

### 配色

| Option | Description | Selected |
|--------|-------------|----------|
| 飞书蓝系 | 主色 #3370FF，背景 #F5F6F7 浅灰，卡片纯白 | ✓ |
| 自定义配色 | 用户指定主色和风格偏好 | |
| Claude 决定 | Claude 选择一套专业的配色方案 | |

**User's choice:** 飞书蓝系

### 信息密度

| Option | Description | Selected |
|--------|-------------|----------|
| 紧凑高效 | 小卡片边距、表格行高较小、信息密度高 | ✓ |
| 宽松舒适 | 大卡片边距、表格行高较大、留白多 | |
| Claude 决定 | 根据页面类型自行判断 | |

**User's choice:** 紧凑高效

---

## 动画与交互

### 页面切换动画

| Option | Description | Selected |
|--------|-------------|----------|
| 轻微淡入淡出 | 页面切换时内容区域做简单的 fade + 微小位移 | ✓ |
| 无动画 | 直接切换，不做任何过渡效果 | |
| Claude 决定 | 根据体验自行判断 | |

**User's choice:** 轻微淡入淡出

### 加载状态

| Option | Description | Selected |
|--------|-------------|----------|
| Ant Skeleton 骨架屏 | 表格和卡片加载时显示灰色占位图形 | ✓ |
| Ant Spin 转圈 | 加载时显示旋转动画 | |
| Claude 决定 | 根据场景自行判断 | |

**User's choice:** Ant Skeleton 骨架屏

---

## 图标与插图

### 图标库

| Option | Description | Selected |
|--------|-------------|----------|
| @ant-design/icons | Ant Design 官方图标库 | ✓ |
| Lucide Icons | 简洁现代的开源图标库 | |
| Claude 决定 | 根据飞书风格自行判断 | |

**User's choice:** @ant-design/icons

### 空状态插图

| Option | Description | Selected |
|--------|-------------|----------|
| Ant Empty 默认 | 用 Ant Design 的 Empty 组件自带插图 | ✓ |
| 自定义 SVG 插图 | 设计专属的插图风格 | |
| Claude 决定 | Claude 自行判断 | |

**User's choice:** Ant Empty 默认

---

## 表格组件选型

| Option | Description | Selected |
|--------|-------------|----------|
| Ant Table | 统一用 Ant Table，自带排序/筛选/分页/加载状态 | ✓ |
| Ant Table + 虚拟滚动 | Ant Table 配合 virtual 属性或 react-window | |
| Claude 决定 | 根据数据量自行判断 | |

**User's choice:** Ant Table

---

## 消息反馈统一

| Option | Description | Selected |
|--------|-------------|----------|
| Ant message + notification | 操作反馈用 message，重要通知用 notification | ✓ |
| 保留 GlobalFeedback | 继续用现有组件，只调整样式 | |
| Claude 决定 | Claude 自行判断 | |

**User's choice:** Ant message + notification

---

## 表单组件统一

| Option | Description | Selected |
|--------|-------------|----------|
| Ant Form 全套 | 统一用 Ant Form + Form.Item + Input/Select/DatePicker | ✓ |
| 只用 Ant 输入组件 | 用 Ant Input/Select 替换原生元素，但不用 Form 包裹 | |
| Claude 决定 | 根据场景自行判断 | |

**User's choice:** Ant Form 全套

---

## 文件上传组件

| Option | Description | Selected |
|--------|-------------|----------|
| Ant Upload.Dragger | 用 Ant Design 的拖拽上传组件替换现有自定义实现 | ✓ |
| 保留自定义上传区域 | 只调整样式与 Ant 主题一致 | |
| Claude 决定 | Claude 自行判断 | |

**User's choice:** Ant Upload.Dragger

---

## 模态框/抽屉统一

| Option | Description | Selected |
|--------|-------------|----------|
| Modal 为主 + Drawer 辅助 | 确认/警告用 Modal，复杂表单编辑用 Drawer | ✓ |
| 全部用 Modal | 所有弹窗场景统一用 Ant Modal | |
| Claude 决定 | 根据场景自行判断 | |

**User's choice:** Modal 为主 + Drawer 辅助

---

## Claude's Discretion

- Ant Design ConfigProvider theme token 的具体数值调优
- 各页面具体的 Ant 组件选型细节
- CSS-in-JS vs CSS Modules 的样式方案选择
- 响应式断点的具体设置

## Deferred Ideas

None — discussion stayed within phase scope
