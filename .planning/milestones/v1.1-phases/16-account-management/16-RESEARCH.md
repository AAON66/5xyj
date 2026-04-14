# Phase 16: 账号管理 - Research

**Researched:** 2026-04-07
**Domain:** 用户 CRUD 管理 + 自改密码 + 强制改密流程（React + FastAPI）
**Confidence:** HIGH

## Summary

Phase 16 是一个前端重心的阶段。后端 CRUD API（创建/列表/更新/重置密码）已完整实现于 `backend/app/api/v1/users.py`，通过 `require_role("admin")` 保护，审计日志已集成。唯一缺失的后端端点是用户自改密码 `PUT /api/v1/auth/change-password`。

前端需要新建一个完整的账号管理页面（Table + Modal 模式），以及在 Header 用户下拉菜单中添加「修改密码」入口。另一个关键功能是 `mustChangePassword` 强制改密弹窗：当新用户首次登录或管理员重置密码后，系统必须弹出不可关闭的改密 Modal。

**关键发现：** 当前 `reset_user_password()` 将 `must_change_password` 设为 `False`，这与 D-05 决策矛盾。需改为 `True` 以触发强制改密流程。

**Primary recommendation:** 先修复后端 `reset_user_password` 的 `must_change_password` 标记并新增 `change-password` 端点，再构建前端页面和强制改密逻辑。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 在 Phase 15 已有的「管理」分组菜单中新增「账号管理」菜单项，路由 /users，admin-only
- **D-02:** 用户列表使用 Ant Design Table，操作通过 Modal 弹窗完成（新建/编辑/重置密码），与员工主档页交互模式一致
- **D-03:** 不在 Settings 页面放账号管理卡片，侧边栏菜单是唯一入口
- **D-04:** 右上角 Header 用户名下拉菜单增加「修改密码」项，点击弹出 Modal。所有角色可见
- **D-05:** must_change_password 为 true 时（新用户首次登录或管理员重置密码后），登录后立即弹出不可关闭的修改密码 Modal，修改成功后才能操作系统
- **D-06:** 自改密码必须验证旧密码（旧密码 + 新密码 + 确认新密码三个字段）
- **D-07:** 密码强度保持现状：最少 8 位，不增加复杂度要求
- **D-08:** 需新增后端端点 PUT /api/v1/auth/change-password（验证旧密码 + 设置新密码 + 清除 must_change_password 标记）
- **D-09:** 创建用户时可选角色为 admin 和 hr（employee 通过三要素验证自动创建，不在此管理）
- **D-10:** 禁用/启用账号使用 Switch 开关，直接在用户列表行内切换
- **D-11:** 管理员不能禁用自己、不能修改自己的角色（前端灰色禁用 + 后端 403 双保险）
- **D-12:** 用户列表表格列：用户名、显示名、角色（Tag）、状态（Switch）、创建时间、操作（编辑/重置密码）

### Claude's Discretion
- Modal 表单的具体布局和验证提示文案
- 用户列表的分页策略（用户数量少可能不需要分页）
- 重置密码确认对话框的具体文案
- 创建用户后是否自动生成初始密码或由管理员手动输入

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ACCT-01 | 管理员可创建新用户账号 | 后端 `POST /api/v1/users/` 已实现，前端需建 Modal 表单调用 |
| ACCT-02 | 管理员可修改用户角色权限 | 后端 `PUT /api/v1/users/{id}` 已支持 role 更新，需加 D-11 自我保护 |
| ACCT-03 | 管理员可重置用户密码 | 后端 `PUT /api/v1/users/{id}/password` 已实现，需修复 `must_change_password` 为 True |
| ACCT-04 | 用户可修改自己的密码 | 需新增 `PUT /api/v1/auth/change-password` 端点 + 前端 Modal |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Ant Design | 5.x (已安装) | Table, Modal, Form, Switch, Tag, Input.Password | 项目统一 UI 库 |
| React Router | 6.x (已安装) | /users 路由注册 | 项目路由方案 |
| FastAPI | 已安装 | 新增 change-password 端点 | 项目后端框架 |
| pwdlib + bcrypt | 已安装 | 密码哈希与验证 | user_service.py 已使用 |

[VERIFIED: codebase grep -- 所有库已在项目中使用]

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| axios (apiClient) | 已安装 | 前端 API 请求 | 所有 API 调用 |
| Pydantic | 已安装 | Schema 验证（ChangePasswordRequest） | 新增后端 schema |

