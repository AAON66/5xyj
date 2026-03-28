# Phase 3: Security Hardening - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

确保所有含 PII 数据的端点受认证保护，添加审计日志记录关键操作，身份证号在非导出场景下脱敏显示。不涉及新功能开发，纯安全加固。

</domain>

<decisions>
## Implementation Decisions

### 端点认证保护 (SEC-01)
- **D-01:** Phase 2 已为所有路由添加 require_role，此阶段查漏补缺确认无遗漏
- **D-02:** auth_enabled=false 时所有保护跳过（开发模式兼容）

### 频率限制 (SEC-02)
- **D-03:** 员工验证端点已有频率限制（Phase 2 实现：5次/15分钟锁定）
- **D-04:** 登录端点也应添加频率限制（同一 IP 或用户名 5次失败/15分钟锁定）

### 审计日志 (SEC-03)
- **D-05:** 记录范围：登录/登出、数据导出、数据导入/融合、用户管理（创建/编辑/禁用）
- **D-06:** 管理员可在系统界面查看审计日志，支持按时间和操作类型筛选
- **D-07:** 日志存储在数据库（新建 AuditLog 模型），包含：操作类型、操作人、时间、IP、详情
- **D-08:** 日志只读，不可删除和修改

### 身份证号脱敏 (SEC-04)
- **D-09:** 脱敏规则：显示前3后4，中间用 * 替代（例：310***1234）
- **D-10:** 导出 Excel 时显示完整身份证号（导出是为了做账，需要完整数据）
- **D-11:** 管理员和 HR 在系统界面看到完整身份证号，员工看到脱敏版本
- **D-12:** 脱敏在 API 响应层处理，不改变数据库存储

### Claude's Discretion
- AuditLog 模型具体字段设计
- 审计日志界面的分页和筛选实现方式
- 脱敏函数的具体实现位置（schema 层 vs middleware 层）
- 登录频率限制是否复用 Phase 2 的 rate_limiter

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 2 认证代码（依赖）
- `backend/app/core/auth.py` — PyJWT 令牌，AuthRole 定义
- `backend/app/dependencies.py` — require_role RBAC 依赖
- `backend/app/api/v1/router.py` — 所有路由的 require_role 配置
- `backend/app/services/rate_limiter.py` — 已有的频率限制器（可复用）

### 需要加审计日志的模块
- `backend/app/api/v1/auth.py` — 登录/员工验证端点
- `backend/app/api/v1/aggregate.py` — 融合/导入端点
- `backend/app/api/v1/users.py` — 用户管理端点
- `backend/app/services/batch_export_service.py` — 导出服务

### 需要加脱敏的模块
- `backend/app/schemas/` — API 响应 schemas（脱敏在序列化层处理）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/rate_limiter.py`: 线程安全的内存频率限制器，可复用于登录端点
- `backend/app/dependencies.py`: require_role 工厂，可扩展为审计感知版本

### Established Patterns
- API 响应统一使用 `success_response()` 封装
- 数据库模型继承 `Base, TimestampMixin, UUIDPrimaryKeyMixin`
- 路由权限通过 FastAPI Depends 注入

### Integration Points
- 审计日志可通过 FastAPI middleware 或 service 层注入
- 脱敏可在 Pydantic schema 的 validator/serializer 中处理

</code_context>

<specifics>
## Specific Ideas

- 审计日志应记录足够信息用于事后追溯，但不需要记录完整的请求/响应体
- 身份证脱敏是 API 层行为，数据库始终存完整号码
- 导出是业务刚需，必须保留完整身份证号

</specifics>

<deferred>
## Deferred Ideas

None — 讨论内容全部在 Phase 3 范围内。

</deferred>

---

*Phase: 03-security-hardening*
*Context gathered: 2026-03-28*
