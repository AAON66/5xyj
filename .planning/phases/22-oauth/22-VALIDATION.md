---
phase: 22
slug: oauth
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-16
updated: 2026-04-20
---

# Phase 22 — Validation Strategy

> Per-phase validation contract, retroactively aligned with delivered tasks during v1.2 gap closure (Phase 24).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (backend) + Playwright 1.59.1 (frontend E2E) + TypeScript strict + ESLint |
| **Config file** | `backend/pyproject.toml` + `frontend/playwright.config.ts` |
| **Quick run command** | `cd /Users/mac/PycharmProjects/5xyj && .venv/bin/python -m pytest backend/tests/test_feishu_auth.py backend/tests/test_feishu_settings_api.py -q` |
| **Full OAuth coverage** | `.venv/bin/python -m pytest backend/tests/test_feishu_auth.py tests/test_feishu_auth.py -q -k "TestOAuth or TestConfirm or TestFeishuBind or smoke or authorize or callback"` |
| **Full suite command** | `.venv/bin/python -m pytest backend/tests/ tests/ -q && cd frontend && npm run lint && npm run build && npm run test:e2e` |
| **Estimated runtime** | ~10s smoke / ~20s OAuth subset / ~90s full suite |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run Full OAuth coverage command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10s quick / 20s OAuth subset

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| `22-01-T1` | 01 | 1 | OAUTH-01, OAUTH-02, OAUTH-03 | T-22-01, T-22-03, T-22-06, T-22-07 | HMAC state 校验 + 工号脱敏 + open_id 唯一性检查 + 新用户固定 employee 角色 | 后端 TDD | `.venv/bin/python -m pytest backend/tests/test_feishu_auth.py tests/test_feishu_auth.py::TestOAuthAutoBinding tests/test_feishu_auth.py::TestOAuthPendingCandidates tests/test_feishu_auth.py::TestConfirmBind -q` | ✅ | ✅ green (smoke coverage added in Phase 24) |
| `22-01-T2` | 01 | 1 | OAUTH-04 | T-22-02, T-22-05 | bind-callback / unbind 强制 JWT 认证 + state HMAC | 后端 TDD | `.venv/bin/python -m pytest tests/test_feishu_auth.py::TestFeishuBind -q` | ✅ | ✅ green |
| `22-02-T1` | 02 | 2 | OAUTH-01, OAUTH-02, OAUTH-03 | T-22-08 | CandidateSelectModal 只展示脱敏工号；URL code/state 立即清除防重放 | 前端静态+E2E | `cd frontend && npm run lint && npm run build && npx playwright test tests/e2e/feishu-oauth.spec.ts` | ✅ | ✅ green |
| `22-02-T2` | 02 | 2 | OAUTH-01..03 | T-22-09 | 人工验证 4 状态 UI 分发 + 候选 Modal 交互 | human-verify | 22-VERIFICATION.md human_verification step 1 | ✅ | ⚠️ pending (UAT) |
| `22-03-T1` | 03 | 2 | OAUTH-04 | T-22-10 | Settings 解绑前 Modal.confirm 二次确认 | 前端静态 | `cd frontend && npm run lint && npm run build` | ✅ | ✅ green |
| `22-03-T2` | 03 | 2 | OAUTH-04 | T-22-11 | 人工验证绑定/解绑流程 | human-verify | 22-VERIFICATION.md human_verification step 2 | ✅ | ⚠️ pending (UAT) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky / awaiting manual*

> **Task ID 依据:** `22-01-PLAN.md`（T1/T2）、`22-02-PLAN.md`（T1/T2）、`22-03-PLAN.md`（T1/T2）的 `<task>` 节点。
>
> **Status 依据:** `22-01-SUMMARY.md` commits b8303b4/803236d/9f946a9/b8a3f79、`22-02-SUMMARY.md` commit 73c94ca、`22-03-SUMMARY.md` plan03 全部完成，以及 Phase 24 Task 1 commit b89bdb5（backend/tests/test_feishu_auth.py smoke tests）。

---

## Wave 0 Requirements