**Installation:** 无需安装新依赖，所有所需库已在项目中。

## Architecture Patterns

### 后端新增端点结构
```
backend/app/
├── api/v1/auth.py           # 新增 PUT /auth/change-password
├── schemas/auth.py          # 新增 ChangePasswordRequest schema
├── services/user_service.py # 修复 reset_user_password + 新增 change_own_password
└── dependencies.py          # require_authenticated_user 已就绪
```

### 前端新增文件结构
```
frontend/src/
├── pages/
│   └── Users.tsx            # 新建：账号管理页面（Table + Modal CRUD）
├── services/
│   └── users.ts             # 新建：用户管理 API 客户端
├── components/
│   └── ChangePasswordModal.tsx  # 新建：修改密码 Modal（Header + 强制改密共用）
├── layouts/
│   └── MainLayout.tsx       # 修改：菜单增加「账号管理」+ Header 增加「修改密码」
├── App.tsx                  # 修改：增加 /users 路由
└── pages/index.ts           # 修改：导出 UsersPage
```

[VERIFIED: 基于 codebase 现有文件结构推导]

### Pattern 1: Table + Modal CRUD（复用员工主档模式）
**What:** 列表用 AntD Table 展示，创建/编辑/重置密码用 Modal 弹窗
**When to use:** 所有管理型 CRUD 页面
**Example:**
```typescript
// Source: frontend/src/pages/Employees.tsx（项目已有模式）
// 1. Table columns 定义含 render 函数
// 2. Modal 用 Form + Form.Item 控制
// 3. 操作按钮在表格 action 列
// 4. 用 message.success/error 反馈
```

### Pattern 2: 行内 Switch 切换状态
**What:** 用户状态用 Switch 组件直接在表格行内切换，无需弹窗
**When to use:** 布尔状态快速切换
**Example:**
```typescript
// D-10: Switch 直接调用 PUT /users/{id} 更新 is_active
<Switch
  checked={record.is_active}
  disabled={record.id === currentUser.id}  // D-11: 不能禁用自己
  onChange={(checked) => handleToggleActive(record.id, checked)}
/>
```

### Pattern 3: 强制改密拦截
**What:** 登录后检查 `mustChangePassword`，若为 true 则弹出不可关闭 Modal
**When to use:** 新用户首次登录 / 管理员重置密码后
**Example:**
```typescript
// 在 MainLayout 或 AuthProvider 中检查
// mustChangePassword 已在 AuthSession 和 AuthenticatedUser 中定义
if (user?.mustChangePassword) {
  // 渲染 closable=false 的 ChangePasswordModal
  // maskClosable=false, keyboard=false, footer 只有提交按钮
}
```

### Anti-Patterns to Avoid
- **不要在 Settings 页面放账号管理入口** -- D-03 明确排除
- **不要跳过后端验证自我操作** -- D-11 要求前端灰色禁用 + 后端 403 双保险
- **不要在 change-password 中跳过旧密码验证** -- D-06 要求必须验证旧密码

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 密码哈希 | 自定义哈希 | `pwdlib` + `BcryptHasher`（已用） | 安全标准，已集成 |
| 表单验证 | 手动校验 | AntD Form.Item rules + Pydantic | 统一验证模式 |
| 请求认证 | 手动 token 处理 | `apiClient` 拦截器（已有） | 统一 auth header 注入 |
| RBAC 保护 | 自定义中间件 | `require_role("admin")`（已有） | 已验证的依赖注入 |

## Common Pitfalls

### Pitfall 1: reset_user_password 未设置 must_change_password = True
**What goes wrong:** 管理员重置密码后，用户不会被强制改密
**Why it happens:** 当前 `user_service.py` line 107 将 `must_change_password` 设为 `False`
**How to avoid:** 修改 `reset_user_password` 将 `must_change_password` 改为 `True`
**Warning signs:** 重置密码后用户直接可以操作系统，无改密提示

### Pitfall 2: 管理员自我操作保护缺失
**What goes wrong:** 管理员禁用自己的账号后无法登录
**Why it happens:** 后端 `update_user` 没有自我操作限制
**How to avoid:** 后端 `PUT /users/{id}` 和 `PUT /users/{id}/password` 检查 `current_user.username == target_user.username`，禁止自我禁用和自我角色修改（返回 403）
**Warning signs:** 管理员在 UI 上能点击自己的 Switch 或角色下拉

