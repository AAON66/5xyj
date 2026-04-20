# Phase 22: 飞书 OAuth 自动匹配登录 - Research

**Researched:** 2026-04-16
**Domain:** OAuth 身份认证 + 员工自动匹配绑定
**Confidence:** HIGH

## Summary

Phase 22 的核心任务是将现有的"飞书 OAuth 登录即创建新 employee 用户"流程升级为"飞书 OAuth 登录 + 自动匹配 EmployeeMaster + 智能绑定已有用户"。当前代码基础已经完成了 80% 的 OAuth 基础设施（code 换 token、CSRF state cookie、JWT 签发），但缺少关键的身份匹配层和绑定管理能力。

主要工作集中在三个方面：(1) 后端 `feishu_oauth_service.py` 新增三级匹配逻辑（open_id 精确匹配 -> 姓名+工号匹配 EmployeeMaster -> 仅姓名匹配），(2) 前端 Login.tsx 处理 `pending_candidates` 状态并展示候选人选择 Modal，(3) Settings.tsx 新增"绑定飞书"卡片 + 后端 bind/unbind 端点。

后端零新依赖。前端零新依赖（使用 Ant Design 现有 Modal/List 组件）。数据库无 schema 变更（User 模型已有 `feishu_open_id` 和 `feishu_union_id` 字段）。

**Primary recommendation:** 以 `feishu_oauth_service.py` 的 `exchange_code_for_user()` 为核心改造点，新增分层匹配逻辑；callback 返回值扩展支持 `pending_candidates` 状态；前端在 Login.tsx 和 Settings.tsx 分别处理候选选择和主动绑定。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 三级匹配优先级：1) feishu_open_id 精确匹配已绑定用户（直接登录） -> 2) 姓名+工号精确匹配 EmployeeMaster -> 3) 仅姓名匹配（低置信度） -> 4) 无匹配则创建新 employee 用户
- **D-02:** 匹配成功后将 feishu_open_id 写入匹配到的 User 记录（或关联的 EmployeeMaster 对应 User），记住绑定关系
- **D-03:** 飞书 API 返回的 name 字段用于姓名匹配；open_id 用于唯一身份标识
- **D-04:** 同名多人时弹出 Modal 展示候选人列表（姓名 + 部门 + 工号后4位），用户点选绑定目标
- **D-05:** 选择后写入 feishu_open_id 绑定关系，下次登录直接通过 open_id 匹配跳过候选列表
- **D-06:** 候选列表信息从 EmployeeMaster 读取（person_name, department, employee_id 脱敏后4位）
- **D-07:** 个人设置页新增"绑定飞书"卡片，使用 OAuth 跳转方式绑定
- **D-08:** 已绑定状态显示飞书昵称 + 解绑按钮；未绑定显示绑定按钮
- **D-09:** 新增后端 bind 回调端点，将 feishu_open_id 写入当前已登录用户（需 JWT 认证）
- **D-10:** 解绑操作清空 User 的 feishu_open_id 和 feishu_union_id
- **D-11:** 绑定已有用户时继承该用户原有角色（admin/hr/employee），不改变角色
- **D-12:** 新建无绑定用户默认 employee 角色
- **D-13:** 不允许通过飞书登录提升角色，角色变更仅限管理员手动操作

### Claude's Discretion
- 候选列表 Modal 的具体样式和布局
- OAuth bind 回调端点的具体路由路径
- 解绑确认的交互方式（确认弹窗 vs 直接解绑）
- 飞书用户名到 display_name 的映射策略

