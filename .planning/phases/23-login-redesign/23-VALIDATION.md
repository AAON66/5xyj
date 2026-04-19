---
phase: 23
slug: login-redesign
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright 1.59.1（已安装，见 `frontend/package.json`） |
| **Config file** | `frontend/playwright.config.ts` |
| **Quick run command** | `cd frontend && npm run test:e2e -- tests/e2e/login-redesign.spec.ts` |
| **Full suite command** | `cd frontend && npm run test:e2e` |
| **Estimated runtime** | 快速集 ~15s / 全量 ~60s |

**项目单元测试现状：** 前端目前没有 Jest/Vitest 单元测试（`frontend/src` 下无 `*.test.*` / `*.spec.*` 文件）。所有前端测试都是 Playwright E2E。本阶段保持此风格。

---

## Sampling Rate

- **After every task commit:** `cd frontend && npm run lint && npm run build`（TypeScript + Vite 编译通过）
- **After every plan wave:** `cd frontend && npm run test:e2e -- tests/e2e/login-redesign.spec.ts`
- **Before `/gsd-verify-work`:** `cd frontend && npm run test:e2e` 全量绿 + 人工 Safari 视觉验证 + 人工 reduced-motion 验证
- **Max feedback latency:** 15 秒（快速集）

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD-00-W0 | 00 | 0 | LOGIN-01/02/03/04 | — | N/A | E2E 测试文件脚手架 | `test -f frontend/tests/e2e/login-redesign.spec.ts` | ❌ W0 | ⬜ pending |
| TBD-LAYOUT | TBD | 1 | LOGIN-01 | — | N/A | Playwright viewport | `npx playwright test tests/e2e/login-redesign.spec.ts -g "layout"` | ❌ W0 | ⬜ pending |
| TBD-PARTICLE | TBD | 1 | LOGIN-02 | T-23-01（WebGL context 泄露） | renderer.dispose + forceContextLoss 调用 | Playwright DOM 断言 | `npx playwright test tests/e2e/login-redesign.spec.ts -g "particle"` | ❌ W0 | ⬜ pending |
| TBD-FALLBACK | TBD | 1 | LOGIN-03 | — | WebGL 不可用时降级不抛错 | Playwright + `page.addInitScript` stub getContext 返回 null | `npx playwright test tests/e2e/login-redesign.spec.ts -g "webgl fallback"` | ❌ W0 | ⬜ pending |
| TBD-DARK | TBD | 1 | LOGIN-04 | — | N/A | Playwright DOM 断言 + `evaluate()` 读取 `data-particle-color` | `npx playwright test tests/e2e/login-redesign.spec.ts -g "dark mode"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

> Planner 需把 Task ID 替换为真实 plan 号后再回填本表。

---

## Wave 0 Requirements

- [ ] `frontend/tests/e2e/login-redesign.spec.ts` — 新增，覆盖 LOGIN-01/02/03/04 的自动化断言
- [ ] 在 `ParticleWave.tsx` 暴露 `data-particle-color` 属性（让 Playwright 读取当前 uniform 值用于 LOGIN-04 验证）
- [ ] 评估在 `frontend/playwright.config.ts` 的 `projects` 数组加 webkit 项（可选，成本低，可让 Safari backdrop-filter 纳入自动化）

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 3D 粒子波浪实际渲染正确性（波形、跟随效果） | LOGIN-02 | Playwright 无法像素级断言 canvas 内容 | 在 `npm run dev` 下打开 `/login`，观察左侧画布：粒子呈波浪起伏；鼠标移动时中心区域粒子被推开呈现跟随；无闪烁、无伪影 |
| Safari 上 `backdrop-filter` 毛玻璃效果 | LOGIN-01 | Playwright 默认 Chromium，无 Safari | macOS Safari 实机打开登录页；确认右侧卡片有玻璃模糊质感；切换暗黑后仍有效 |
| 动画流畅度 60fps | LOGIN-02 | 需要 DevTools Performance Profile | Chrome DevTools → Performance → 录制 5s；帧率不低于 55fps，无 "Long task" 告警 |
| reduced-motion 降级 | LOGIN-02 / LOGIN-03 | 系统级偏好无法稳定 stub | macOS System Settings → Accessibility → Reduce motion 打开；刷新登录页；粒子应停止跟随或降级为静态 |

---

## Validation Sign-Off

- [ ] 所有任务有 `<automated>` verify 或 Wave 0 依赖
- [ ] Sampling 连续性：不允许连续 3 个任务无自动化验证
- [ ] Wave 0 覆盖所有 ❌ 项
- [ ] 未使用 watch 模式 flag
- [ ] Feedback latency < 15 秒
- [ ] `nyquist_compliant: true` 在 frontmatter 中置位

**Approval:** pending