### Pitfall 3: 强制改密 Modal 可被绕过
**What goes wrong:** 用户通过直接输入 URL 或刷新页面绕过改密弹窗
**Why it happens:** Modal 只在某个组件首次渲染时显示
**How to avoid:** 在 MainLayout 级别（而非页面级别）持续检查 `user.mustChangePassword`，确保每次渲染都拦截
**Warning signs:** 用户刷新页面后改密弹窗消失

### Pitfall 4: change-password 成功后前端 session 未更新
**What goes wrong:** 改密成功后 `mustChangePassword` 仍为 true，弹窗重复出现
**Why it happens:** 只调了 API 但没更新 localStorage 中的 session
**How to avoid:** 改密成功后更新 `AuthSession.mustChangePassword = false` 并调用 `writeAuthSession()`
**Warning signs:** 改密成功后弹窗不消失或刷新页面后再次出现

### Pitfall 5: 创建用户时 must_change_password 默认为 False
**What goes wrong:** 新建用户首次登录不会被强制改密
**Why it happens:** `create_user` 中 `must_change_password=False`（line 68）
**How to avoid:** 新建用户时设置 `must_change_password=True`
**Warning signs:** 新用户登录后直接进入系统，无改密提示

## Code Examples

### 后端: ChangePasswordRequest Schema
```python
# Source: 基于现有 backend/app/schemas/auth.py 模式
class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
```
[VERIFIED: 遵循项目已有 Pydantic schema 模式]

### 后端: change-password 端点
```python
# Source: 基于现有 backend/app/api/v1/auth.py 模式
@router.put('/change-password', summary="修改密码")
def change_password_endpoint(
    request: Request,
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_authenticated_user),
):
    user = get_user_by_username(db, current_user.username)
    if not verify_password(body.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect.")
    user.hashed_password = hash_password(body.new_password)
    user.must_change_password = False
    db.commit()
    log_audit(db, action="change_password", ...)
    return success_response({"message": "Password changed successfully."})
```
[VERIFIED: 遵循项目已有端点模式]

### 前端: 用户管理 API 客户端
```typescript
// Source: 基于现有 frontend/src/services/employees.ts 模式
import { apiClient, type ApiSuccessResponse } from './api';

export interface UserItem {
  id: string;
  username: string;
  role: 'admin' | 'hr';
  display_name: string;
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
  updated_at: string;
}

export async function fetchUsers(): Promise<UserItem[]> {
  const resp = await apiClient.get<ApiSuccessResponse<UserItem[]>>('/users/');
  return resp.data.data;
}

export async function createUser(input: CreateUserInput): Promise<UserItem> { ... }
export async function updateUser(id: string, input: UpdateUserInput): Promise<UserItem> { ... }
export async function resetUserPassword(id: string, newPassword: string): Promise<void> { ... }
export async function changeOwnPassword(oldPassword: string, newPassword: string): Promise<void> { ... }
```
[VERIFIED: 遵循项目 apiClient 和 ApiSuccessResponse 模式]

