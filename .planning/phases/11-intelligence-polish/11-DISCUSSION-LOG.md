# Phase 11: Intelligence & Polish - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 11-intelligence-polish
**Areas discussed:** 跨期对比视图设计, 异常检测策略, 公积金全地区标准化, 字段映射覆盖 UI

---

## 跨期对比视图设计

### 对比期数

| Option | Description | Selected |
|--------|-------------|----------|
| 两个期间 | 类似现有的批次对比，左右两列对比 | ✓ |
| 多期（2-6个） | 支持选择 2-6 个月份同时对比 | |

**User's choice:** 两个期间

### 对比粒度

| Option | Description | Selected |
|--------|-------------|----------|
| 按人员明细 | 每个员工一行 | |
| 按公司/地区汇总 | 汇总层面对比 | |
| 两者都支持 | 默认汇总，可展开明细 | ✓ |

**User's choice:** 两者都支持

### 差异展示

| Option | Description | Selected |
|--------|-------------|----------|
| 表格 + 颜色高亮 | 变化字段红/绿高亮 | ✓ |
| 表格 + 变化量列 | 额外显示变化量和变化率 | |
| Claude 决定 | | |

**User's choice:** 表格 + 颜色高亮

---

## 异常检测策略

### 异常定义

| Option | Description | Selected |
|--------|-------------|----------|
| 基数/金额变化超过阈值 | 同一员工相邻两期变化超过百分比阈值 | ✓ |
| 基数 + 金额 + 人员变动 | 还检测新增/减少人员、停缴/补缴 | |
| 全面检测 | 所有异常类型 | |

**User's choice:** 基数/金额变化超过阈值

### 阈值粒度

| Option | Description | Selected |
|--------|-------------|----------|
| 全局一个阈值 | 统一百分比阈值 | |
| 按险种分别配置 | 每个险种独立阈值 | ✓ |
| 全局默认 + 可覆盖 | 全局默认值，特定险种可覆盖 | |

**User's choice:** 按险种分别配置

### 异常处理

| Option | Description | Selected |
|--------|-------------|----------|
| 只标记展示 | HR 自行判断 | |
| 标记 + 可确认/排除 | HR 可标记处理状态 | ✓ |
| Claude 决定 | | |

**User's choice:** 标记 + 可确认/排除

---

## 公积金全地区标准化

### 样例覆盖

| Option | Description | Selected |
|--------|-------------|----------|
| 全部已有 | 6 个地区公积金样例文件都在 data/samples/公积金/ | ✓ |
| 部分缺失 | 部分地区样例缺失 | |
| 不确定 | | |

**User's choice:** 全部已有

---

## 字段映射覆盖 UI

### 映射入口

| Option | Description | Selected |
|--------|-------------|----------|
| 导入结果页内嵌 | 在导入完成后的结果页展示映射表 | |
| 独立管理页 | 专门的字段映射页面 | |
| 两者都支持 | 导入结果页快速修正 + 独立管理页批量管理 | ✓ |

**User's choice:** 两者都支持

### 映射持久化

| Option | Description | Selected |
|--------|-------------|----------|
| 仅影响当前文件 | 修正只应用于当前已导入的文件 | ✓ |
| 保存为规则优先 | 修正保存为规则，后续相同表头自动应用 | |
| Claude 决定 | | |

**User's choice:** 仅影响当前文件

---

## Claude's Discretion

- 跨期对比的具体 SQL 查询优化方式
- 异常检测阈值的默认值
- 公积金各地区解析器的具体实现细节
- 字段映射管理页的筛选条件设计

## Deferred Ideas

None — discussion stayed within phase scope
