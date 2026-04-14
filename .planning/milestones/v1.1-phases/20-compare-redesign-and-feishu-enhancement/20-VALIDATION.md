---
phase: 20
slug: compare-redesign-and-feishu-enhancement
status: passed
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-09
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for compare diff UX and Feishu runtime settings.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + ESLint + TypeScript/Vite build + Playwright |
| **Config file** | `backend/pytest.ini` (implicit via pytest discovery), `frontend/package.json`, `frontend/playwright.config.ts` |
| **Quick run command** | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_compare_api.py backend/tests/test_feishu_settings_api.py -q && cd frontend && ./node_modules/.bin/eslint src/services/compare.ts src/components/CompareWorkbookDiff.tsx src/pages/Compare.tsx src/pages/PeriodCompare.tsx src/services/feishu.ts src/hooks/useFeishuFeatureFlag.ts src/pages/FeishuSettings.tsx src/pages/FeishuSync.tsx tests/e2e/compare-diff.spec.ts tests/e2e/feishu-settings.spec.ts` |
| **Full suite command** | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_compare_api.py backend/tests/test_feishu_settings_api.py -q && cd frontend && npm run lint && npm run build && npm run test:e2e` |
| **Estimated runtime** | ~7 minutes |

---

## Sampling Rate

- **After every task commit:** Run the task-specific pytest/eslint command listed below
- **After every plan wave:** Run the quick run command
- **Before `/gsd-verify-work`:** Full suite must be green, including compare/feishu Playwright coverage
- **Max feedback latency:** ~7 minutes

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | COMP-01 | T-20-01 | period compare 过滤和分页不会改变差异计数或左右值对齐关系 | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_compare_api.py -q -k "period"` | ✅ | ✅ green |
| 20-01-02 | 01 | 1 | COMP-01 | T-20-02 | compare export/batch compare 现有合同在新 schema 下不回归 | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_compare_api.py -q` | ✅ | ✅ green |
| 20-02-01 | 02 | 2 | COMP-01 | T-20-03 | workbook diff viewer 左右滚动同步且差异单元格高亮稳定 | eslint | `cd /Users/mac/PycharmProjects/5xyj/frontend && ./node_modules/.bin/eslint src/components/CompareWorkbookDiff.tsx src/pages/PeriodCompare.tsx src/pages/Compare.tsx src/services/compare.ts` | ✅ | ✅ green |
| 20-02-02 | 02 | 2 | COMP-01 | T-20-04 | 浏览器级 compare 页面可分页浏览 500+ 数据窗口且保持左右表格对齐 | e2e | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run test:e2e -- compare-diff.spec.ts` | ✅ | ✅ green |
| 20-03-01 | 03 | 1 | FEISHU-01 | T-20-05 | 飞书运行时设置更新后，effective settings 在 feature flags/auth/sync 中统一生效 | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_feishu_settings_api.py -q -k "runtime or feature"` | ✅ | ✅ green |
| 20-03-02 | 03 | 1 | FEISHU-01 | T-20-06 | secret 不被回显，admin 以外无法写入运行时凭证 | pytest | `cd /Users/mac/PycharmProjects/5xyj && python3 -m pytest backend/tests/test_feishu_settings_api.py -q` | ✅ | ✅ green |
| 20-04-01 | 04 | 2 | FEISHU-01 | T-20-07 | settings 页保存后会刷新 flags，sync 页不会继续显示旧状态 | eslint | `cd /Users/mac/PycharmProjects/5xyj/frontend && ./node_modules/.bin/eslint src/services/feishu.ts src/hooks/useFeishuFeatureFlag.ts src/pages/FeishuSettings.tsx src/pages/FeishuSync.tsx` | ✅ | ✅ green |
| 20-04-02 | 04 | 02 | FEISHU-01 | T-20-08 | 浏览器级 admin 配置流不会泄露 secret，且移动端仍可完成编辑与 sync config 管理 | e2e | `cd /Users/mac/PycharmProjects/5xyj/frontend && npm run test:e2e -- feishu-settings.spec.ts` | ✅ | ✅ green |

*Status: ⬜ planned · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/test_compare_api.py` — 现有 compare API 测试可承载分页/过滤/导出回归
- [x] `frontend/playwright.config.ts` — 现有 Playwright 基础设施可承载 compare/feishu route-mocked 场景
- [x] `frontend/package.json` — lint/build/e2e 命令已存在，无需新增脚手架
- [x] `frontend/src/pages/Compare.tsx` / `frontend/src/pages/PeriodCompare.tsx` — 两页均已接上同一 compare service，可复用共享 viewer
- [x] `frontend/src/pages/FeishuSettings.tsx` / `frontend/src/pages/FeishuSync.tsx` — 飞书配置与同步页面骨架已存在，可直接增强

*Existing infrastructure covers the phase once backend settings persistence and new e2e specs are added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 真实飞书租户凭证更新后立即执行 OAuth / 字段拉取 / 同步 smoke test | FEISHU-01 | 本地测试环境没有稳定可复用的真实租户与凭证轮转场景 | 在 staging 以 admin 身份保存一组真实 app id/secret，确认设置页显示“已配置”，随后分别验证 OAuth authorize-url、字段发现、一次 push/pull smoke test |
| 500+ 员工数据窗口在真实浏览器里的滚动观感 | COMP-01 | route-mocked e2e 能验证结构和行为，但不能完全替代视觉/滚动体验主观检查 | 使用 seeded 500+ compare 数据集打开月度对比页，检查双面板滚动同步、表头冻结和切页后状态保持 |

---

## Validation Sign-Off

- [x] All planned tasks have automated verify targets
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers compare + feishu 两条主链路
- [x] No watch-mode flags
- [x] Feedback latency < 45s for task-level checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** executed and passed
