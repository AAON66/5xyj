---
phase: 22-oauth
plan: "03"
status: complete
started: 2026-04-17
completed: 2026-04-17
---

# Plan 22-03 Summary: 飞书账号绑定设置页

## Objective
在个人设置页新增"飞书账号绑定"卡片，支持已登录用户主动绑定/解绑飞书账号。

## What was built

### Task 1: feishu.ts bind/unbind API + Settings.tsx 绑定卡片
- **feishu.ts**: 新增 `fetchBindAuthorizeUrl()`, `feishuBindCallback()`, `unbindFeishu()` 三个 API 函数
- **Settings.tsx**: 新增 `feishu-bind` 卡片配置，未绑定显示绑定按钮，已绑定显示飞书昵称+解绑按钮
- 解绑前弹出 Modal.confirm 二次确认（T-22-10 威胁缓解）
- 绑定回调通过 URL 参数 `code` + `state` + `action=bind` 处理
- 所有角色（admin/hr/employee）可见

### Bug fixes during verification
- **OAuth state 验证失败**: cookie 跨域不可用，改用 localStorage 存储签名 state
- **Vite proxy**: 添加 `/api` 代理消除前后端跨域问题
- **Redirect URI**: 统一为 `http://127.0.0.1:5173/login` 与 Vite server host 一致
- **fetchFeishuAuthorizeUrl**: 修复返回值类型（对象 vs 字符串）
- **Login.tsx bind 转发**: 检测 `bind:` state 前缀转发到 Settings 页
- **Feature flag 移除**: 飞书绑定卡片不再受 feishu_oauth_enabled 控制

### Task 2: 人工验证 ✓
用户确认：绑定、解绑、重新绑定流程全部正常。

## Key files

### Created
- (none — all modifications to existing files)

### Modified
- `frontend/src/pages/Settings.tsx` — 飞书绑定卡片
- `frontend/src/services/feishu.ts` — bind/unbind API + localStorage state
- `frontend/src/pages/Login.tsx` — bind callback 转发
- `frontend/src/services/api.ts` — withCredentials
- `frontend/src/config/env.ts` — 相对路径 baseURL
- `frontend/vite.config.ts` — API proxy
- `backend/app/api/v1/feishu_auth.py` — state_signed 验证
- `backend/app/core/config.py` — feishu_oauth_redirect_uri
- `backend/app/main.py` — CORS credentials
- `.env` — FEISHU_OAUTH_REDIRECT_URI

## Deviations
- 原计划用 cookie 做 CSRF state 验证，因跨域问题改用 localStorage + 签名
- 添加了 Vite proxy（原计划未涉及）
- 移除了 feishu_oauth_enabled 对绑定卡片的控制（用户要求）

## Self-Check: PASSED
- [x] 飞书绑定卡片在设置页可见
- [x] 未绑定 → 绑定 → 已绑定状态正确
- [x] 已绑定 → 解绑 → 未绑定状态正确
- [x] lint 通过
- [x] build 通过
- [x] 人工验证通过
