---
phase: 7
slug: design-system-ui-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend), pytest 7.x (backend — no changes expected) |
| **Config file** | `frontend/vitest.config.ts` or "none — Wave 0 installs" |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run && cd ../backend && python -m pytest` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | UI-01 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 07-01-02 | 01 | 1 | UI-02 | build + visual | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 07-02-01 | 02 | 2 | UI-01 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 07-02-02 | 02 | 2 | UI-03 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 07-02-03 | 02 | 2 | UI-04 | build + visual | `cd frontend && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `npm install antd @ant-design/icons@^5` — install Ant Design dependencies
- [ ] `frontend/src/theme/themeConfig.ts` — ConfigProvider theme token configuration
- [ ] `frontend/vitest.config.ts` — if vitest not yet configured

*Note: This is primarily a UI migration phase — build success is the primary automated gate.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Feishu-inspired visual theme | UI-02 | Visual quality is subjective | Open each page, verify card-based layout, #3370FF accent, #F5F6F7 background |
| Page transition animations | UI-03 | Animation smoothness requires visual check | Navigate between pages, verify fade-in transitions without jarring reloads |
| Premium design details | UI-04 | Design quality is subjective | Check spacing, scrolling behavior, background details across pages |
| Sidebar collapse behavior | UI-02 | Interaction pattern | Click collapse button, verify icon-only mode and smooth transition |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
