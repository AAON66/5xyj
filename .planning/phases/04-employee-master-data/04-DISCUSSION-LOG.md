# Phase 4: Employee Master Data - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 04-employee-master-data
**Areas discussed:** region 字段补全, 批量导入体验, 匹配策略, 前端完善度

---

## Region 字段管理

| Option | Description | Selected |
|--------|-------------|----------|
| 固定选项列表 | 只能从预定义地区中选择（广州/杭州/厦门/深圳/武汉/长沙），新增地区需后台配置 | ✓ |
| 自由输入 | 用户可输入任意地区名称，灵活但可能不一致 | |
| 下拉+自定义 | 默认从已知地区选择，也允许输入新地区 | |

**User's choice:** 固定选项列表
**Notes:** 与社保解析器支持的 6 个地区保持一致，数据一致性优先

---

## 批量导入重复处理

| Option | Description | Selected |
|--------|-------------|----------|
| 覆盖更新 | 已存在的工号直接用新数据覆盖，最简单 | ✓ |
| 跳过已存在 | 工号已存在则跳过该行，只导入新员工 | |
| 报错提示 | 发现重复工号时报错，让 HR 手动决定 | |

**User's choice:** 覆盖更新
**Notes:** HR 只需确保 Excel 是最新的即可

---

## 匹配策略

| Option | Description | Selected |
|--------|-------------|----------|
| 工号优先，身份证号备选 | 先按工号精确匹配，不存在时尝试身份证号 | |
| 身份证号优先，工号备选 | 先按身份证号匹配，跨公司也能匹配 | |
| 双维度并行 | 同时按工号和身份证号匹配，任一命中即成功 | ✓ |

**User's choice:** 双维度并行
**Notes:** 覆盖面最广

---

## 匹配失败处理

| Option | Description | Selected |
|--------|-------------|----------|
| 标记为未匹配，保留数据 | 未匹配的社保记录正常导入，标记状态，HR 后续处理 | ✓ |
| 拒绝导入未匹配行 | 只导入能匹配的记录，未匹配的报错 | |

**User's choice:** 标记为未匹配，保留数据

---

## 前端完善度

| Option | Description | Selected |
|--------|-------------|----------|
| 按地区筛选 | 添加 region 下拉筛选 | ✓ |
| 按公司筛选 | 添加 company_name 下拉筛选 | ✓ |
| 导入结果反馈 | 批量导入后显示新增/更新/失败统计 | ✓ |
| 列表分页 | 员工列表添加分页功能 | ✓ |

**User's choice:** 全部选中

---

## Claude's Discretion

- region 字段数据库迁移方式
- 前端筛选组件样式和布局
- 导入结果反馈 UI 形式
- 匹配结果记录数据模型细节
