---
phase: 16-account-management
verified: 2026-04-07T09:00:00Z
status: human_needed
score: 4/4 must-haves verified
human_verification:
  - test: "管理员账号管理页面 CRUD 流程"
    expected: "admin 登录后可见账号管理菜单，点击进入 /users，创建/编辑/禁用用户均正常工作"
    why_human: "需要启动前后端并在浏览器中操作验证完整 CRUD 交互"
  - test: "管理员自我保护 UI 禁用态"
    expected: "当前管理员行的 Switch 灰色禁用，编辑自己时角色 Select 灰色禁用"
    why_human: "需要浏览器验证 disabled 视觉状态"
  - test: "强制改密弹窗不可关闭 + 刷新持久化"
    expected: "mustChangePassword=true 用户登录后弹出不可关闭 Modal，F5 刷新后 Modal 仍在，改密后消失"
    why_human: "需要真实浏览器测试 Modal 交互和页面刷新行为"
  - test: "employee 角色不显示修改密码菜单"
    expected: "员工三要素登录后 Header 下拉无修改密码选项"
    why_human: "需要 employee 角色真实登录验证 UI 条件渲染"
  - test: "旧密码错误时 form-level 错误提示"
    expected: "输入错误旧密码后当前密码字段下方显示红色错误文字（非 toast）"
    why_human: "需要浏览器验证表单错误 UI 显示方式"
---

# Phase 16: 账号管理 Verification Report