### Deferred Ideas (OUT OF SCOPE)
- 飞书通讯录 employee_no 精确拉取（需额外权限审批）-- v2+
- 已登录用户合并账号（将两个 User 记录合并为一个）-- v2+
- 飞书扫码内嵌二维码（QRLogin SDK）-- Phase 23 登录页改版时考虑
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OAUTH-01 | 用户可在登录页通过飞书扫码或本设备飞书自动登录进入系统 | 现有 OAuth 基础设施已完成（authorize-url + callback + CSRF state），只需完善 callback 返回逻辑和前端处理 |
| OAUTH-02 | 飞书登录后系统自动按姓名/工号查询 EmployeeMaster，唯一匹配时自动绑定系统用户 | 需新增 EmployeeMaster 查询逻辑到 exchange_code_for_user()，匹配成功后写入 feishu_open_id |
| OAUTH-03 | 同名多人时系统展示候选列表让用户选择绑定目标，无匹配时创建无绑定的 employee 用户 | callback 返回需支持 pending_candidates 状态 + 新增 confirm-bindAPI + 前端 Modal 选择组件 |
| OAUTH-04 | 已登录用户可在个人设置页通过"绑定飞书"入口关联自己的飞书账号 | 需新增 bind 回调端点 + unbind 端点 + Settings.tsx 绑定飞书卡片 |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 现有 | OAuth 回调路由、bind/unbind 端点 | 项目已用 [VERIFIED: 项目代码] |
| SQLAlchemy | 现有 | User + EmployeeMaster 查询与更新 | 项目已用 [VERIFIED: 项目代码] |
| httpx | 现有 | 飞书 OAuth token exchange API 调用 | 项目已用 [VERIFIED: feishu_oauth_service.py] |
| PyJWT | 现有 | JWT 签发与验证 | 项目已用 [VERIFIED: auth.py] |
| Ant Design | 现有 | Modal、List、Card 等 UI 组件 | 项目已用 [VERIFIED: Login.tsx] |
| React Router | 现有 | OAuth 回调 URL 参数解析 | 项目已用 [VERIFIED: Login.tsx] |

### Supporting

无新增依赖。所有需求均可通过现有项目依赖实现。

**Installation:**
```bash
# 无新增依赖
```

## Architecture Patterns

### 修改文件清单

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── feishu_auth.py        # 修改: 新增 bind-callback, unbind, confirm-bindendpoints
│   │   └── auth.py               # 修改: /me 端点返回 feishu 绑定状态
│   ├── services/
│   │   ├── feishu_oauth_service.py  # 重构核心: 新增三级匹配逻辑
│   │   └── user_service.py       # 修改: 新增 bind/unbind feishu 方法
│   └── models/
│       └── user.py               # 不变 (feishu_open_id/union_id 字段已存在)
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.tsx             # 修改: 处理 pending_candidates 状态 + Modal
│   │   └── Settings.tsx          # 修改: 新增 "绑定飞书" 卡片
│   ├── services/
│   │   └── feishu.ts             # 修改: 新增 confirmBind, bindFeishu, unbindFeishu API
│   └── components/
│       └── CandidateSelectModal.tsx  # 新建: 候选人选择 Modal 组件
tests/
└── test_feishu_auth.py           # 修改: 新增匹配逻辑和 bind/unbind 测试
```

### Pattern 1: 分层匹配 (Tiered Matching)

**What:** OAuth callback 返回结果分为四种状态：matched（直接登录）、auto_bound（自动绑定后登录）、pending_candidates（需用户选择）、new_user（创建新用户后登录）。

**When to use:** 每次飞书 OAuth 回调处理时。

**Example:**
```python
# Source: 基于现有 matching_service.py 的分层匹配模式 [VERIFIED: 项目代码]
async def exchange_code_for_user(db: Session, code: str, settings: Settings) -> dict:
    # ... (获取飞书用户信息: open_id, name) ...

    # 第1层: open_id 精确匹配已绑定用户
    user = db.query(User).filter(User.feishu_open_id == open_id).first()
    if user:
        token, exp = issue_access_token(...)
        return {"status": "matched", "access_token": token, ...}

    # 第2层: 姓名精确匹配 EmployeeMaster
    candidates = db.query(EmployeeMaster).filter(
        EmployeeMaster.person_name == feishu_name,
        EmployeeMaster.active == True,
    ).all()

    if len(candidates) == 1:
        # 唯一匹配 -> 自动绑定
        emp = candidates[0]
        user = _find_or_create_user_for_employee(db, emp, open_id, union_id, feishu_name)
        token, exp = issue_access_token(...)
        return {"status": "auto_bound", "access_token": token, ...}

    if len(candidates) > 1:
        # 多人同名 -> 返回候选列表
        return {
            "status": "pending_candidates",
            "feishu_open_id": open_id,
            "feishu_union_id": union_id,
            "feishu_name": feishu_name,
            "candidates": [
                {
                    "employee_master_id": c.id,
                    "person_name": c.person_name,
                    "department": c.department or "",
                    "employee_id_masked": f"****{c.employee_id[-4:]}" if len(c.employee_id) >= 4 else c.employee_id,
                }
                for c in candidates
            ],
        }

    # 第4层: 无匹配 -> 创建新 employee 用户
    user = _create_new_feishu_user(db, open_id, union_id, feishu_name)
    token, exp = issue_access_token(...)
    return {"status": "new_user", "access_token": token, ...}
