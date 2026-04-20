---
phase: 22-oauth
verified: 2026-04-16T23:30:00Z
status: gaps_found
score: 3/4 must-haves verified
gaps:
  - truth: "所有后端测试通过，验证三级匹配和 bind/unbind 逻辑正确"
    status: failed
    reason: "Plan 03 将 OAuth state 验证从 cookie 改为 body.state_signed，但未同步更新测试用例。authorize-url 不再设置 cookie，测试仍依赖 cookie 传递 signed state，导致 9/16 Phase 22 测试失败。"
    artifacts:
      - path: "tests/test_feishu_auth.py"
        issue: "9 个测试因 state 验证失败返回 400，需在 callback/bind-callback 请求 body 中传递 state_signed"
      - path: "backend/app/api/v1/feishu_auth.py"
        issue: "authorize-url 端点不再 set_cookie，仅通过 response body 返回 state_signed"
    missing:
      - "测试用例需更新：从 authorize-url 响应中提取 state_signed，在 callback 请求 body 中传递"
      - "或恢复 authorize-url 端点的 set_cookie 行为以保持向后兼容"
human_verification:
  - test: "飞书 OAuth 完整登录流程"
    expected: "点击飞书登录 -> 扫码/自动登录 -> 根据匹配结果直接登录或弹出候选人 Modal -> 成功进入系统"
    why_human: "需要真实飞书 OAuth 授权环境和 EmployeeMaster 数据才能验证"
  - test: "设置页飞书绑定/解绑流程"
    expected: "设置页显示飞书绑定卡片 -> 点击绑定 -> 飞书授权 -> 回到设置页显示已绑定 -> 解绑 -> 恢复未绑定"
    why_human: "需要真实飞书 OAuth 环境和前后端联调才能验证完整流程"
---

# Phase 22: 飞书 OAuth 自动匹配登录 Verification Report

**Phase Goal:** 用户能通过飞书扫码或自动登录进入系统，系统自动将飞书身份与已有员工数据绑定
**Verified:** 2026-04-16T23:30:00Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 用户在登录页点击"飞书登录"后完成登录进入系统主页 | VERIFIED | Login.tsx 处理 matched/auto_bound/new_user 状态直接 writeAuthSession + 跳转；feishu.ts 定义了完整的 FeishuOAuthResult 联合类型 |
| 2 | 飞书登录后若姓名唯一匹配 EmployeeMaster，系统自动绑定 | VERIFIED | feishu_oauth_service.py 实现 4 层匹配逻辑，Layer 2 查询 EmployeeMaster.person_name == feishu_name，唯一时调用 _find_or_create_user_for_employee 写入 feishu_open_id |
| 3 | 同名多人展示候选列表让用户选择；无匹配时创建 employee 用户 | VERIFIED | pending_candidates 返回候选列表（工号脱敏 ****XXXX）；CandidateSelectModal.tsx 展示姓名+部门+脱敏工号；Login.tsx 处理 Modal 交互；new_user 创建 employee 角色用户 |
| 4 | 已登录用户可在设置页绑定飞书账号 | VERIFIED | Settings.tsx 新增 feishu-bind 卡片，调用 fetchBindAuthorizeUrl/unbindFeishu；后端 bind-authorize-url/bind-callback/unbind 端点需 JWT 认证 |
| 5 | 所有后端测试通过验证实现正确性 | FAILED | 9/16 Phase 22 测试因 OAuth state 验证失败返回 400。Plan 03 移除了 authorize-url 的 set_cookie 行为，测试仍依赖 cookie 传递 signed state。 |

