# Phase 22: 飞书 OAuth 自动匹配登录 - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

用户能通过飞书扫码或自动登录进入系统，系统自动将飞书身份与已有员工数据（EmployeeMaster）绑定。已登录用户可在设置页主动绑定飞书账号。

**现有基础设施（已完成）：**
- `feishu_oauth_service.py` — exchange_code_for_user()，已实现 OAuth code 换取用户信息
- `feishu_auth.py` — authorize-url + callback 路由已存在
- User 模型已有 `feishu_open_id`、`feishu_union_id` 字段
- EmployeeMaster 模型已有 `person_name`、`employee_id`、`id_number`、`department`
- Login.tsx 已有飞书登录按钮 + OAuth 回调检测
- CSRF state cookie 保护已实现
- JWT 认证体系完整（admin/hr/employee 三角色）

</domain>

<decisions>
## Implementation Decisions

### 自动绑定匹配策略
- **D-01:** 三级匹配优先级：1) feishu_open_id 精确匹配已绑定用户（直接登录） → 2) 姓名+工号精确匹配 EmployeeMaster → 3) 仅姓名匹配（低置信度） → 4) 无匹配则创建新 employee 用户
- **D-02:** 匹配成功后将 feishu_open_id 写入匹配到的 User 记录（或关联的 EmployeeMaster 对应 User），记住绑定关系
- **D-03:** 飞书 API 返回的 name 字段用于姓名匹配；open_id 用于唯一身份标识

### 同名多人处理
- **D-04:** 同名多人时弹出 Modal 展示候选人列表（姓名 + 部门 + 工号后4位），用户点选绑定目标
- **D-05:** 选择后写入 feishu_open_id 绑定关系，下次登录直接通过 open_id 匹配跳过候选列表
- **D-06:** 候选列表信息从 EmployeeMaster 读取（person_name, department, employee_id 脱敏后4位）

### 绑定飞书入口
- **D-07:** 个人设置页新增「绑定飞书」卡片，使用 OAuth 跳转方式绑定
- **D-08:** 已绑定状态显示飞书昵称 + 解绑按钮；未绑定显示绑定按钮
- **D-09:** 新增后端 bind 回调端点，将 feishu_open_id 写入当前已登录用户（需 JWT 认证）
- **D-10:** 解绑操作清空 User 的 feishu_open_id 和 feishu_union_id

### 角色与权限继承
- **D-11:** 绑定已有用户时继承该用户原有角色（admin/hr/employee），不改变角色
- **D-12:** 新建无绑定用户默认 employee 角色
- **D-13:** 不允许通过飞书登录提升角色，角色变更仅限管理员手动操作

### Claude's Discretion
- 候选列表 Modal 的具体样式和布局
- OAuth bind 回调端点的具体路由路径
- 解绑确认的交互方式（确认弹窗 vs 直接解绑）
- 飞书用户名到 display_name 的映射策略

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 认证系统
- `backend/app/core/auth.py` — JWT 签发与验证，AuthUser 结构
- `backend/app/services/feishu_oauth_service.py` — exchange_code_for_user() 当前实现，需修改加入匹配逻辑
- `backend/app/api/v1/feishu_auth.py` — authorize-url + callback 路由
- `backend/app/api/v1/auth.py` — login/me 等认证路由

### 用户与员工模型
- `backend/app/models/user.py` — User 模型（feishu_open_id, feishu_union_id, role 字段）
- `backend/app/models/employee_master.py` — EmployeeMaster 模型（person_name, employee_id, department）
- `backend/app/services/user_service.py` — 用户创建与管理

### 匹配服务（可参考）
- `backend/app/services/matching_service.py` — 现有分层匹配模式可参考

### 前端
- `frontend/src/pages/Login.tsx` — 当前登录页（含飞书按钮）
- `frontend/src/pages/Settings.tsx` — 当前设置页（需添加绑定飞书卡片）
- `frontend/src/services/feishu.ts` — fetchFeishuAuthorizeUrl, feishuOAuthCallback
- `frontend/src/services/auth.ts` — 认证相关前端服务

### 研究参考
- `.planning/research/SUMMARY.md` — v1.2 研究（OAuth 用户身份割裂、CSRF cookie 生产环境问题）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `feishu_oauth_service.py`: exchange_code_for_user() 已处理 code→token→user_info 流程，只需扩展匹配逻辑
- `matching_service.py`: 分层匹配模式（精确→模糊→fallback）可参考
- `Login.tsx`: OAuth 回调检测 useEffect 已实现，可扩展支持 bind 回调
- CSRF state cookie 签名/验证函数可复用

### Established Patterns
- JWT Bearer token 认证贯穿所有需认证端点
- 系统设置通过 system_settings 表覆盖环境变量
- Feature flags 控制飞书功能开关

### Integration Points
- `feishu_oauth_service.py` 需新增 EmployeeMaster 查询逻辑
- `Settings.tsx` 需新增绑定飞书卡片
- `feishu_auth.py` 需新增 bind 回调路由
- callback 返回需支持 `pending_candidates` 状态（同名多人时）

</code_context>

<specifics>
## Specific Ideas

- 研究发现：OAuth 用户身份割裂是关键风险 — 同一人通过飞书和密码登录会产生两个账号，必须通过匹配+绑定解决
- CSRF state cookie 在前后端分离部署下可能丢失，需根据环境动态设置 samesite/secure 参数
- 候选列表中工号脱敏显示后4位即可（如 ****1234），避免完整工号泄露

</specifics>

<deferred>
## Deferred Ideas

- 飞书通讯录 employee_no 精确拉取（需额外权限审批）— v2+
- 已登录用户合并账号（将两个 User 记录合并为一个）— v2+
- 飞书扫码内嵌二维码（QRLogin SDK）— Phase 23 登录页改版时考虑

</deferred>

---

*Phase: 22-oauth*
*Context gathered: 2026-04-16*
