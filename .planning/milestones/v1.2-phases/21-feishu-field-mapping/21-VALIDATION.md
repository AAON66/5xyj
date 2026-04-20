---
phase: 21
slug: feishu-field-mapping
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-15
updated: 2026-04-20
---

# Phase 21 — Validation Strategy

> Per-phase validation contract, retroactively aligned with delivered tasks during v1.2 gap closure (Phase 24).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (backend) + Playwright 1.59.1 (frontend E2E) + TypeScript strict + ESLint (frontend static) |
| **Config file** | `backend/pyproject.toml` + `frontend/playwright.config.ts` |
| **Quick run command** | `cd /Users/mac/PycharmProjects/5xyj && .venv/bin/python -m pytest backend/tests/test_mapping_api.py -q` |
| **Full suite command** | `.venv/bin/python -m pytest backend/tests/ -q && cd frontend && npm run lint && npm run build && npm run test:e2e` |
| **Estimated runtime** | ~10s backend, ~60s frontend E2E |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest backend/tests/test_mapping_api.py -q`
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10s backend / 60s full suite

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| `21-01-T1` | 01 | 0 | FMAP-02 | — | Schema accepts optional ui_type without leaking internals | 后端单元（TDD RED→GREEN）| `.venv/bin/python -m pytest backend/tests/test_mapping_api.py -q` | ✅ | ✅ green |
| `21-01-T2` | 01 | 1 | FMAP-01, FMAP-02 | T-21-01 (Tampering) | SuggestMappingRequest Pydantic 校验拒绝畸形请求 | 后端单元 | `.venv/bin/python -m pytest backend/tests/test_mapping_api.py -q` | ✅ | ✅ green |
| `21-01-T3` | 01 | 1 | FMAP-04 | — | 前端服务类型与后端契约对齐，防止 runtime 反序列化错误 | 前端类型/lint | `cd frontend && npx tsc --noEmit && npm run lint` | ✅ | ✅ green |
| `21-02-T1` | 02 | 2 | FMAP-02, FMAP-04 | — | ReactFlow 节点渲染不向 DOM 注入未转义飞书字段名 | 前端静态+E2E | `cd frontend && npm run lint && npm run build && npx playwright test tests/e2e/feishu-field-mapping.spec.ts` | ✅ | ✅ green |
| `21-02-T2` | 02 | 2 | FMAP-03 | T-21-04 (Tampering) | 保存前两步 Modal 给用户 UX 提醒（非安全控制，文档化 accept） | 前端静态+E2E | 同 21-02-T1 | ✅ | ✅ green |
| `21-02-T3` | 02 | 2 | FMAP-01..04 | T-21-05 (Spoofing) | 人工验证字段类型 Tag / 连线样式 / Modal 流程 | human-verify | 21-HUMAN-UAT.md steps 1–4 | ✅ | ⚠️ pending (UAT) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky / awaiting manual*

> 注：Task ID 与 `21-01-PLAN.md` / `21-02-PLAN.md` 的 `<task>` 节点一一对应（T1/T2/T3）。Status 依据 `21-01-SUMMARY.md` commit 1c2732f/e0160c0/2bc68da 与 `21-02-SUMMARY.md` commit c928548 记录的自动化验证结果。21-02-T3 的最终 UAT 签字留 pending，追踪于 `21-HUMAN-UAT.md`，这是已知的 v1.2 tech debt（可接受）。

---

## Wave 0 Requirements

- [x] `backend/tests/test_mapping_api.py` — suggest-mapping endpoint 覆盖（FMAP-01/02/04, 6 个用例）
- [x] `backend/app/schemas/feishu.py` — FeishuFieldInfo.ui_type 字段
- [x] `frontend/src/services/feishu.ts` — MappingSuggestion / SuggestMappingResponse / suggestMapping 类型与调用

*Existing backend pytest infrastructure + frontend Vite/ESLint/Playwright stack covers all phase requirements; no new framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Covered By |
|----------|-------------|------------|-------------------|------------|
| 飞书字段类型 Tag 视觉验证 | FMAP-02 | 视觉 UI 颜色/Tooltip 需要人眼 | 打开映射页，确认每个飞书字段节点有彩色 Tag 且悬停 Tooltip 显示类型名 + type 枚举 | 21-02-T3 / 21-HUMAN-UAT step 1 |
| 自动匹配连线样式验证 | FMAP-04 | ReactFlow 虚实线渲染视觉效果 | 点击自动匹配，确认高置信度(>=0.9)实线 / 低置信度(<0.9)虚线，可手动删除/新增连线 | 21-02-T3 / 21-HUMAN-UAT step 2 |
| 关键字段警告 Modal 验证 | FMAP-03 | Modal 交互与颜色语义 | 不映射 person_name 点保存，确认弹出警告 Modal，红色=必填、黄色=建议，两个按钮可用 | 21-02-T3 / 21-HUMAN-UAT step 3 |
| 映射预览 Modal 验证 | FMAP-03 | Modal 内容完整性 | 完成映射后点保存，确认预览 Modal 展示完整映射关系表（系统字段 \| 中文名 \| 飞书字段 \| 字段类型） | 21-02-T3 / 21-HUMAN-UAT step 4 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s (full suite)
- [x] `nyquist_compliant: true` set in frontmatter
- [ ] Final HUMAN-UAT sign-off (tracked in `21-HUMAN-UAT.md`; 4/4 steps currently pending — accepted v1.2 tech debt)

**Approval:** retroactively approved 2026-04-20（Phase 24 gap closure）