**Score:** 4/5 truths verified (4 roadmap SCs verified, 1 test regression gap)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/feishu_oauth_service.py` | 三级匹配逻辑 + _find_or_create_user_for_employee + _serialize_candidate | VERIFIED | 包含 matched/auto_bound/pending_candidates/new_user 四种状态、confirm_bind JWT 验证、工号脱敏 |
| `backend/app/api/v1/feishu_auth.py` | confirm-bind + bind-authorize-url + bind-callback + unbind 端点 | VERIFIED | 4 个端点全部存在且包含完整实现 |
| `backend/app/services/user_service.py` | bind_feishu + unbind_feishu 方法 | VERIFIED | 两个方法存在，分别写入/清空 feishu_open_id 和 feishu_union_id |
| `tests/test_feishu_auth.py` | 匹配逻辑 + bind/unbind 测试 | PARTIAL | 测试类全部存在（TestOAuthAutoBinding/TestOAuthPendingCandidates/TestConfirmBind/TestFeishuBind），但 9/16 因 state 验证回归而失败 |
| `frontend/src/components/CandidateSelectModal.tsx` | 候选人选择 Modal 组件 | VERIFIED | 55 行完整组件，展示姓名+部门+脱敏工号，支持 loading 状态 |
| `frontend/src/pages/Login.tsx` | OAuth 回调处理 pending_candidates 状态 | VERIFIED | 导入并使用 CandidateSelectModal，处理 4 种状态分发 |
| `frontend/src/services/feishu.ts` | confirmFeishuBind + fetchBindAuthorizeUrl + unbindFeishu API | VERIFIED | Candidate 接口、FeishuOAuthResult 联合类型、5 个 API 函数全部存在 |
| `frontend/src/pages/Settings.tsx` | 飞书账号绑定卡片 | VERIFIED | feishu-bind 卡片配置、绑定/解绑逻辑、feishuBindCallback 调用 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| feishu_auth.py | feishu_oauth_service.py | exchange_code_for_user() | WIRED | Pattern found in source |
| feishu_oauth_service.py | employee_master.py | EmployeeMaster 查询 | WIRED | Pattern found in source |
| Login.tsx | feishu.ts | feishuOAuthCallback + confirmFeishuBind | WIRED | Pattern found in source |
| Login.tsx | CandidateSelectModal.tsx | 组件导入和状态传递 | WIRED | Pattern found in source |
| Settings.tsx | feishu.ts | fetchBindAuthorizeUrl + unbindFeishu | WIRED | Pattern found in source |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| CandidateSelectModal.tsx | candidates prop | Login.tsx state <- feishuOAuthCallback API | Backend queries EmployeeMaster via DB | FLOWING |
| Settings.tsx | feishuBound/feishuDisplayName | /auth/me API | Backend reads User.feishu_open_id from DB | FLOWING |
| Login.tsx | OAuth result | feishuOAuthCallback -> /auth/feishu/callback | Backend exchange_code_for_user queries DB | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Frontend TypeScript 编译 | npx tsc --noEmit | Exit 0 | PASS |
| Frontend 构建 | npm run build | built in 3.77s | PASS |
| Phase 22 后端测试 | pytest -k "TestOAuth or TestConfirm or TestFeishuBind" | 7 passed, 9 failed | FAIL |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| OAUTH-01 | Plan 01, 02 | 用户可在登录页通过飞书扫码或自动登录进入系统 | SATISFIED | Login.tsx 飞书登录按钮 + OAuth 回调处理 + 4 种状态分发 |
| OAUTH-02 | Plan 01, 02 | 飞书登录后唯一匹配时自动绑定系统用户 | SATISFIED | exchange_code_for_user Layer 2 实现自动绑定逻辑 |
| OAUTH-03 | Plan 01, 02 | 同名多人展示候选列表；无匹配创建 employee 用户 | SATISFIED | pending_candidates + CandidateSelectModal + new_user 创建 |
| OAUTH-04 | Plan 01, 03 | 已登录用户可在设置页绑定飞书账号 | SATISFIED | Settings.tsx feishu-bind 卡片 + bind/unbind API 端点 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | 所有 Phase 22 文件无 TODO/FIXME/placeholder/stub |

### Human Verification Required

### 1. 飞书 OAuth 完整登录流程

**Test:** 点击飞书登录 -> 完成扫码/自动登录 -> 验证 matched/auto_bound/pending_candidates/new_user 四种状态的正确 UI 行为
**Expected:** 直接登录或弹出候选人 Modal，选择后成功进入系统
**Why human:** 需要真实飞书 OAuth 授权环境、EmployeeMaster 测试数据和前后端联调

### 2. 设置页飞书绑定/解绑流程

**Test:** 用密码登录 -> 设置页 -> 绑定飞书 -> 飞书授权 -> 回到设置页已绑定 -> 解绑 -> 恢复未绑定
**Expected:** 绑定/解绑状态正确切换，飞书昵称正确显示
**Why human:** 需要真实飞书 OAuth 环境

### Gaps Summary

**1 个 gap 阻塞完整验证：**

Plan 03 实施过程中将 OAuth state 验证机制从 cookie 改为 body 传递 `state_signed`（因 CORS 跨域 cookie 不可用），但未同步更新 `tests/test_feishu_auth.py` 中的测试用例。authorize-url 端点不再设置 cookie，而测试仍依赖 cookie 读取 signed state，导致 callback 和 bind-callback 请求因 state 验证失败返回 400。

**修复方案：** 测试用例需从 authorize-url 响应 JSON 中提取 `state_signed`，在 callback/bind-callback 请求 body 中传递该值。

受影响的测试类：
- TestOAuthAutoBinding (4/4 failed)
- TestOAuthPendingCandidates (1/1 failed)
- TestConfirmBind (1/4 failed, 其余 3 个不依赖 state)
- TestFeishuBind (3/7 failed)

---

_Verified: 2026-04-16T23:30:00Z_
_Verifier: Claude (gsd-verifier)_
