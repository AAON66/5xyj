# Phase 16: 账号管理 - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

管理员可完整管理系统用户（创建/修改角色/重置密码），普通用户可自主修改密码。后端 CRUD API 已基本就绪（ACCT-01/02/03），仅缺用户自改密码端点（ACCT-04）。本阶段主要工作是新建前端账号管理页面 + 补齐自改密码后端端点 + 强制改密流程。

</domain>

<decisions>
## Implementation Decisions

### 管理页面布局
- **D-01:** 在 Phase 15 已有的「管理」分组菜单中新增「账号管理」菜单项，路由 /users，admin-only
- **D-02:** 用户列表使用 Ant Design Table，操作通过 Modal 弹窗完成（新建/编辑/重置密码），与员工主档页交互模式一致
- **D-03:** 不在 Settings 页面放账号管理卡片，侧边栏菜单是唯一入口

### 用户自改密码入口
- **D-04:** 右上角 Header 用户名下拉菜单增加「修改密码」项，点击弹出 Modal。所有角色可见
- **D-05:** must_change_password 为 true 时（新用户首次登录或管理员重置密码后），登录后立即弹出不可关闭的修改密码 Modal，修改成功后才能操作系统

### 密码策略与安全
- **D-06:** 自改密码必须验证旧密码（旧密码 + 新密码 + 确认新密码三个字段）
- **D-07:** 密码强度保持现状：最少 8 位，不增加复杂度要求
- **D-08:** 需新增后端端点 PUT /api/v1/auth/change-password（验证旧密码 + 设置新密码 + 清除 must_change_password 标记）

### 角色与状态操作
- **D-09:** 创建用户时可选角色为 admin 和 hr（employee 通过三要素验证自动创建，不在此管理）
- **D-10:** 禁用/启用账号使用 Switch 开关，直接在用户列表行内切换
- **D-11:** 管理员不能禁用自己、不能修改自己的角色（前端灰色禁用 + 后端 403 双保险）

### 列表显示字段
- **D-12:** 用户列表表格列：用户名、显示名、角色（Tag）、状态（Switch）、创建时间、操作（编辑/重置密码）

### Claude's Discretion
- Modal 表单的具体布局和验证提示文案
- 用户列表的分页策略（用户数量少可能不需要分页）
- 重置密码确认对话框的具体文案
- 创建用户后是否自动生成初始密码或由管理员手动输入

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above

### 后端核心文件
- `backend/app/models/user.py` — User 模型定义（username, hashed_password, role, is_active, must_change_password 等字段）
- `backend/app/services/user_service.py` — 已有 CRUD 方法（create_user, update_user, reset_user_password, list_users 等）
- `backend/app/api/v1/users.py` — 已有管理员用户管理端点（POST/GET/PUT + 密码重置）
- `backend/app/api/v1/auth.py` — 登录/验证端点，需新增 change-password
- `backend/app/schemas/users.py` — UserCreate, UserUpdate, UserPasswordReset, UserRead schemas
- `backend/app/schemas/auth.py` — AuthLoginRequest, AuthLoginResponse schemas
- `backend/app/dependencies.py` — require_role() RBAC 依赖

### 前端核心文件
- `frontend/src/layouts/MainLayout.tsx` — 菜单定义（管理组）+ Header 用户下拉
- `frontend/src/pages/Settings.tsx` — Settings 页面卡片模式参考
- `frontend/src/pages/Login.tsx` — 密码输入 + mustChangePassword warning 参考
- `frontend/src/components/AuthProvider.tsx` — Auth 状态管理
- `frontend/src/hooks/useAuth.ts` — useAuth() hook
- `frontend/src/services/authSession.ts` — session 管理（mustChangePassword 字段已存在）
- `frontend/src/services/auth.ts` — 认证 API 客户端

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `user_service.py` — 完整的 CRUD 方法，Phase 16 后端只需新增 change-password 端点
- `require_role("admin")` — RBAC 依赖已就绪，直接用于新端点和路由保护
- `log_audit()` — 审计日志已集成到所有用户管理端点
- `AuthProvider` + `useAuth()` — 前端 auth 状态管理完备，可直接获取 session/user
- `authSession.ts` — mustChangePassword 字段已在 session 中存储
- `Login.tsx` 的 `Input.Password` + `LockOutlined` 组件 — 密码输入 UI 参考
- Ant Design `Modal`, `Form`, `Table`, `Switch`, `Tag` — 已在项目中广泛使用

### Established Patterns
- Phase 15 的 Settings 页面卡片搜索模式 — 但本阶段不用（账号管理走独立页面）
- 员工主档页面的 Table + Modal CRUD 模式 — 本阶段复用此模式
- localStorage 持久化模式（theme-mode, menu-open-keys）— 不涉及本阶段

### Integration Points
- `MainLayout.tsx` GROUP-ADMIN 数组需新增「账号管理」菜单项
- `MainLayout.tsx` Header 用户下拉菜单需新增「修改密码」项
- `App.tsx` 需添加 /users 路由（admin-only）
- `AuthProvider.tsx` 或 `MainLayout.tsx` 需处理 mustChangePassword 强制弹窗逻辑

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-account-management*
*Context gathered: 2026-04-07*
