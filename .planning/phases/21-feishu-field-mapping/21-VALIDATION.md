---
phase: 21
slug: feishu-field-mapping
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + vitest/manual (frontend) |
| **Config file** | `backend/pytest.ini` or `pyproject.toml` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v && cd ../frontend && npm run lint && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | FMAP-01 | — | N/A | integration | `pytest tests/test_feishu_fields.py` | ❌ W0 | ⬜ pending |
| 21-01-02 | 01 | 1 | FMAP-02 | — | N/A | unit | `pytest tests/test_feishu_fields.py` | ❌ W0 | ⬜ pending |
| 21-02-01 | 02 | 1 | FMAP-04 | — | N/A | unit | `pytest tests/test_field_suggest.py` | ❌ W0 | ⬜ pending |
| 21-03-01 | 03 | 2 | FMAP-02 | — | N/A | manual | frontend visual check | N/A | ⬜ pending |
| 21-03-02 | 03 | 2 | FMAP-04 | — | N/A | manual | frontend visual check | N/A | ⬜ pending |
| 21-03-03 | 03 | 2 | FMAP-03 | — | N/A | manual | frontend visual check | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_feishu_fields.py` — stubs for FMAP-01, FMAP-02 (ui_type 透传)
- [ ] `tests/test_field_suggest.py` — stubs for FMAP-04 (同义词匹配建议 API)

*Existing infrastructure covers frontend lint/build checks.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 飞书字段节点显示类型 Badge + Tooltip | FMAP-02 | 视觉 UI 验证 | 打开映射页，确认每个飞书字段节点有彩色 Tag 且悬停显示类型 |
| 自动连线高/低置信度样式 | FMAP-04 | ReactFlow 视觉效果 | 点击自动匹配，确认高置信度实线、低置信度虚线 |
| 未映射关键字段警告 Modal | FMAP-03 | Modal 交互验证 | 不映射 person_name，点保存，确认弹出警告 Modal |
| 预览 Modal 汇总表 | FMAP-03 | Modal 内容验证 | 完成映射后点保存，确认预览 Modal 显示完整映射关系表 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
