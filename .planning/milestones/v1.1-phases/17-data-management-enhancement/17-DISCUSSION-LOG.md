# Phase 17: 数据管理增强 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 17-data-management-enhancement
**Areas discussed:** 多选筛选交互, 匹配状态过滤, 批次删除联动, 缴费基数修复

---

## 多选筛选交互

| Option | Description | Selected |
|--------|-------------|----------|
| 账期也多选（推荐） | 三个筛选全部多选，账期下拉显示所有已选地区+公司的账期并集 | ✓ |
| 账期保持单选 | 地区/公司多选，但账期保持单选 | |

**User's choice:** 账期也多选
**Notes:** 无

| Option | Description | Selected |
|--------|-------------|----------|
| AntD Select mode=multiple（推荐） | 与现有单选一致的下拉框，只是改为多选模式 | ✓ |
| Checkbox 分组面板 | 展开的 Checkbox 分组，类似电商筛选 | |

**User's choice:** AntD Select mode=multiple

| Option | Description | Selected |
|--------|-------------|----------|
| 需要全选（推荐） | 每个多选下拉顶部加「全选」选项 | ✓ |
| 不需要 | 只能逐个选择 | |

**User's choice:** 需要全选

| Option | Description | Selected |
|--------|-------------|----------|
| 保留级联（推荐） | 选了地区后，公司下拉只显示已选地区下的公司 | ✓ |
| 取消级联 | 三个筛选独立，各自显示所有可选项 | |

**User's choice:** 保留级联

---

## 匹配状态过滤

| Option | Description | Selected |
|--------|-------------|----------|
| 和地区/公司同行（推荐） | 作为筛选栏的第四个下拉 | ✓ |
| Tab 切换 | 在表格上方用 Tabs 切换 | |

**User's choice:** 和地区/公司同行

| Option | Description | Selected |
|--------|-------------|----------|
| 全部 / 已匹配 / 未匹配（推荐） | 简单三项，默认选已匹配 | ✓ |
| 细分所有状态 | 显示全部 5 种状态多选过滤 | |

**User's choice:** 全部 / 已匹配 / 未匹配

---

## 批次删除联动

| Option | Description | Selected |
|--------|-------------|----------|
| 就是现有 cascade | 当前 cascade delete 已覆盖所需 | ✓ |
| 还有其他表 | 除了三张表还有其他需要清理 | |

**User's choice:** 就是现有 cascade
**Notes:** 无需新增关联表清理

| Option | Description | Selected |
|--------|-------------|----------|
| 显示影响范围（推荐） | 删除确认弹窗显示具体影响数量 | ✓ |
| 简单确认即可 | 只显示「确认删除此批次？」 | |

**User's choice:** 显示影响范围

---

## 缴费基数修复

| Option | Description | Selected |
|--------|-------------|----------|
| 解析时拿错列 | 导入 Excel 时字段映射错误 | |
| 存储时覆盖 | 解析正确但存入数据库时被覆盖 | |
| 显示时拿错字段 | 后端正确但前端显示错误字段 | |
| 我不确定具体原因 | 需要 Claude 调查 | ✓ |

**User's choice:** 不确定具体原因，所有地区都有问题，由 Claude 在研究阶段调查定位

## Claude's Discretion

- 多选下拉的 maxTagCount 展示策略
- 匹配状态下拉的样式
- 删除影响数量的查询方式

## Deferred Ideas

None
