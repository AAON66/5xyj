# Phase 15: 菜单重组与设置导航 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-07
**Phase:** 15-menu-reorganize-settings-nav
**Areas discussed:** 菜单分组方案, 设置页内容与搜索, 折叠状态持久化

---

## 菜单分组方案

| Option | Description | Selected |
|--------|-------------|----------|
| 按业务流程分组 | 数据处理/数据分析/管理/系统设置，四组按业务逻辑划分 | |
| 按频率分组 | 常用/数据分析/高级设置，按使用频率划分 | ✓ |

**User's choice:** 按频率分组
**Notes:** 用户偏好按使用频率而非业务流程分组

---

## 快速融合入口

| Option | Description | Selected |
|--------|-------------|----------|
| 独立置顶（推荐） | 快速融合放在菜单最顶部不折叠，一键可达 | ✓ |
| 归入数据处理组 | 与批次管理等同属数据处理流程 | |

**User's choice:** 独立置顶
**Notes:** 最高频操作应该最容易触达

---

## 分组明细

| Option | Description | Selected |
|--------|-------------|----------|
| 方案 A（推荐） | 常用：看板/批次/校验/导出。分析：对比/异常/映射。管理：员工/数据/审计/API/飞书 | ✓ |
| 方案 B | 四组更细分：常用/数据处理/分析/管理 | |

**User's choice:** 方案 A（三组）
**Notes:** 三组足够，四组过于细碎

---

## 菜单默认展开状态

| Option | Description | Selected |
|--------|-------------|----------|
| 常用展开，其他折叠（推荐） | 首次加载只展开常用组 | ✓ |
| 全部展开 | 所有分组默认展开 | |
| 全部折叠 | 所有分组默认折叠 | |

**User's choice:** 常用展开，其他折叠

---

## 设置页组织

| Option | Description | Selected |
|--------|-------------|----------|
| 单页分区（推荐） | /settings 页面用卡片分区展示各类设置 | ✓ |
| 左右分栏布局 | 左侧导航右侧内容，类似 macOS 偏好设置 | |
| 保持现状只改菜单 | 不建设置页，各设置保持独立页面 | |

**User's choice:** 单页分区

---

## 设置页搜索交互

| Option | Description | Selected |
|--------|-------------|----------|
| 页内筛选+滚动高亮（推荐） | 输入关键词隐藏不匹配卡片，高亮匹配项 | ✓ |
| 下拉快速跳转 | 搜索框弹出下拉列表，点击跳转 | |

**User's choice:** 页内筛选+滚动高亮

---

## 折叠状态持久化

| Option | Description | Selected |
|--------|-------------|----------|
| localStorage（推荐） | 关闭浏览器重开仍保持，与 theme-mode 一致 | ✓ |
| sessionStorage | 当前标签页内保持，关闭后重置 | |

**User's choice:** localStorage，键名 menu-open-keys

---

## Claude's Discretion

- 设置页卡片排列顺序和视觉样式
- 搜索高亮动画效果
- 员工角色菜单是否需要分组

## Deferred Ideas

None
