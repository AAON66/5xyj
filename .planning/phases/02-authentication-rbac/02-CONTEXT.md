# Phase 2: Authentication & RBAC - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

为系统增加三角色认证与权限控制（管理员 / HR / 员工），扩展现有的双角色 HMAC 令牌系统为基于 PyJWT 的三角色体系。管理员/HR 用密码登录，员工用工号+身份证号+姓名验证后获取临时 Token。管理员可在界面上管理用户账号。

不涉及：前端 UI 重设计（Phase 7-8）、飞书 OAuth（Phase 10）、API Key（Phase 9）。本阶段只做认证基础设施和权限控制。

</domain>

<decisions>
## Implementation Decisions

### 员工验证流程
- **D-01:** 员工通过工号+身份证号+姓名验证身份，验证数据来源是员工主数据表（EmployeeMaster）
- **D-02:** 验证成功后发放临时 Token（role=employee），员工可以浏览多页、查看历史记录，无需反复验证
- **D-03:** 员工 Token 有效期 30 分钟
- **D-04:** 同一 IP 或同一工号 5 次验证失败后锁定 15 分钟（防止身份证号枚举）

### 用户管理
- **D-05:** 管理员/HR 账号存储在数据库中（新建 User 模型），密码用 bcrypt 哈希
- **D-06:** 员工不需要单独创建账号，直接通过员工主数据验证
- **D-07:** 系统首次启动时自动创建默认管理员（admin/admin），并提示修改密码
- **D-08:** 管理员可在界面上创建/编辑/禁用 HR 和管理员账号

### Token 策略
- **D-09:** 从自定义 HMAC 令牌迁移到 PyJWT（HS256 签名），保持向后兼容的 Bearer token 格式
- **D-10:** 管理员/HR Token 有效期 8 小时（一个工作日）
- **D-11:** 员工 Token 有效期 30 分钟
- **D-12:** Token payload 包含 sub（用户名或工号）、role（admin/hr/employee）、iat、exp

### 权限边界
- **D-13:** 管理员：用户管理 + 系统配置 + 所有业务功能
- **D-14:** HR：所有业务功能（上传/融合/导出/数据管理/员工主数据管理），但不能管理用户账号和系统设置
- **D-15:** 员工：仅查询个人社保公积金数据，不能看到他人数据
- **D-16:** 认证层只加在 API 路由层（dependencies.py），不改动解析/融合/导出的业务逻辑
- **D-17:** 保留现有 auth_enabled 开关，关闭后系统行为与当前完全一致

### 部署兼容
- **D-18:** 不引入新的外部服务（继续用 SQLite），部署流程不变
- **D-19:** pip install 自动安装 PyJWT + passlib[bcrypt] 依赖
- **D-20:** 首次启动自动建表 + 创建默认管理员，无需手动操作

### Claude's Discretion
- require_role 依赖注入的具体实现方式
- 密码强度验证规则
- Token 刷新机制（是否需要 refresh token）
- 数据库迁移策略（Alembic migration 细节）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有认证代码
- `backend/app/core/auth.py` — 当前 HMAC 令牌实现，AuthRole 定义，需要扩展为三角色
- `backend/app/dependencies.py` — require_authenticated_user 依赖，需要增加 require_role
- `backend/app/api/v1/auth.py` — 登录端点，需要增加员工验证端点
- `backend/app/schemas/auth.py` — Auth 相关 Pydantic schemas
- `backend/app/core/config.py` — Settings 中的 auth 相关配置

### 前端认证
- `frontend/src/components/AuthProvider.tsx` — React 认证上下文，需要适配新角色
- `frontend/src/pages/Login.tsx` — 登录页，需要增加员工验证入口
- `frontend/src/hooks/authContext.ts` — 认证 hook 定义
- `frontend/src/services/auth.ts` — 认证 API 调用服务
- `frontend/src/services/authSession.ts` — Token 本地存储

### 员工主数据
- `backend/app/models/employee_master.py` — 员工主数据模型，员工验证的数据来源
- `backend/app/services/employee_service.py` — 员工服务
- `backend/app/api/v1/employees.py` — 员工 API 路由

### 路由注册
- `backend/app/api/v1/router.py` — API 路由注册，需要为新端点添加权限保护

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/core/auth.py`: 已有完整的令牌签发/验证逻辑，只需替换 HMAC→PyJWT 并扩展角色
- `backend/app/dependencies.py`: `require_authenticated_user` 已有 Bearer token 解析，扩展为 `require_role` 即可
- `frontend/src/components/AuthProvider.tsx`: 完整的 React 认证上下文（session 管理、登录/登出、初始化），只需适配新角色
- `frontend/src/services/authSession.ts`: localStorage 会话管理，可复用

### Established Patterns
- 认证通过 FastAPI Depends 注入（HTTPBearer scheme）
- Settings 中有 `auth_enabled` 开关控制是否启用认证
- 前端通过 AuthContext + AuthProvider 管理认证状态
- API 响应统一使用 `success_response()` 封装

### Integration Points
- `backend/app/api/v1/router.py` 注册所有路由，需要为各路由添加角色保护
- `backend/app/bootstrap.py` 初始化逻辑，需要增加默认管理员自动创建
- `backend/app/core/database.py` 数据库模型注册

</code_context>

<specifics>
## Specific Ideas

- 员工验证是"三要素验证"（工号+身份证号+姓名），不是传统的用户名密码登录，需要单独的验证端点
- 管理员首次启动自动创建，提示修改密码的体验要友好
- 认证只是"门卫"，不碰融合/导出/解析的业务代码
- auth_enabled 开关保留，确保关闭后行为与当前完全一致

</specifics>

<deferred>
## Deferred Ideas

- 飞书 OAuth 登录 — Phase 10
- API Key 认证 — Phase 9
- 身份证号脱敏显示 — Phase 3（安全加固）
- 审计日志 — Phase 3（安全加固）
- 频率限制（除员工验证外的其他端点）— Phase 3

</deferred>

---

*Phase: 02-authentication-rbac*
*Context gathered: 2026-03-28*