```

### Pattern 2: Confirm-Bind 端点 (候选人选择确认)

**What:** 用户从候选列表选择后，前端调用 confirm-bind 端点完成绑定并签发 JWT。

**When to use:** pending_candidates 状态下用户选择候选人后。

**Example:**
```python
# Source: 基于现有 feishu_auth.py 路由模式 [VERIFIED: 项目代码]
@router.post("/confirm-bind", summary="确认绑定飞书与员工")
async def confirm_bind(
    body: ConfirmBindBody,  # feishu_open_id, feishu_union_id, feishu_name, employee_master_id
    request: Request,
    db: Session = Depends(get_db),
):
    # 验证 employee_master_id 存在
    emp = db.query(EmployeeMaster).filter(EmployeeMaster.id == body.employee_master_id).first()
    if not emp:
        return error_response("NOT_FOUND", "员工记录不存在", 404)

    # 检查 open_id 是否已被其他用户绑定
    existing = db.query(User).filter(User.feishu_open_id == body.feishu_open_id).first()
    if existing:
        return error_response("ALREADY_BOUND", "该飞书账号已绑定其他用户", 409)

    # 查找或创建 User 并绑定
    user = _find_or_create_user_for_employee(db, emp, body.feishu_open_id, body.feishu_union_id, body.feishu_name)
    token, exp = issue_access_token(...)
    return success_response({"access_token": token, ...})
```

### Pattern 3: Bind/Unbind 端点 (已登录用户主动绑定)

**What:** 已登录用户通过设置页主动发起飞书 OAuth 绑定/解绑。

**When to use:** Settings 页面"绑定飞书"功能。

**Example:**
```python
# Source: 基于现有 feishu_auth.py CSRF 模式 [VERIFIED: 项目代码]
@router.get("/bind-authorize-url", summary="获取飞书绑定授权 URL")
async def get_bind_authorize_url(request: Request, db: Session = Depends(get_db)):
    # 与 authorize-url 类似，但 redirect_uri 指向 bind-callback
    # state 中可编码 action=bind 用于区分
    ...

@router.post("/bind-callback", summary="飞书绑定回调")
async def feishu_bind_callback(
    body: OAuthCallbackBody,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_auth),  # 需 JWT 认证
):
    # 验证 state cookie
    # 调用飞书 API 获取 open_id
    # 检查 open_id 是否已被其他用户绑定
    # 写入当前用户的 feishu_open_id / feishu_union_id
    ...

@router.post("/unbind", summary="解绑飞书")
async def unbind_feishu(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(require_auth),
):
    # 清空当前用户的 feishu_open_id 和 feishu_union_id
    ...
