# Phase 8: Page Rebuild & UX Flow - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 08-page-rebuild-ux-flow
**Areas discussed:** 角色导航差异化, 响应式布局策略, 中文本地化方案, 上传到导出工作流

---

## 角色导航差异化

### 侧边栏差异程度

| Option | Description | Selected |
|--------|-------------|----------|
| 仅过滤菜单项 | 同一布局，按角色显示/隐藏菜单项 | ✓ |
| 分角色布局 | 员工用无侧边栏简洁布局，HR/admin完整侧边栏 | |
| 分组+标记 | 菜单按功能分组，不同角色看不同分组，admin带角标 | |

**User's choice:** 仅过滤菜单项
**Notes:** 保持现有 buildMenuItems 逻辑

### 员工首页

| Option | Description | Selected |
|--------|-------------|----------|
| 直接进查询页 | 员工只有一个功能，不需要中间页 | ✓ |
| 简洁员工首页 | 轻量级工作台，显示欢迎+最近缴费+查询入口 | |

**User's choice:** 直接进查询页

### 无权限页面处理

| Option | Description | Selected |
|--------|-------------|----------|
| 静默跳转工作台 | 直接跳回角色默认页面 | ✓ |
| 显示 403 提示页 | 显示"您无权访问"提示+返回按钮 | |

**User's choice:** 静默跳转工作台

---

## 响应式布局策略

### 小屏幕侧边栏

| Option | Description | Selected |
|--------|-------------|----------|
| 自动折叠 | ≤1440px 自动折叠为图标模式(64px) | ✓ |
| 保持手动折叠 | 不做自动响应，用户自己点 | |
| 抽屉模式 | 小屏变成 Drawer 汉堡菜单 | |

**User's choice:** 自动折叠

### 表格列溢出

| Option | Description | Selected |
|--------|-------------|----------|
| 水平滚动 | Ant Table scroll={{ x: true }}，固定左侧列 | ✓ |
| 隐藏次要列 | 小屏隐藏部分列，提供展开按钮 | |
| 卡片模式切换 | 小屏变卡片列表 | |

**User's choice:** 水平滚动

---

## 中文本地化方案

### 本地化策略

| Option | Description | Selected |
|--------|-------------|----------|
| Ant ConfigProvider + 硬编码 | zhCN locale + 业务文案硬编码中文 | ✓ |
| 引入 i18n 框架 | react-i18next 完整国际化 | |

**User's choice:** Ant ConfigProvider + 硬编码

### 错误消息中文化

| Option | Description | Selected |
|--------|-------------|----------|
| 前端统一拦截 | API 客户端层拦截错误码映射为中文 | ✓ |
| 后端直接返回中文 | 后端 API 直接返回中文错误消息 | |

**User's choice:** 前端统一拦截

---

## 上传到导出工作流

### 流程串联方式

| Option | Description | Selected |
|--------|-------------|----------|
| 步骤引导条 | Ant Steps 组件（上传→解析→校验→导出） | ✓ |
| 完成后自动跳转 | 每步完成自动进下一步 | |
| 保持现状+快捷链接 | 各页面底部加"下一步"按钮 | |

**User's choice:** 步骤引导条

### 引导条位置

| Option | Description | Selected |
|--------|-------------|----------|
| 各页面顶部 | 四个页面都显示同一个 Steps | ✓ |
| 仅在工作台页 | 只在 HR 工作台首页显示 | |

**User's choice:** 各页面顶部

### 步骤状态反馈

| Option | Description | Selected |
|--------|-------------|----------|
| 状态图标+颜色 | 利用 Ant Steps status 属性：完成/进行中/警告/失败 | ✓ |
| 简单当前/完成 | 只区分已完成和当前 | |

**User's choice:** 状态图标+颜色

---

## Claude's Discretion

- 断点数值微调、Steps 样式、错误码映射表设计、Table 固定列选择

## Deferred Ideas

None
