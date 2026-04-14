---
phase: 16-account-management
plan: 02
subsystem: ui
tags: [react, antd, modal, crud, rbac, password]

requires:
  - phase: 16-account-management plan 01
    provides: backend user CRUD API + change-password API + /auth/me must_change_password

provides:
  - Users.tsx 账号管理页面 (Table + Modal CRUD)
  - users.ts API 客户端 (fetchUsers, createUser, updateUser, resetUserPassword)
  - ChangePasswordModal 共用组件 (forced/voluntary modes)
  - MainLayout 集成 (菜单+Header 修改密码+强制改密拦截)
  - /users 路由注册 (admin-only)

affects: []

tech-stack:
  added: []
  patterns:
    - "ChangePasswordModal forced/voluntary dual-mode pattern"
    - "writeAuthSession -> AUTH_SESSION_EVENT -> AuthProvider sync for mustChangePassword"
    - "currentUserId derived from user list match by username"

key-files:
  created:
    - frontend/src/services/users.ts
    - frontend/src/pages/Users.tsx
    - frontend/src/components/ChangePasswordModal.tsx
  modified:
    - frontend/src/services/auth.ts
    - frontend/src/layouts/MainLayout.tsx
    - frontend/src/App.tsx
    - frontend/src/pages/index.ts

key-decisions:
  - "Used UserOutlined icon for account management menu (TeamOutlined already used for employees)"
  - "currentUserId derived by matching username from user list rather than adding id to AuthSession"
  - "employee role filtered from change password menu using role !== 'employee' check"

patterns-established:
  - "ChangePasswordModal: shared component with forced (closable=false) and voluntary modes"
  - "Session sync: writeAuthSession inside modal -> AUTH_SESSION_EVENT -> AuthProvider auto-sync"

requirements-completed: [ACCT-01, ACCT-02, ACCT-03, ACCT-04]

duration: 4min
completed: 2026-04-07
---

# Phase 16 Plan 02: Frontend Account Management Summary

**Ant Design Table+Modal CRUD 账号管理页面 + 双模式修改密码弹窗 + 强制改密拦截 + employee 角色隔离**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-07T08:19:26Z
- **Completed:** 2026-04-07T08:23:46Z
- **Tasks:** 2 completed (Task 3 is checkpoint:human-verify, returned to orchestrator)
- **Files modified:** 7

## Accomplishments
- Users.tsx 完整 CRUD 页面：列表 Table + 创建/编辑 Modal + Switch 状态切换 + Popconfirm+Modal 重置密码
- admin 自我保护：Switch disabled + Select disabled 防止禁用自己或改自己角色
- 409/403 错误 form-level 处理（用户名重复在表单字段下方提示）
- ChangePasswordModal 支持强制模式（closable=false, maskClosable=false）和自主模式
- MainLayout 集成：管理菜单 + Header 修改密码（仅 admin/hr）+ mustChangePassword 强制拦截
- employee 角色不显示修改密码菜单项

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建用户管理 API 客户端 + 账号管理页面** - `125807c` (feat)
2. **Task 2: ChangePasswordModal 组件 + MainLayout 集成 + 路由注册** - `b251e50` (feat)

## Files Created/Modified
- `frontend/src/services/users.ts` - 用户管理 API 客户端（fetchUsers, createUser, updateUser, resetUserPassword）
- `frontend/src/services/auth.ts` - 新增 changeOwnPassword 函数
- `frontend/src/pages/Users.tsx` - 账号管理页面（Table + 3 个 Modal）
- `frontend/src/components/ChangePasswordModal.tsx` - 共用修改密码弹窗（强制/自主双模式）
- `frontend/src/layouts/MainLayout.tsx` - 菜单新增账号管理 + Header 修改密码 + 强制改密拦截
- `frontend/src/App.tsx` - /users 路由注册（admin-only RoleRoute）
- `frontend/src/pages/index.ts` - 导出 UsersPage

## Decisions Made
- 使用 UserOutlined 图标而非 TeamOutlined（后者已用于员工主档）
- currentUserId 通过用户列表匹配 username 获取，而非修改 AuthSession 添加 id 字段
- employee 角色过滤使用 `user.role !== 'employee'` 条件判断

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed lint error: unused variable `_` in table render**
- **Found during:** Task 2 (verification step)
- **Issue:** `_: unknown` parameter in table render column triggered @typescript-eslint/no-unused-vars
- **Fix:** Renamed to `_value` to satisfy lint rule
- **Files modified:** frontend/src/pages/Users.tsx
- **Verification:** npm run lint passes
- **Committed in:** b251e50 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial naming fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Task 3 (checkpoint:human-verify) 需要人工验证 7 个场景
- 前后端均需启动后进行完整功能验证

---
*Phase: 16-account-management*
*Completed: 2026-04-07*