- [x] `backend/app/services/feishu_oauth_service.py` — 3-level matching + confirm_bind JWT
- [x] `backend/app/api/v1/feishu_auth.py` — authorize-url / callback / confirm-bind / bind-authorize-url / bind-callback / unbind
- [x] `backend/app/services/user_service.py` — bind_feishu / unbind_feishu
- [x] `frontend/src/components/CandidateSelectModal.tsx` — 候选人选择 Modal（脱敏工号展示）
- [x] `backend/tests/test_feishu_auth.py` — 3 smoke 测试（Phase 24 补齐 Wave 0 残缺覆盖）
- [x] `tests/test_feishu_auth.py` — TestOAuthAutoBinding / TestOAuthPendingCandidates / TestConfirmBind / TestFeishuBind（22 tests 全绿）

*Existing backend pytest + frontend Vite/Playwright 基础设施覆盖所有 phase 需求，无需新框架安装。*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Covered By |
|----------|-------------|------------|-------------------|------------|
| 飞书 OAuth 完整登录流程（扫码 → 4 状态分发） | OAUTH-01..03 | 需真实飞书 OAuth 授权环境 + EmployeeMaster 测试数据 | 启动后端/前端 → 登录页点击飞书登录 → 扫码 → 验证 matched / auto_bound / pending_candidates / new_user 四种 UI 行为 | 22-02-T2（22-VERIFICATION.md human_verification step 1） |
| 设置页绑定/解绑流程 | OAUTH-04 | 需真实飞书 OAuth + 前后端联调 | 用密码登录 → 设置页 → 绑定飞书 → 授权 → 已绑定 → 解绑 → 未绑定 | 22-03-T2（22-VERIFICATION.md human_verification step 2） |

---

## Acknowledged Tech Debt

本 phase 在 v1.2 milestone audit 中被标记有 3 项可接受 tech debt：

1. **后端 OAuth smoke 测试在 Phase 24 才补齐到标准路径。** 原 22-VERIFICATION.md 声称 `test_feishu_auth.py` 9/16 红是对 *OAuth 核心测试* 的幻觉描述 — 实际上 `tests/test_feishu_auth.py::TestOAuth* / TestConfirm* / TestFeishuBind*` 共 22 个测试在当前基线上全部绿；22-VERIFICATION.md 当时观察到的失败集中在 `TestFeatureFlags` / `TestSettingsEndpoints`（与 OAuth 无关）。Phase 24 Task 1 在 `backend/tests/test_feishu_auth.py` 补齐了 3 个最小 smoke 测试（authorize-url 契约 / callback 成功路径 mock HTTP / callback state 校验失败 → 400）作为标准后端 tests 目录的覆盖。完整状态覆盖（auto_bound / pending_candidates / unbind / error path）仍由 `tests/test_feishu_auth.py` 提供，未来里程碑可将两者合并至统一路径。

2. **HUMAN-UAT 未完成。** 22-02-T2 与 22-03-T2 的端到端人工验证依赖真实飞书 OAuth 环境（app_id/app_secret + staging domain + HR 扫码），截至 v1.2 milestone 归档时未完成。代码层面所有实现已就绪（commits 73c94ca + plan03 全部完成），仅等待 staging 环境签字。Verify as 可接受 tech debt，追踪至 `.planning/STATE.md` blockers。

3. **CSRF state 策略在 Plan 03 从 cookie 改为 localStorage + body.state_signed。** 这是 OAuth 跨域实现的演进（Plan 01/02 用 cookie，Plan 03 因 Vite proxy + 跨域 cookie 问题改为 body 传递 HMAC 签名 state）。当前 feishu_auth.py 同时支持两种路径：`signed_value = body.state_signed or request.cookies.get(OAUTH_STATE_COOKIE)`。HMAC 校验逻辑本身（`_verify_state`）保持不变，安全语义等价。

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s (OAuth subset)
- [x] `nyquist_compliant: true` set in frontmatter
- [ ] Final HUMAN-UAT sign-off（22-02-T2 + 22-03-T2 依赖 staging 飞书 OAuth 环境 — 可接受 v1.2 tech debt）

**Approval:** retroactively approved 2026-04-20（Phase 24 gap closure）
