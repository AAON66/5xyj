# Phase 4: Employee Master Data - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

HR 可维护完整的员工主数据（包含地区字段），用于身份验证和社保数据匹配。后端大部分 CRUD/导入/匹配功能已实现，本阶段主要补全 region 字段、完善批量导入体验、确认匹配策略、完善前端交互。

不涉及：员工自助查询页面（Phase 5）、数据管理/仪表盘（Phase 6）、UI 重设计（Phase 7-8）。

</domain>

<decisions>
## Implementation Decisions

### Region 字段补全 (MASTER-01)
- **D-01:** EmployeeMaster 模型新增 `region` 字段（String，可选）
- **D-02:** region 值从固定选项列表中选择：广州、杭州、厦门、深圳、武汉、长沙（与当前已支持的 6 个地区一致）
- **D-03:** 新增地区需后台配置，前端从 API 获取可用地区列表
- **D-04:** 批量导入时 Excel 中的 region 列映射到此字段，未填写时设为 null

### 批量导入体验 (MASTER-02)
- **D-05:** 工号重复时覆盖更新（用新数据覆盖已有记录），不跳过也不报错
- **D-06:** 批量导入完成后前端显示统计：新增数 / 更新数 / 失败数 / 总行数
- **D-07:** 失败行（如缺少必填字段）跳过并汇总展示，不中断整个导入流程

### 匹配策略 (MASTER-04)
- **D-08:** 社保数据与员工主数据采用双维度并行匹配：工号(employee_id) 和 身份证号(id_number) 任一命中即为匹配成功
- **D-09:** 未匹配的社保记录正常导入，标记为"未匹配"状态，HR 可后续手动处理
- **D-10:** 匹配结果需可追溯（记录匹配方式：工号匹配 / 身份证号匹配 / 未匹配）

### 前端完善 (MASTER-03)
- **D-11:** 员工列表页添加按地区(region)下拉筛选
- **D-12:** 员工列表页添加按公司(company_name)下拉筛选
- **D-13:** 员工列表页添加分页功能（服务端分页）
- **D-14:** 批量导入后展示导入结果反馈（新增/更新/失败统计）

### Claude's Discretion
- region 字段的数据库迁移方式
- 前端筛选组件的具体样式和布局
- 导入结果反馈的 UI 形式（弹窗 / 内嵌 / toast）
- 匹配结果记录的数据模型细节

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 员工主数据模型（现有代码）
- `backend/app/models/employee_master.py` — EmployeeMaster 模型定义（需新增 region 字段）
- `backend/app/models/employee_master_audit.py` — 员工主数据审计记录
- `backend/app/schemas/employees.py` — Pydantic schemas（需同步 region 字段）
- `backend/app/services/employee_service.py` — 完整的员工服务（683 行，CRUD/导入/匹配/搜索）

### API 端点（现有代码）
- `backend/app/api/v1/employees.py` — 员工 CRUD + 批量导入 + 自助查询端点
- `backend/app/api/v1/router.py` — 路由注册和权限配置

### 匹配服务（现有代码）
- `backend/app/services/matching_service.py` — 社保数据与员工主数据匹配逻辑

### 前端页面（现有代码）
- `frontend/src/pages/Employees.tsx` — 员工列表页
- `frontend/src/pages/EmployeeCreate.tsx` — 员工创建页
- `frontend/src/config/env.ts` — API base URL 配置

### Phase 3 审计日志（依赖）
- `backend/app/services/audit_service.py` — log_audit 函数，员工增删改操作需接入

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/employee_service.py`: 完整的 CRUD、导入、搜索功能已实现，只需补充 region 字段和调整导入逻辑
- `backend/app/services/matching_service.py`: 已有匹配框架，需确认是否支持双维度并行匹配
- `backend/app/utils/masking.py`: Phase 3 的脱敏工具，列表展示身份证号时可复用
- `backend/app/services/audit_service.py`: Phase 3 的审计服务，员工操作需接入

### Established Patterns
- API 响应统一使用 `success_response()` 封装
- 模型继承 `Base, TimestampMixin, UUIDPrimaryKeyMixin`
- 搜索用 SQLAlchemy `ilike` + `or_` 多字段模糊匹配
- 路由权限通过 `require_role("admin", "hr")` 注入

### Integration Points
- EmployeeMaster 模型新增 region 字段后，需同步 schema、service、API
- 前端 Employees.tsx 已有基础列表，需添加筛选/分页组件
- 批量导入端点已存在，需调整覆盖更新逻辑和返回结果统计

</code_context>

<specifics>
## Specific Ideas

- 地区列表与社保解析器支持的 6 个地区保持一致
- 批量导入是 HR 最频繁的操作，导入结果反馈必须清晰直观
- 匹配结果需记录匹配方式（工号/身份证号/未匹配），方便后续排查

</specifics>

<deferred>
## Deferred Ideas

None — 讨论内容全部在 Phase 4 范围内。

</deferred>

---

*Phase: 04-employee-master-data*
*Context gathered: 2026-03-28*