### 前端: ChangePasswordModal 共用组件
```typescript
// 强制改密 (mustChangePassword) 和自主改密 (Header 菜单) 共用此组件
// 区别: forced 模式下 closable=false, maskClosable=false, keyboard=false
interface ChangePasswordModalProps {
  open: boolean;
  forced?: boolean;  // true = 不可关闭
  onSuccess: () => void;
  onCancel?: () => void;
}
```
[ASSUMED: 基于 D-04/D-05 推导的组件设计]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (已配置) |
| Config file | tests/conftest.py |
| Quick run command | `pytest tests/test_users.py -x` |
| Full suite command | `pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ACCT-01 | 管理员创建用户 | unit | `pytest tests/test_users.py::TestCreateUser -x` | YES |
| ACCT-02 | 管理员修改角色 | unit | `pytest tests/test_users.py::TestUpdateUser -x` | YES (部分) |
| ACCT-03 | 管理员重置密码 + must_change_password=True | unit | `pytest tests/test_users.py::TestResetPassword -x` | YES (需扩展) |
| ACCT-04 | 用户自改密码 | unit | `pytest tests/test_users.py::TestChangePassword -x` | NO -- Wave 0 |
| D-11 | 管理员自我保护 | unit | `pytest tests/test_users.py::TestSelfProtection -x` | NO -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_users.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_users.py::TestChangePassword` -- 用户自改密码端点测试（ACCT-04）
- [ ] `tests/test_users.py::TestSelfProtection` -- 管理员不能禁用/改角色自己（D-11）
- [ ] `tests/test_users.py::TestResetPassword` 扩展 -- 验证 must_change_password 设为 True
- [ ] 前端: `npm run lint && npm run build` -- 编译检查

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | pwdlib/bcrypt (已用), min 8 chars (D-07) |
| V3 Session Management | yes | JWT + localStorage (已有), 改密后清 mustChangePassword |
| V4 Access Control | yes | require_role("admin") + D-11 自我保护 |
| V5 Input Validation | yes | Pydantic schema + AntD Form rules |
| V6 Cryptography | no | 不涉及新加密需求 |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| 管理员自我禁用导致系统锁死 | Denial of Service | D-11 前端禁用 + 后端 403 双保险 |
| 旧密码暴力破解 | Tampering | 复用已有 RateLimiter（可选） |
| 改密后 token 仍有效 | Elevation | 当前 JWT 无法吊销 -- 可接受（短 TTL） |
| XSS 通过 display_name | Tampering | AntD 自动转义 + 后端 max_length 限制 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 新建用户应设置 must_change_password=True | Pitfalls | 新用户首次登录不会被强制改密 |
| A2 | ChangePasswordModal 作为共用组件（forced/voluntary）| Code Examples | 如果分两个组件会有代码重复但无功能影响 |
| A3 | 管理员创建用户时由管理员手动输入初始密码 | Discretion | 如果自动生成需额外 UI 显示生成的密码 |

## Open Questions

1. **创建用户初始密码策略**
   - What we know: D-09 规定可选 admin/hr 角色，Claude's Discretion 包含此项
   - What's unclear: 管理员手动输入 vs 系统自动生成
   - Recommendation: 管理员手动输入（更简单），配合 `must_change_password=True` 强制首次改密

2. **change-password 是否需要 rate limiting**
   - What we know: login 端点已有 RateLimiter
   - What's unclear: 改密端点是否需要类似保护
   - Recommendation: 暂不加（已登录用户，低风险），后续可加

## Project Constraints (from CLAUDE.md)

- Frontend: React + Ant Design
- Backend: FastAPI
- Commands: `npm run lint`, `npm run build`, `npm run dev`, `pytest`
- 零新依赖策略
- 遵循项目已有的 Table + Modal CRUD 模式

## Sources

### Primary (HIGH confidence)
- `backend/app/api/v1/users.py` -- 已有用户管理 CRUD 端点（完整阅读）
- `backend/app/services/user_service.py` -- 用户服务层（完整阅读，发现 must_change_password bug）
- `backend/app/models/user.py` -- User 模型（完整阅读）
- `backend/app/api/v1/auth.py` -- 认证端点（完整阅读，确认缺少 change-password）
- `backend/app/schemas/users.py` -- 用户 schemas（完整阅读）
- `backend/app/schemas/auth.py` -- 认证 schemas（完整阅读）
- `backend/app/dependencies.py` -- RBAC 依赖（完整阅读）
- `frontend/src/layouts/MainLayout.tsx` -- 菜单和 Header 结构（完整阅读）
- `frontend/src/App.tsx` -- 路由结构（完整阅读）
- `frontend/src/components/AuthProvider.tsx` -- Auth 状态管理（完整阅读）
- `frontend/src/services/authSession.ts` -- Session 存储（完整阅读）
- `frontend/src/services/auth.ts` -- 认证 API 客户端（完整阅读）
- `frontend/src/hooks/authContext.ts` -- Auth 上下文（完整阅读）
- `frontend/src/pages/Employees.tsx` -- Table + Modal 模式参考（部分阅读）
- `tests/test_users.py` -- 现有用户测试（完整阅读）

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- 所有库已在项目中使用，无需引入新依赖
- Architecture: HIGH -- 后端 API 已 80% 就绪，前端模式有成熟参考
- Pitfalls: HIGH -- 通过代码审查发现了具体的 must_change_password bug

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (30 days -- 项目内部代码变动为主)
