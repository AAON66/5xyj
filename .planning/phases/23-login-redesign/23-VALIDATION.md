---
phase: 23
slug: login-redesign
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-19
updated_by_planner: 2026-04-19
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright 1.59.1（已安装，见 `frontend/package.json`） |
| **Config file** | `frontend/playwright.config.ts`（`baseURL = http://127.0.0.1:4173`, strictPort） |
| **Quick run command** | `cd frontend && npm run test:e2e -- tests/e2e/login-redesign.spec.ts` |
| **Full suite command** | `cd frontend && npm run test:e2e` |
| **Estimated runtime** | 快速集 ~15s / 全量 ~60s |

**项目单元测试现状：** 前端目前没有 Jest/Vitest 单元测试（`frontend/src` 下无 `*.test.*` / `*.spec.*` 文件）。所有前端测试都是 Playwright E2E。本阶段保持此风格。

---

## Sampling Rate

- **After every task commit（快速反馈，满足 15s 预算）:** `cd frontend && npm run lint && npx tsc --noEmit`（TypeScript + eslint 编译通过，不跑 build）
- **After every plan wave:** `cd frontend && npm run test:e2e -- tests/e2e/login-redesign.spec.ts`（仅新增集，5 个测试）
- **Acceptance gate (Plan 03 Task 3 checkpoint 之前)：** `cd frontend && npm run build && npm run test:e2e`（全量绿 + 独立 chunk）
- **Before `/gsd-verify-work`:** Acceptance gate 全绿 + 人工 Safari 视觉验证 + 人工 reduced-motion 验证
- **Max feedback latency:** 15 秒（快速集），Acceptance gate 约 60s 允许超出（不阻塞开发循环，只在 checkpoint 之前跑）

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 23-01-T1 | 01 | 1 | LOGIN-03 | T-23-02（three 供应链）| pin 精确版本 + npm audit | 依赖验证 | `cd frontend && grep -E '"three":\\s*"0.184.0"' package.json && npm audit --audit-level=high --production` | ✅ W1 | ⬜ pending |
| 23-01-T2 | 01 | 1 | LOGIN-03 | T-23-03（XSS）| 禁用 dangerouslySetInnerHTML | 静态 grep + tsc | `cd frontend && grep -Fq "export function CssGradientBackground" src/components/CssGradientBackground.tsx && ! grep -Fq dangerouslySetInnerHTML src/components/CssGradientBackground.tsx && npx tsc --noEmit` | ✅ W1 | ⬜ pending |
| 23-01-T3 | 01 | 0 | LOGIN-01/02/03/04 | — | N/A | Wave 0 E2E 脚手架 | `cd frontend && test -f tests/e2e/login-redesign.spec.ts && npx tsc --noEmit` | ✅ W1 | ⬜ pending |
| 23-02-T1 | 02 | 2 | LOGIN-02 / LOGIN-04（粒子色）| T-23-01（WebGL context 泄露）| cleanup 5 件齐全 + forceContextLoss | 静态 grep + Playwright DOM | `cd frontend && grep -Fq "renderer.forceContextLoss()" src/components/ParticleWave.tsx && npx playwright test tests/e2e/login-redesign.spec.ts -g "particle"` | ❌ (Plan 03 集成后) | ⬜ pending |
| 23-03-T1 | 03 | 3 | LOGIN-01（品牌文本部分）| T-23-03（XSS）| 纯文本渲染，无 inner HTML | 静态 grep + tsc | `cd frontend && grep -Fq "export function BrandPanel" src/components/BrandPanel.tsx && grep -Fq "from 'antd'" src/components/BrandPanel.tsx && npx tsc --noEmit` | ✅ W1 | ⬜ pending |
| 23-03-T2-layout-desktop | 03 | 3 | LOGIN-01 | — | N/A | Playwright viewport 1440×900 | `cd frontend && npx playwright test tests/e2e/login-redesign.spec.ts -g "layout — desktop split"` | ✅ W1 | ⬜ pending |
| 23-03-T2-layout-mobile | 03 | 3 | LOGIN-01 | — | N/A | Playwright viewport 375×812 | `cd frontend && npx playwright test tests/e2e/login-redesign.spec.ts -g "layout — mobile form-only"` | ✅ W1 | ⬜ pending |
| 23-03-T2-particle | 03 | 3 | LOGIN-02 | T-23-01 | Suspense fallback CssGradientBackground | Playwright DOM | `cd frontend && npx playwright test tests/e2e/login-redesign.spec.ts -g "particle"` | ✅ W1 | ⬜ pending |
| 23-03-T2-fallback | 03 | 3 | LOGIN-03 | — | WebGL 不可用时降级不抛错 | Playwright + addInitScript stub getContext → null | `cd frontend && npx playwright test tests/e2e/login-redesign.spec.ts -g "webgl fallback"` | ✅ W1 | ⬜ pending |
| 23-03-T2-dark | 03 | 3 | LOGIN-04 | — | N/A | Playwright DOM + evaluate(data-particle-color)；localStorage key = `'theme-mode'` | `cd frontend && npx playwright test tests/e2e/login-redesign.spec.ts -g "dark mode"` | ✅ W1 | ⬜ pending |
| 23-03-T3 | 03 | 3 | LOGIN-01/02/03/04 | T-23-01, T-23-08 | 粒子/玻璃态/降级/认证回归全部人工通过 | 人工 checkpoint（`npm run dev -- --host 127.0.0.1 --port 4173`） | 用户输入 `approved` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