**Phase Goal:** 管理员可完整管理系统用户，用户可自主维护密码
**Verified:** 2026-04-07T09:00:00Z
**Status:** human_needed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 管理员可在账号管理页面创建新用户并分配角色 | VERIFIED | `Users.tsx` 包含完整 createUser Modal + createForm + ROLE_OPTIONS (admin/hr) + fetchUsers 列表刷新；`users.ts` 包含 createUser API 调用 `POST /users/`；`App.tsx` 路由 `/users` 注册在 admin-only RoleRoute 内 |
| 2 | 管理员可修改已有用户的角色权限 | VERIFIED | `Users.tsx` 包含 editModal + updateUser 调用 + editingUser 状态管理 + 角色 Select 组件 |
| 3 | 管理员可为用户重置密码 | VERIFIED | `Users.tsx` 包含 Popconfirm 确认 + resetPasswordModal + resetUserPassword API 调用；后端 `reset_user_password` 设置 `must_change_password=True`（line 107） |
| 4 | 普通用户可在个人设置中修改自己的密码 | VERIFIED | `ChangePasswordModal.tsx` 完整实现（changeOwnPassword API + form 验证 + writeAuthSession 同步）；`MainLayout.tsx` Header 下拉菜单包含修改密码项（admin/hr only）；后端 `PUT /auth/change-password` 端点验证旧密码后设新密码 |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/schemas/auth.py` | ChangePasswordRequest schema | VERIFIED | 含 `class ChangePasswordRequest(BaseModel)` with old_password (min 1) + new_password (min 8) |
| `backend/app/services/user_service.py` | change_own_password + must_change_password fixes | VERIFIED | `change_own_password` (line 113)、`create_user` 设 `must_change_password=True` (line 68)、`reset_user_password` 设 `must_change_password=True` (line 107) |
| `backend/app/api/v1/auth.py` | change-password endpoint + fixed /me | VERIFIED | `PUT /change-password` (line 140) with employee 403 (line 148)、`GET /me` 从 DB 读取 must_change_password (line 178) |
| `backend/app/api/v1/users.py` | admin self-protection | VERIFIED | "Cannot disable your own account" (line 80)、"Cannot change your own role" (line 82)、"Cannot reset your own password" (line 114) |
| `tests/test_users.py` | TestChangePassword + TestAuthMe + TestSelfProtection | VERIFIED | 28 tests all passing: TestChangePassword (6)、TestAuthMe (3)、TestSelfProtection (4) + 其他 |
| `frontend/src/services/users.ts` | User API client | VERIFIED | fetchUsers, createUser, updateUser, resetUserPassword 四个函数均存在 |
| `frontend/src/services/auth.ts` | changeOwnPassword | VERIFIED | `export async function changeOwnPassword` (line 66) 调用 `PUT /auth/change-password` |
| `frontend/src/pages/Users.tsx` | 账号管理 CRUD 页面 | VERIFIED | 459 行，包含 Table + 3 个 Modal + Switch + Popconfirm + 409 错误处理 |
| `frontend/src/components/ChangePasswordModal.tsx` | 双模式修改密码弹窗 | VERIFIED | 130 行，forced 模式 closable={!forced} maskClosable={!forced}、writeAuthSession 同步、form-level 400 错误处理 |
| `frontend/src/layouts/MainLayout.tsx` | 菜单 + Header + 强制改密 | VERIFIED | 账号管理菜单项 (line 102)、修改密码菜单 (line 415-419)、employee 角色过滤 (line 415)、mustChangePassword 强制弹窗 (line 531-532) |
| `frontend/src/App.tsx` | /users 路由 | VERIFIED | `<Route path="/users" element={<UsersPage />} />` (line 145) within admin RoleRoute |
| `frontend/src/pages/index.ts` | UsersPage 导出 | VERIFIED | `export { UsersPage } from './Users'` (line 24) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| auth.py (API) | user_service.py | change_own_password | WIRED | Line 151: `change_own_password(db, current_user.username, ...)` |
| auth.py (API) | schemas/auth.py | ChangePasswordRequest | WIRED | Line 14: import, Line 143: parameter type |
| auth.py (API) | user_service.py | get_user_by_username in /me | WIRED | Line 20: import, Line 172: DB lookup in /me |
| Users.tsx | users.ts | API calls | WIRED | Lines 23-26: imports, Lines 94/111/132/168/200: function calls |
| MainLayout.tsx | ChangePasswordModal.tsx | component import | WIRED | Line 48: import, Lines 524+532: two instances rendered |
| ChangePasswordModal.tsx | auth.ts | changeOwnPassword | WIRED | Line 6: import, Line 30: API call |
| ChangePasswordModal.tsx | authSession.ts | writeAuthSession | WIRED | Line 7: import, Line 38: session sync call |
| App.tsx | Users.tsx | route registration | WIRED | Line 32: import UsersPage, Line 145: `/users` route |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| Users.tsx | users state | fetchUsers -> GET /users/ | Yes -- backend list_users queries DB via SQLAlchemy | FLOWING |
| ChangePasswordModal.tsx | form values | User input + changeOwnPassword API | Yes -- PUT /auth/change-password writes to DB | FLOWING |
| MainLayout.tsx | mustChangePassword | user from AuthProvider -> readAuthSession -> /auth/me | Yes -- /auth/me reads from DB (line 178 of auth.py) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend tests pass | `python3 -m pytest tests/test_users.py -x -q` | 28 passed, 1 warning | PASS |
| TypeScript compiles | `npx tsc --noEmit` | No errors | PASS |
| Commits verified | `git log --oneline 79fdfae..b251e50` | All 6 commits found | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ACCT-01 | 16-02 | 管理员可创建新用户账号 | SATISFIED | Users.tsx createModal + createUser API + 后端 create_user (must_change_password=True) |
| ACCT-02 | 16-02 | 管理员可修改用户角色权限 | SATISFIED | Users.tsx editModal + updateUser API + role Select + self-protection |
| ACCT-03 | 16-01, 16-02 | 管理员可重置用户密码 | SATISFIED | Users.tsx resetPassword flow + 后端 reset_user_password (must_change_password=True) + self-protection |
| ACCT-04 | 16-01, 16-02 | 用户可修改自己的密码 | SATISFIED | ChangePasswordModal + changeOwnPassword API + 后端 change-password endpoint + employee 403 |

No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| ChangePasswordModal.tsx | 78 | `footer={forced ? undefined : undefined}` -- 两个分支结果相同，无实际效果 | Info | 不影响功能，footer 默认行为正确（forced 时 cancelButtonProps 隐藏取消按钮），可能是作者意图通过 forced 分支自定义 footer 但最终未实现 |

### Human Verification Required

### 1. 管理员 CRUD 完整流程

**Test:** admin 登录后进入 /users，创建 hr 用户（用户名/密码/角色），编辑显示名，禁用用户
**Expected:** 所有操作成功，列表实时刷新
**Why human:** 需要真实浏览器完成多步 UI 交互

### 2. 管理员自我保护 UI 禁用态

**Test:** 当前管理员在用户列表中，Switch 灰色不可点击；编辑自己时角色 Select 灰色不可选
**Expected:** `disabled` 视觉状态正确渲染
**Why human:** 需要浏览器验证 Ant Design disabled 组件视觉状态

### 3. 强制改密 + 刷新持久化

**Test:** 重置 hr 用户密码后用该用户登录，弹出不可关闭 Modal，F5 刷新后 Modal 仍在，改密后消失
**Expected:** Modal closable=false 生效，刷新后 /auth/me 返回 must_change_password=true 使 Modal 重现
**Why human:** 需要真实浏览器验证 Modal 不可关闭属性和页面刷新后状态恢复

### 4. employee 角色隔离

**Test:** 员工三要素登录后查看 Header 下拉菜单
**Expected:** 无修改密码选项
**Why human:** 需要 employee 角色真实登录验证条件渲染

### 5. 旧密码错误 form-level 提示

**Test:** 修改密码时输入错误旧密码提交
**Expected:** 当前密码字段下方出现红色错误文字"当前密码错误，请重新输入"而非 toast
**Why human:** 需要验证 form-level 错误提示的视觉表现

### Gaps Summary

无代码级 gap。所有后端 API 端点已实现并通过 28 个测试；所有前端组件已创建且 TypeScript 编译通过；路由、菜单、Modal 均已正确连接。唯一需要人工验证的是浏览器中的完整交互流程（5 个场景），包括 UI 禁用态、强制改密弹窗不可关闭、页面刷新后状态持久化等无法通过静态分析确认的行为。

---

_Verified: 2026-04-07T09:00:00Z_
_Verifier: Claude (gsd-verifier)_
