# Phase 5: Employee Portal - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

员工验证后可安全查看个人社保和公积金缴费记录。包含概览首页（最新月份汇总+个人信息）和历史明细页（按月份列表，可展开查看各险种拆分）。社保和公积金在同一页面并列展示。严格数据隔离确保员工只能查看自己的数据。

不涉及：导出/打印功能（延后到 Phase 11）、数据管理/仪表盘（Phase 6）、UI 重设计（Phase 7-8）。

</domain>

<decisions>
## Implementation Decisions

### 社保明细展示 (PORTAL-01, PORTAL-05)
- **D-01:** 默认显示汇总金额（单位合计/个人合计/总额），点击可展开查看各险种明细
- **D-02:** 展开后显示：养老(单位/个人)、医疗(单位/个人)、失业(单位/个人)、工伤(单位)、生育(单位)，加缴费基数
- **D-03:** 后端 EmployeeSelfServiceRecordRead schema 需新增各险种明细字段（pension_company, pension_personal, medical_company, medical_personal, unemployment_company, unemployment_personal, injury_company, maternity_amount）和 payment_base
- **D-04:** lookup_employee_self_service 服务需从 NormalizedRecord 中读取这些字段并填充到返回结果

### 公积金展示 (PORTAL-02)
- **D-05:** 公积金与社保在同一页面并列展示，不分 tab
- **D-06:** 每月记录同时包含社保明细和公积金明细（housing_fund_personal, housing_fund_company, housing_fund_total）
- **D-07:** 当前 schema 已有公积金字段，无需新增

### 历史记录浏览 (PORTAL-03)
- **D-08:** 所有月份按时间倒序排列（最新月份在前），不分页不筛选
- **D-09:** 每条记录显示：月份、地区、公司、汇总金额，可展开看险种明细

### 数据隔离与安全 (PORTAL-04)
- **D-10:** 后端所有员工查询端点必须强制使用 token 中的 employee_id，不接受前端传入的 ID 参数
- **D-11:** 服务层增加二次校验：即使 API 被篡改，查询条件也必须绑定到当前 token 用户
- **D-12:** 新增测试验证：用 employee A 的 token 尝试查询 employee B 的数据，必须返回 403

### 员工登录体验
- **D-13:** 员工验证后进入概览首页：显示个人信息（姓名、工号、公司、脱敏身份证号）+ 最新月份的缴费汇总
- **D-14:** 概览首页下方是按月份倒序的历史记录列表，可展开查看各险种明细
- **D-15:** 无需独立的"历史明细"页面，概览和历史在同一页面

### 无数据状态
- **D-16:** 员工登录后无社保记录时，显示友好提示"暂无社保缴费记录，请联系 HR 确认"，不显示空表格

### Token 过期处理
- **D-17:** Token 过期时前端显示"登录已过期，请重新验证"提示，2 秒后自动跳回验证页
- **D-18:** 不支持自动续期（30 分钟是有意设计的安全限制）

### 导出/打印
- **D-19:** 本阶段不实现导出/打印功能，延后到 Phase 11

### Claude's Discretion
- 概览首页的具体布局（卡片式 vs 列表式）
- 险种明细的展开/折叠动画
- 无数据状态的图标/插画选择
- Token 过期提示的具体 UI 实现

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 员工自助服务（现有代码）
- `backend/app/services/employee_service.py` — lookup_employee_self_service 函数（349行起）
- `backend/app/schemas/employees.py` — EmployeeSelfServiceRecordRead（需扩展险种字段）
- `backend/app/api/v1/employees.py` — self-service/query 端点
- `backend/app/api/v1/auth.py` — employee_verify_endpoint 员工验证

### 前端页面（现有代码）
- `frontend/src/pages/EmployeeSelfService.tsx` — 已有自助查询页（238行，需大幅改造）
- `frontend/src/pages/Portal.tsx` — 门户首页（96行）
- `frontend/src/pages/Login.tsx` — 登录页（含员工验证入口）
- `frontend/src/App.tsx` — 路由配置

### 数据模型（参考）
- `backend/app/models/normalized_record.py` — NormalizedRecord 模型，包含各险种字段
- `backend/app/core/auth.py` — AuthUser 数据类，包含 role 和 employee_id

### Phase 2/3 安全基础（依赖）
- `backend/app/dependencies.py` — require_role, require_authenticated_user
- `backend/app/services/rate_limiter.py` — 员工验证频率限制
- `backend/app/utils/masking.py` — 身份证号脱敏

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lookup_employee_self_service`: 已有完整的查询逻辑（匹配 employee_master + normalized_records），只需扩展返回字段
- `EmployeeSelfService.tsx`: 238行已有页面框架，需要改造为概览+明细模式
- `mask_id_number`: Phase 3 脱敏工具可复用
- `readAuthSession`: Phase 3 修复后的统一 token 读取方法

### Established Patterns
- 员工验证流程：工号+身份证号+姓名 → 30分钟 token
- API 响应格式：success_response() 封装
- 前端 token 管理：authSession 服务

### Integration Points
- NormalizedRecord 模型已有各险种字段，只需在 self-service 查询中读取并返回
- 前端需从 EmployeeSelfService 页面改造为概览+明细展开模式

</code_context>

<specifics>
## Specific Ideas

- 概览首页应该让员工一眼看到最重要的信息：最新月份缴费总额和个人信息
- 险种明细展开设计参考社保局网站的分项展示方式
- 数据隔离是硬性安全要求，必须有测试覆盖

</specifics>

<deferred>
## Deferred Ideas

- 导出/打印个人社保明细 — 延后到 Phase 11（智能与完善）

</deferred>

---

*Phase: 05-employee-portal*
*Context gathered: 2026-03-29*