> Task ID 命名：`{phase}-{plan}-T{task_index}`（checkpoint 任务以 `T3` 结尾）；若单 task 对应多个 E2E grep 断言（如 23-03-T2 一次性覆盖 5 个断言），用 `-{assertion_slug}` 区分。
> 每行 Per-Task 条目对应 `login-redesign.spec.ts` 中一个独立 `test()`；5 行 E2E assertion（`23-03-T2-layout-desktop`、`-layout-mobile`、`-particle`、`-fallback`、`-dark`）与 Plan 01 Task 3 所定义的 5 个 `test()` 一一对应。
> Status 列在执行期间由 executor / checker 逐行更新。

---

## Wave 0 Requirements (由 Plan 01 Task 3 承载)

- [x] `frontend/tests/e2e/login-redesign.spec.ts` — 新增，覆盖 LOGIN-01/02/03/04 的 5 个 `test()` 断言
- [x] 在 `ParticleWave.tsx` 暴露 `data-particle-color` 属性（Plan 02 Task 1 实现）
- [x] 在 `ThemeModeProvider.tsx:14` 确认 STORAGE_KEY = `'theme-mode'`（已由 Plan 01 Task 3 的 dark-mode 测试正确使用）
- [x] 每个 test 在 `test.beforeEach` 清理 `'social-security-auth-session'` 以避免 Login.tsx:118-120 的早返回
- [ ] 评估在 `frontend/playwright.config.ts` 的 `projects` 数组加 webkit 项（可选，成本低，可让 Safari backdrop-filter 纳入自动化；本阶段不强制）

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Covered By |
|----------|-------------|------------|-------------------|------------|
| 3D 粒子波浪实际渲染正确性（波形、跟随效果） | LOGIN-02 | Playwright 无法像素级断言 canvas 内容 | 开 `npm run dev -- --host 127.0.0.1 --port 4173` 打开 /login，观察左侧画布：粒子呈波浪起伏；鼠标移动时中心区域粒子被推开呈现跟随；无闪烁、无伪影 | 23-03-T3 步骤 1 |
| Safari 上 `backdrop-filter` 毛玻璃效果 | LOGIN-01 / LOGIN-04 | Playwright 默认 Chromium，无 Safari | macOS Safari 实机打开 `http://127.0.0.1:4173/login`；确认右侧卡片有玻璃模糊质感；切换暗黑后仍有效 | 23-03-T3 步骤 2 |
| 动画流畅度 60fps | LOGIN-02 | 需要 DevTools Performance Profile | Chrome DevTools → Performance → 录制 5s；帧率不低于 55fps，无 "Long task" 告警 | 23-03-T3 性能抽检 |
| reduced-motion 降级 | LOGIN-02 / LOGIN-03 | 系统级偏好无法稳定 stub | macOS System Settings → Accessibility → Reduce motion 打开；刷新登录页；粒子应停止跟随或降级为静态 | 23-03-T3 步骤 5 |
| 认证回归（账号/员工/飞书全流程）| LOGIN-01..04 的不回归要求 | 涉及真实后端与 OAuth；Phase 22 全量回归脚本覆盖 | 现有测试账号登录 → 工作台；员工查询 Tab；飞书 OAuth（如启用）| 23-03-T3 步骤 6 |
| 1024px 断点立即切换 60:40 / 50:50 | LOGIN-01 | DevTools resize 操作人工观察 | Chrome DevTools 切 1023px（50:50）→ 1024px（60:40）；验证 matchMedia 精确触发 | 23-03-T3 步骤 3 |

---

## Validation Sign-Off

- [x] 所有任务有 `<automated>` verify 或 Wave 0 依赖
- [x] Sampling 连续性：不允许连续 3 个任务无自动化验证（满足 — Plan 01 3/3 自动化，Plan 02 1/1 自动化，Plan 03 Task 1/2 自动化、Task 3 checkpoint 人工）
- [x] Wave 0 覆盖所有 ❌ 项（Plan 01 Task 3 创建 E2E 文件 + Plan 02 Task 1 暴露 data-particle-color）
- [x] 未使用 watch 模式 flag
- [x] Feedback latency < 15 秒（快速集）；Acceptance gate 约 60s 仅在 checkpoint 之前跑，不阻塞开发循环
- [x] `nyquist_compliant: true` 已置位 frontmatter 与 3 个 PLAN 文件
- [x] Per-Task Map 5 行 E2E 断言（layout-desktop / layout-mobile / particle / fallback / dark）与 Plan 01 Task 3 的 5 个 `test()` 一一对应

**Approval:** pending executor