```

### Anti-Patterns to Avoid

- **直接按 feishu_name 创建新用户而不查 EmployeeMaster:** 这会导致身份割裂问题（同一人两个账号），正是 Phase 22 要解决的核心问题。[VERIFIED: PITFALLS.md Pitfall 2]
- **把 pending_candidates 的完整 employee_id 暴露给前端:** 安全风险，必须脱敏为后4位。[VERIFIED: CONTEXT.md D-06]
- **confirm-bind 不验证 open_id 是否已被其他用户绑定:** 会导致同一个飞书账号绑定多个系统用户。
- **bind 回调不要求 JWT 认证:** 任何人都能绑定任意用户的飞书账号。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT 签发 | 自定义 token | 现有 `issue_access_token()` | 已经过测试和验证 [VERIFIED: auth.py] |
| CSRF state 保护 | 自定义方案 | 现有 `_sign_state()` / `_verify_state()` | 已实现 HMAC 签名 [VERIFIED: feishu_auth.py] |
| 密码哈希 | 自定义 | 现有 `hash_password()` | pwdlib + bcrypt [VERIFIED: user_service.py] |
| 候选人 Modal | 自定义 dialog | Ant Design `Modal` + `List` | 项目标准 UI 库 [VERIFIED: Login.tsx 使用 antd] |

## Common Pitfalls

### Pitfall 1: pending_candidates 状态安全性

**What goes wrong:** confirm-bind 端点接受前端传来的 feishu_open_id + employee_master_id 进行绑定，但未验证该 feishu_open_id 确实来自刚才的 OAuth 流程，攻击者可伪造。

**Why it happens:** pending_candidates 是无状态返回，后端不保留中间态，前端持有 open_id 后再回传。

**How to avoid:** 两种方案择一：(A) confirm-bind 时要求前端带上原始 OAuth state 并在后端验证（推荐）；(B) pending_candidates 时后端生成一个临时 token（短时效，如5分钟），confirm-bind 时验证该 token。方案 A 更简单，复用现有 CSRF state 验证逻辑。

**Warning signs:** 有人能不通过飞书 OAuth 就绑定任意 feishu_open_id 到任意用户。

### Pitfall 2: feishu_open_id 唯一性冲突

**What goes wrong:** 当同一个飞书用户尝试绑定到不同系统用户时，由于 `feishu_open_id` 字段有 `unique=True` 约束，直接写入会抛 IntegrityError。

**Why it happens:** User 模型已定义 `feishu_open_id: unique=True`。[VERIFIED: user.py line 20]

**How to avoid:** 在绑定前显式检查 `db.query(User).filter(User.feishu_open_id == open_id).first()`，如已存在则返回 `ALREADY_BOUND` 错误。不要依赖数据库层异常来控制业务逻辑。

**Warning signs:** 500 Internal Server Error 包含 `UNIQUE constraint failed`。

### Pitfall 3: CSRF state cookie 跨域丢失

**What goes wrong:** 现有 cookie 设置 `samesite="lax"`, `secure=False`，在前后端分离部署（不同端口/域名）时，浏览器可能不携带 cookie，导致 state 验证失败。

**Why it happens:** 飞书 OAuth 是 cross-site redirect，POST 请求时 SameSite=Lax 不附带 cookie。[VERIFIED: feishu_auth.py line 76-80, PITFALLS.md Pitfall 4]

**How to avoid:** 根据 `settings.runtime_environment` 动态设置 cookie 参数：本地开发用 `samesite="lax", secure=False`；生产环境用 `samesite="none", secure=True`（需 HTTPS）。当前代码已有 `runtime_environment` 设置。[VERIFIED: config.py line 78]

**Warning signs:** 开发环境正常但生产环境飞书登录100%失败，错误码 `INVALID_STATE`。

### Pitfall 4: EmployeeMaster 与 User 的关联缺失

**What goes wrong:** EmployeeMaster 和 User 是独立表，没有外键关联。自动匹配绑定后，系统知道"这个飞书用户对应 EmployeeMaster 记录 X"，但 User 表没有字段记录与哪个 EmployeeMaster 关联。

**Why it happens:** 当前 User 模型只有 `feishu_open_id` / `feishu_union_id`，没有 `employee_master_id` 字段。

**How to avoid:** 对于 Phase 22 的需求范围，可以不新增 User.employee_master_id 字段。匹配逻辑是：(1) open_id 匹配 User -> 直接登录；(2) 姓名匹配 EmployeeMaster -> 查找或创建对应 User -> 写入 open_id。关键是"查找对应 User"的逻辑——可以通过 username 约定（如 `emp_{employee_id}`）或通过 display_name 匹配来关联。但更健壮的做法是在 User 模型新增 nullable `employee_master_id` 字段。[ASSUMED]

**Warning signs:** 无法追溯 User 与 EmployeeMaster 的对应关系。

### Pitfall 5: fetchFeishuAuthorizeUrl 返回类型不一致

**What goes wrong:** 前端 `fetchFeishuAuthorizeUrl()` 返回 `Promise<string>`，但后端 `/authorize-url` 返回 `success_response({"url": url})`，即 `data` 是一个对象而不是字符串。

**Why it happens:** 前端类型声明 `ApiSuccessResponse<string>` 与后端实际返回格式不匹配。[VERIFIED: feishu.ts line 302-306 vs feishu_auth.py line 73]

**How to avoid:** 检查并修复前端 `fetchFeishuAuthorizeUrl()` 的返回类型处理——应从 `response.data.data.url` 读取 URL，或保持当前 `response.data.data` 如果后端已被修改。实际测试确认当前行为。

**Warning signs:** 飞书登录按钮点击后跳转到 `[object Object]` 而不是飞书授权页。

## Code Examples

### 后端: exchange_code_for_user 重构

```python
# Source: 基于现有代码重构 [VERIFIED: feishu_oauth_service.py]
from backend.app.models.employee_master import EmployeeMaster

