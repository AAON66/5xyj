# Phase 6: Data Management - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

HR 可高效浏览、筛选和审计所有社保数据。包含：新建数据管理页面（明细数据 + 全员汇总双 Tab）、增强现有 Dashboard 添加数据质量指标、增强现有 Imports 页面添加导入历史追溯。

不涉及：导出功能改动（继续使用现有双模板导出流程）、UI 重设计（Phase 7-8）、跨期对比（Phase 11）。

</domain>

<decisions>
## Implementation Decisions

### 数据浏览与筛选 (DATA-01)
- **D-01:** 新建独立「数据管理」页面，与现有 Results/Imports 页面职责分离
- **D-02:** 三条件联动筛选：地区 → 公司 → 月份，选地区后公司下拉框只显示该地区的公司
- **D-03:** 表格默认显示汇总列（姓名、工号、地区、公司、月份、单位合计、个人合计、总额），点击行展开查看各险种明细
- **D-04:** 筛选条件通过 URL query params 持久化（?region=shenzhen&company=xxx&period=202602），刷新保留、可分享链接
- **D-05:** 数据管理页面作为侧边栏一级菜单项，与 Dashboard、导入、导出并列
- **D-06:** 数据管理页面不包含导出功能，导出继续使用现有 Exports 页面

### 全员汇总视图 (DATA-02)
- **D-07:** 数据管理页面内设两个 Tab：「明细数据」和「全员汇总」
- **D-08:** 全员汇总支持双维度切换：按员工汇总（每人一行，最新月份数据）和按月份汇总（每月一行，总人数/总金额/平均金额）
- **D-09:** 汇总视图复用相同的三条件联动筛选器

### 数据质量仪表盘 (DATA-03)
- **D-10:** 增强现有 Dashboard.tsx 页面，添加数据质量区域
- **D-11:** 监控三个质量指标：缺失字段统计（缺少姓名/身份证号/工号的记录数）、异常金额检测（缴费基数超出合理范围）、重复记录检测（同一人同月多条记录）
- **D-12:** 质量指标按导入批次维度展示，每个批次显示各指标的问题数量

### 导入历史追溯 (DATA-04)
- **D-13:** 增强现有 Imports.tsx 页面，添加操作人、记录数、时间戳等信息列
- **D-14:** ImportBatch 模型新增 created_by 字段（ForeignKey 关联 User 表），导入时从当前登录用户 token 中提取
- **D-15:** 已有的 ImportBatch 记录 created_by 为 null（兼容历史数据）

### Claude's Discretion
- 数据管理页面的具体 Tab 组件实现方式
- 联动筛选的加载状态和空状态展示
- 汇总视图的排序方式
- 质量指标的异常阈值具体数值
- 导入历史的分页参数

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 数据模型（核心）
- `backend/app/models/normalized_record.py` — NormalizedRecord 模型，包含所有标准字段（region, company_name, billing_period, 各险种金额）
- `backend/app/models/import_batch.py` — ImportBatch 模型（需新增 created_by 字段）
- `backend/app/models/validation_issue.py` — ValidationIssue 模型，质量指标数据来源
- `backend/app/models/match_result.py` — MatchResult 模型，匹配状态数据
- `backend/app/models/source_file.py` — SourceFile 模型，导入文件信息

### 现有服务（复用）
- `backend/app/services/dashboard_service.py` — 现有 Dashboard 服务（需扩展质量指标）
- `backend/app/services/validation_service.py` — 校验服务，质量检测逻辑来源
- `backend/app/services/matching_service.py` — 匹配服务，未匹配记录统计来源
- `backend/app/services/audit_service.py` — 审计服务，操作记录

### 现有前端页面（增强）
- `frontend/src/pages/Dashboard.tsx` — 现有 Dashboard 页面（需添加质量区域）
- `frontend/src/pages/Imports.tsx` — 现有导入页面（需添加操作人等列）
- `frontend/src/pages/Results.tsx` — 现有结果页面（参考筛选模式）

### API 端点
- `backend/app/api/v1/dashboard.py` — Dashboard API（需扩展质量端点）
- `backend/app/api/v1/imports.py` — 导入 API（需返回操作人信息）
- `backend/app/api/v1/router.py` — 路由注册

### Phase 4 参考（筛选模式）
- `backend/app/api/v1/employees.py` — 员工列表筛选 API（服务端分页 + 筛选参数模式）
- `frontend/src/pages/Employees.tsx` — 员工列表页面（联动筛选 UI 模式参考）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard_service.py`: 已有总量统计和批次状态计数，可直接扩展质量指标
- `Employees.tsx`: Phase 4 已实现服务端分页 + 筛选下拉，可复用相同模式
- `PageContainer`, `SectionState`, `SurfaceNotice`: 现有 UI 组件可复用
- `NormalizedRecord` 模型已有完整的 region, company_name, billing_period 索引

### Established Patterns
- API 响应统一使用 `success_response()` 封装
- 路由权限通过 `require_role("admin", "hr")` 注入
- 前端筛选用 `useState` + `useEffect` 联动，从 API 获取选项列表
- 服务端分页返回 `items` + `total` + `page` + `page_size`

### Integration Points
- 新数据管理页面需在 App.tsx 添加路由，AppShell 添加导航项
- ImportBatch 新增 created_by 后需更新 schema 和 import API
- Dashboard 质量指标需新建后端 service 方法和 API 端点
- 联动筛选需新建 API 端点返回可用的地区/公司/月份选项

</code_context>

<specifics>
## Specific Ideas

- 联动筛选参考 Phase 4 员工列表的筛选交互模式，保持一致性
- 数据质量仪表盘应该一目了然，让 HR 快速判断本次导入是否有问题
- 全员汇总的双维度切换要直观，不要让 HR 困惑

</specifics>

<deferred>
## Deferred Ideas

- 筛选结果导出为 Excel — 可以考虑在后续阶段加入
- 自定义表格列配置 — Phase 8 UI 重建时考虑

</deferred>

---

*Phase: 06-data-management*
*Context gathered: 2026-03-30*
