# Phase 9: API System - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

将现有内部 API 形式化为对外 REST API 体系，新增 API Key 认证机制供外部程序调用。所有核心功能通过统一的 /api/v1/ 端点对外开放，响应格式规范化，API 文档中文化并仅管理员可见。

</domain>

<decisions>
## Implementation Decisions

### API Key 认证设计
- **D-01:** API Key 绑定到具体用户（admin/HR），继承该用户的角色权限，审计日志可追溯到具体用户
- **D-02:** API Key 永不过期，管理员可手动禁用或删除
- **D-03:** 每个用户最多创建 5 个 API Key
- **D-04:** API Key 通过请求头 `X-API-Key` 传递
- **D-05:** 只有管理员（admin）角色可以创建和管理 API Key

### API 版本与路由结构
- **D-06:** 外部 API 和前端内部 API 共用同一套 `/api/v1/` 端点，仅认证方式不同（JWT vs API Key）
- **D-07:** 所有现有功能对 API Key 开放，涉密功能（用户管理、审计日志等）仅管理员 API Key 可访问
- **D-08:** 后端 dependencies 层统一处理 JWT 和 API Key 两种认证方式，对业务层透明

### 响应格式规范化
- **D-09:** 保持现有 `{success, message, data}` / `{success, error: {code, message}}` 结构不变
- **D-10:** 列表接口在响应中增加 pagination 字段：`{total, page, page_size}`
- **D-11:** 建立统一错误码前缀体系，按模块分类：AUTH_xxx, IMPORT_xxx, EMPLOYEE_xxx, EXPORT_xxx, SYSTEM_xxx

### API 文档定制
- **D-12:** 所有端点、参数、模型加中文 description/summary
- **D-13:** 端点按功能分组标签（社保查询、员工管理、导入导出、认证、系统管理）
- **D-14:** 关键端点提供请求/响应示例值（FastAPI example schema）
- **D-15:** 纯内部端点（如系统配置）在 Swagger 文档中隐藏（`include_in_schema=False`）
- **D-16:** /docs 仅管理员角色登录后可访问
- **D-17:** 额外生成 Markdown 格式的 API 文档文件
- **D-18:** 提供一个 API 端点（如 GET /api/v1/docs/markdown）返回 API 文档内容

### Claude's Discretion
- API Key 的具体生成算法和长度（推荐 32-64 字符随机字符串）
- API Key 在数据库中的存储方式（明文 vs 哈希，推荐哈希存储仅展示一次）
- 分页参数的默认值和最大值
- 错误码编号规则的具体细节
- Markdown 文档的具体格式和章节结构

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有 API 架构
- `backend/app/api/v1/router.py` — 当前路由注册和角色权限配置，Phase 9 需在此基础上支持双认证
- `backend/app/api/v1/responses.py` — 现有统一响应格式（success_response / error_response），需扩展分页支持
- `backend/app/dependencies.py` — 当前 require_role / require_authenticated_user 依赖注入，需扩展支持 API Key

### 认证体系
- `backend/app/core/auth.py` — JWT 认证逻辑，API Key 认证需与其并行
- `backend/app/api/v1/auth.py` — 登录端点，API Key 管理端点需加在此处或新建模块
- `backend/app/models/user.py` — 用户模型，API Key 需关联到用户

### 数据模型
- `backend/app/models/` — 所有 SQLAlchemy 模型，需新增 ApiKey 模型
- `backend/app/schemas/` — 所有 Pydantic schema，需新增 API Key 相关 schema

### FastAPI 文档
- `backend/app/main.py` — FastAPI app 初始化，/docs 路由配置在此

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `responses.py`: 已有 `success_response` / `error_response` 统一响应函数，扩展分页字段即可
- `dependencies.py`: 已有 `require_role` / `require_authenticated_user`，可扩展为同时支持 JWT 和 API Key
- `router.py`: 已有完整的路由注册结构和角色权限配置
- `models/audit_log.py`: 已有审计日志模型，API Key 操作可复用

### Established Patterns
- 路由层使用 `dependencies=[Depends(require_role(...))]` 做权限控制
- Schema 层使用 Pydantic BaseModel 做输入验证和输出序列化
- 服务层抛自定义异常，API 层捕获并返回统一错误响应

### Integration Points
- `dependencies.py` — API Key 认证逻辑需在此新增，与现有 JWT 认证并行
- `router.py` — 所有路由已注册，无需新增路由前缀
- `main.py` — /docs 访问控制需在 FastAPI app 层面配置
- 审计日志 — API Key 的创建、使用、禁用需记录审计日志

</code_context>

<specifics>
## Specific Ideas

- 用户要求 API 文档同时有 Swagger UI 和 Markdown 两种形式
- 需要一个 API 端点直接返回文档内容（GET /api/v1/docs/markdown）
- 涉密功能的定义：用户管理、审计日志等管理类功能仅管理员 API Key 可访问
- API Key 只有管理员能设置和管理，HR 用户也可以拥有 API Key 但不能自己创建

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-api-system*
*Context gathered: 2026-03-31*