async def exchange_code_for_user(db: Session, code: str, settings: Settings) -> dict:
    """
    Exchange Feishu OAuth code for user info, match against EmployeeMaster,
    find/create system user, and issue JWT.

    Returns dict with "status" field indicating match result:
    - "matched": existing bound user, includes access_token
    - "auto_bound": newly bound user via unique name match, includes access_token
    - "pending_candidates": multiple name matches, includes candidates list
    - "new_user": no match found, new employee user created, includes access_token
    """
    # 1. 飞书 API 调用获取 open_id + name (保持现有逻辑)
    open_id, union_id, feishu_name = await _fetch_feishu_user_info(code, settings)

    # 2. 第一级: open_id 精确匹配
    user = db.query(User).filter(User.feishu_open_id == open_id).first()
    if user:
        return _build_login_response(user, settings, status="matched")

    # 3. 第二级: 姓名匹配 EmployeeMaster
    candidates = db.query(EmployeeMaster).filter(
        EmployeeMaster.person_name == feishu_name,
        EmployeeMaster.active == True,
    ).all()

    if len(candidates) == 1:
        user = _find_or_create_user_for_employee(db, candidates[0], open_id, union_id, feishu_name)
        return _build_login_response(user, settings, status="auto_bound")

    if len(candidates) > 1:
        return {
            "status": "pending_candidates",
            "feishu_open_id": open_id,
            "feishu_union_id": union_id,
            "feishu_name": feishu_name,
            "candidates": [_serialize_candidate(c) for c in candidates],
        }

    # 4. 第四级: 无匹配 -> 创建新用户
    user = _create_new_feishu_user(db, open_id, union_id, feishu_name)
    return _build_login_response(user, settings, status="new_user")
```

### 前端: OAuth 回调处理 pending_candidates

```typescript
// Source: 基于现有 Login.tsx useEffect 模式 [VERIFIED: Login.tsx line 40-58]
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  if (code && state && feishu_oauth_enabled) {
    feishuOAuthCallback(code, state)
      .then((result) => {
        if (result.status === 'pending_candidates') {
          // 展示候选人选择 Modal
          setCandidates(result.candidates);
          setPendingFeishuInfo({
            feishu_open_id: result.feishu_open_id,
            feishu_union_id: result.feishu_union_id,
            feishu_name: result.feishu_name,
          });
          setShowCandidateModal(true);
        } else {
          // matched / auto_bound / new_user -> 直接登录
          writeAuthSession({
            accessToken: result.access_token,
            role: result.role as AuthRole,
            username: result.username,
            displayName: result.display_name,
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            signedInAt: new Date().toISOString(),
          });
          window.location.href = '/';
        }
      })
      .catch(() => message.error('飞书登录失败'));
  }
}, [feishu_oauth_enabled, message]);
```

### 前端: CandidateSelectModal 组件

```typescript
// Source: Ant Design Modal + List 模式 [ASSUMED: 推荐实现方式]
import { Modal, List, Typography } from 'antd';

interface Candidate {
  employee_master_id: string;
  person_name: string;
  department: string;
  employee_id_masked: string;
}

interface Props {
  open: boolean;
  candidates: Candidate[];
  onSelect: (employeeMasterId: string) => void;
  onCancel: () => void;
  loading: boolean;
}

