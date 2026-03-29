# Phase 5: Employee Portal - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-03-29
**Phase:** 05-employee-portal
**Areas discussed:** 社保明细展示, 历史记录浏览, 数据隔离与安全, 公积金展示, 员工登录体验, 无数据状态, Token过期处理, 导出/打印

---

## 社保明细展示

| Option | Description | Selected |
|--------|-------------|----------|
| 全部险种明细 | 每个险种都显示单位+个人金额 | |
| 简化版本 | 只显示汇总 | |
| 可展开明细 | 默认汇总，点击展开看各险种 | ✓ |

**User's choice:** 可展开明细

---

## 历史记录浏览

| Option | Description | Selected |
|--------|-------------|----------|
| 按月份列表 | 所有月份按时间倒序排列 | ✓ |
| 按月份筛选 | 下拉选择月份 | |
| 时间范围选择 | 起止月份筛选 | |

**User's choice:** 按月份列表

---

## 数据隔离与安全

| Option | Description | Selected |
|--------|-------------|----------|
| 现有机制足够 | token 约束即可 | |
| 需要加固 | 服务层二次校验 + 测试 | ✓ |

**User's choice:** 需要加固

---

## 公积金展示

| Option | Description | Selected |
|--------|-------------|----------|
| 与社保并列 | 同一页面并列 | ✓ |
| 分页签切换 | 社保和公积金分 tab | |

**User's choice:** 与社保并列

---

## 员工登录体验

| Option | Description | Selected |
|--------|-------------|----------|
| 直接进入记录列表 | 简单直接 | |
| 概览首页+明细 | 先概览再详情 | ✓ |
| 当前流程不变 | 保持现有 | |

**User's choice:** 概览首页+明细

---

## 无数据状态

| Option | Description | Selected |
|--------|-------------|----------|
| 友好提示 | 显示"暂无记录，请联系HR" | ✓ |
| 空表格+提示 | 显示空表格结构 | |

**User's choice:** 友好提示

---

## Token 过期处理

| Option | Description | Selected |
|--------|-------------|----------|
| 提示后跳转登录 | 显示过期提示，2秒后跳回 | ✓ |
| 静默跳回 | 直接跳回不提示 | |

**User's choice:** 提示后跳转登录

---

## 导出/打印

| Option | Description | Selected |
|--------|-------------|----------|
| 延后到 Phase 11 | 当前只做查看 | ✓ |
| 本阶段实现 | 导出 Excel/PDF | |

**User's choice:** 延后到 Phase 11

---

## Claude's Discretion

- 概览首页布局
- 险种展开/折叠动画
- 无数据状态图标
- Token 过期 UI 实现
