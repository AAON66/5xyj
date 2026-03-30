# Phase 6: Data Management - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 06-data-management
**Areas discussed:** 数据浏览与筛选, 数据质量仪表盘, 导入历史追溯, 全员汇总视图, 数据导出功能, 导航位置, 筛选持久化

---

## 数据浏览与筛选

### 页面位置

| Option | Description | Selected |
|--------|-------------|----------|
| 新建独立页面 | 新建「数据管理」页面，与现有页面职责分离 | ✓ |
| 增强现有 Results 页面 | 在 Results.tsx 基础上添加筛选和全员视图 | |
| 整合到 Dashboard | Dashboard 下方添加数据表格和筛选器 | |

**User's choice:** 新建独立页面

### 筛选方式

| Option | Description | Selected |
|--------|-------------|----------|
| 多条件联动筛选 | 地区→公司→月份三条件联动 | ✓ |
| 独立筛选 | 各条件独立不联动 | |
| 搜索框+筛选 | 下拉筛选基础上加搜索框 | |

**User's choice:** 多条件联动筛选

### 表格列展示

| Option | Description | Selected |
|--------|-------------|----------|
| 汇总模式 | 默认汇总列，点击展开明细 | ✓ |
| 全展开模式 | 直接显示所有险种列 | |
| 可配置列 | HR 可自选显示列 | |

**User's choice:** 汇总模式

---

## 数据质量仪表盘

### 位置

| Option | Description | Selected |
|--------|-------------|----------|
| 增强现有 Dashboard | 在 Dashboard.tsx 上添加质量区域 | ✓ |
| 独立质量页面 | 新建专门的质量页面 | |
| 嵌入数据管理页面 | 作为数据管理页面的 Tab 或区域 | |

**User's choice:** 增强现有 Dashboard

### 质量指标

| Option | Description | Selected |
|--------|-------------|----------|
| 缺失字段统计 | 按批次统计缺少关键字段的记录数 | ✓ |
| 异常金额检测 | 缴费基数或金额超出合理范围 | ✓ |
| 重复记录检测 | 同一人同月多条记录 | ✓ |
| 未匹配记录数 | 未匹配到员工主数据的记录 | |

**User's choice:** 缺失字段统计 + 异常金额检测 + 重复记录检测

---

## 导入历史追溯

### 展示方式

| Option | Description | Selected |
|--------|-------------|----------|
| 增强现有 Imports 页面 | 在 Imports.tsx 上添加操作人等列 | ✓ |
| 独立历史页面 | 新建专门的导入历史页面 | |
| 嵌入 Dashboard | 扩展 Dashboard 的最近批次区域 | |

**User's choice:** 增强现有 Imports 页面

### 操作人追溯

| Option | Description | Selected |
|--------|-------------|----------|
| 新增 operator 字段 | ImportBatch 新增 created_by 关联 User | ✓ |
| 复用审计日志 | 从 AuditLog 查询导入事件的操作人 | |

**User's choice:** 新增 operator 字段

---

## 全员汇总视图

### 主维度

| Option | Description | Selected |
|--------|-------------|----------|
| 按员工汇总 | 每人一行，最新月份数据 | |
| 按月份汇总 | 每月一行，总人数/总金额 | |
| 双维度切换 | 支持员工和月份两种视角切换 | ✓ |

**User's choice:** 双维度切换

### 位置

| Option | Description | Selected |
|--------|-------------|----------|
| 数据管理页面 Tab | 明细数据和全员汇总两个 Tab | ✓ |
| 独立汇总页面 | 新建独立的全员汇总页面 | |
| 嵌入 Dashboard | Dashboard 下方添加汇总表格 | |

**User's choice:** 数据管理页面 Tab

---

## 数据导出功能

| Option | Description | Selected |
|--------|-------------|----------|
| 不需要 | 数据管理页面只做浏览筛选，导出用现有流程 | ✓ |
| 筛选结果导出 | 支持导出当前筛选结果为 Excel | |
| 链接到导出页面 | 放导出按钮跳转到 Exports 页面 | |

**User's choice:** 不需要

---

## 导航位置

| Option | Description | Selected |
|--------|-------------|----------|
| 一级菜单项 | 侧边栏一级菜单，与 Dashboard 并列 | ✓ |
| 二级子菜单 | 放在「数据」父菜单下 | |

**User's choice:** 一级菜单项

---

## 筛选持久化

| Option | Description | Selected |
|--------|-------------|----------|
| URL 参数持久化 | 筛选条件存入 URL query params | ✓ |
| 不持久化 | 仅存在于页面状态 | |

**User's choice:** URL 参数持久化

---

## Claude's Discretion

- Tab 组件实现方式
- 联动筛选的加载/空状态展示
- 汇总视图排序方式
- 异常阈值具体数值
- 导入历史分页参数

## Deferred Ideas

- 筛选结果导出为 Excel — 后续阶段考虑
- 自定义表格列配置 — Phase 8 UI 重建时考虑