export function CandidateSelectModal({ open, candidates, onSelect, onCancel, loading }: Props) {
  return (
    <Modal
      title="选择您的身份"
      open={open}
      onCancel={onCancel}
      footer={null}
    >
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        系统发现多个同名员工，请选择您的身份以完成绑定：
      </Typography.Text>
      <List
        dataSource={candidates}
        loading={loading}
        renderItem={(item) => (
          <List.Item
            style={{ cursor: 'pointer' }}
            onClick={() => onSelect(item.employee_master_id)}
          >
            <List.Item.Meta
              title={item.person_name}
              description={`${item.department || '未知部门'} | 工号 ${item.employee_id_masked}`}
            />
          </List.Item>
        )}
      />
    </Modal>
  );
}
```

### Settings.tsx: 绑定飞书卡片

```typescript
// Source: 基于现有 SETTINGS_CARDS 模式 [VERIFIED: Settings.tsx]
// 在 SETTINGS_CARDS 数组中新增:
{
  key: 'feishu-bind',
  title: '飞书账号绑定',
  description: '绑定或解绑飞书账号，绑定后可使用飞书快捷登录',
  keywords: ['飞书', '绑定', '账号', '解绑'],
  roles: ['admin', 'hr', 'employee'],
  // 此卡片内容为自定义渲染（非 linkTo），需内联绑定/解绑逻辑
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 飞书 OAuth v1 token exchange（需先获取 app_access_token） | 飞书 OAuth v2 token exchange（直接用 client_id + client_secret） | 2024 飞书 API 更新 | v2 更符合 RFC 6749 标准，参数名不同，expires_in 语义变化 |
| 飞书授权页 `/open-apis/authen/v1/index?app_id=` | 新授权页 `/open-apis/authen/v1/authorize?client_id=` | 2024 飞书 API 更新 | 当前代码已使用新授权页但仍用 v1 token endpoint |

**当前代码状态：** 授权 URL 已使用新版格式（`accounts.feishu.cn` + `client_id`），但 token exchange 仍使用 v1 端点（`authen/v1/access_token` + `app_access_token` 头）。此混合状态目前可工作，但建议保持 v1 token endpoint 不做迁移，避免不必要的风险。[VERIFIED: feishu_auth.py line 67-70, feishu_oauth_service.py line 31-51] [CITED: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token]

**Deprecated/outdated:**
- 飞书 OAuth v1 授权页 URL（`/open-apis/authen/v1/index`）：已被新授权页替代，当前代码已更新 [VERIFIED: feishu_auth.py]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 可以不新增 User.employee_master_id 字段，通过 username 约定关联 | Pitfall 4 | 中等 -- 后续查找绑定关系需要额外查询，但不影响 Phase 22 核心功能 |
| A2 | CandidateSelectModal 使用 Ant Design Modal + List 组件即可满足 UX 需求 | Code Examples | 低 -- 如果需要更复杂的交互可以后续调整 |
| A3 | confirm-bind 安全性可通过复用现有 CSRF state 验证来保障 | Pitfall 1 | 中等 -- 如果 state cookie 已被 callback 消费删除，需要额外 token 机制 |

## Open Questions

1. **fetchFeishuAuthorizeUrl 返回类型问题**
   - What we know: 后端返回 `{"data": {"url": "..."}}`，前端声明返回 `string`
   - What's unclear: 当前运行时是否有中间层转换，还是前端实际收到的是对象
   - Recommendation: 实现时检查并修复，确保前端正确提取 URL 字符串

2. **confirm-bind 的安全验证机制**
   - What we know: callback 成功后 state cookie 被删除（`resp.delete_cookie`），confirm-bind 无法复用
   - What's unclear: 是否需要为 pending_candidates 生成临时 token
   - Recommendation: 为 pending_candidates 状态生成短时效临时 token（5分钟），confirm-bind 时验证该 token。token 可以是 JWT，payload 包含 feishu_open_id + 过期时间

3. **feishu_oauth_redirect_uri 配置缺失**
   - What we know: `feishu_auth.py` 通过 `getattr(settings, "feishu_oauth_redirect_uri", "")` 读取，但 Settings 模型未定义此字段
   - What's unclear: 实际运行时该值是否通过环境变量注入（pydantic-settings 允许 extra='ignore'）
   - Recommendation: 在 Settings 模型中显式添加 `feishu_oauth_redirect_uri: str = ""` 字段。bind 回调需要不同的 redirect_uri

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml or pytest.ini |
| Quick run command | `pytest tests/test_feishu_auth.py -x -q` |
| Full suite command | `pytest` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OAUTH-01 | 飞书 OAuth 登录完整流程 | integration | `pytest tests/test_feishu_auth.py::TestOAuthStateValidation -x` | Yes (需扩展) |
| OAUTH-02 | 唯一姓名匹配自动绑定 | unit | `pytest tests/test_feishu_auth.py::TestOAuthAutoBinding -x` | No -- Wave 0 |
| OAUTH-03 | 同名多人返回候选列表 + confirm-bind | unit | `pytest tests/test_feishu_auth.py::TestOAuthPendingCandidates -x` | No -- Wave 0 |
| OAUTH-03 | 无匹配创建新 employee 用户 | unit | `pytest tests/test_feishu_auth.py::TestOAuthUserCreation::test_oauth_callback_creates_new_user -x` | Yes (已有) |
| OAUTH-04 | bind/unbind 端点 | unit | `pytest tests/test_feishu_auth.py::TestFeishuBind -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_feishu_auth.py -x -q`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_feishu_auth.py::TestOAuthAutoBinding` -- 唯一匹配自动绑定（需 seed EmployeeMaster fixture）
- [ ] `tests/test_feishu_auth.py::TestOAuthPendingCandidates` -- 同名多人候选列表 + confirm-bind
- [ ] `tests/test_feishu_auth.py::TestFeishuBind` -- bind-callback + unbind 端点
- [ ] `tests/conftest.py` -- 新增 `seed_multiple_employees_same_name` fixture（同名多人测试数据）

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | 飞书 OAuth 2.0 + JWT Bearer token（现有体系） |
| V3 Session Management | yes | JWT 有时效（480分钟），localStorage 存储（现有体系） |
| V4 Access Control | yes | 角色继承不提升（D-13），bind 需 JWT 认证（D-09） |
| V5 Input Validation | yes | open_id/employee_master_id 格式验证，候选人工号脱敏 |
| V6 Cryptography | no | 不涉及加密操作 |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSRF on OAuth callback | Spoofing | HMAC-signed state cookie (已实现) [VERIFIED: feishu_auth.py] |
| Unauthorized binding (伪造 open_id 绑定) | Elevation of Privilege | confirm-bind 需临时 token 验证 + bind-callback 需 JWT 认证 |
| 信息泄露 (完整工号) | Information Disclosure | 候选列表工号脱敏为后4位 (D-06) |
| 身份割裂 (同人多账号) | Spoofing | 三级匹配逻辑消除割裂 (D-01) |
| feishu_open_id 唯一性冲突导致 500 | Denial of Service | 绑定前显式检查唯一性 |

## Sources

### Primary (HIGH confidence)
- 项目源码深度分析: feishu_oauth_service.py, feishu_auth.py, user.py, employee_master.py, Login.tsx, Settings.tsx, feishu.ts, auth.py, config.py, conftest.py, test_feishu_auth.py
- [飞书 OAuth v2 API 文档](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token) -- token exchange 格式
- `.planning/research/SUMMARY.md` -- v1.2 整体研究报告
- `.planning/research/PITFALLS.md` -- OAuth 身份割裂和 CSRF cookie 问题
- `22-CONTEXT.md` -- 用户决策和实现约束

### Secondary (MEDIUM confidence)
- [飞书 OAuth 登录实现教程](https://iamazing.cn/page/feishu-oauth-login) -- 社区实践
- [Next14 + Auth5 飞书授权登录](https://juejin.cn/post/7357261180493135898) -- v2 API 参数格式验证

### Tertiary (LOW confidence)
- 无

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 零新依赖，完全基于现有代码扩展
- Architecture: HIGH - 修改范围精确到文件和函数，基于现有代码深度分析
- Pitfalls: HIGH - 5个 pitfall 中4个有代码一手证据，1个基于合理推断

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (稳定领域，现有代码基础不会频繁变化)
