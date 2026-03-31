---
phase: 8
slug: page-rebuild-ux-flow
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend) |
| **Config file** | `frontend/vite.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run --reporter=verbose && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run --reporter=verbose && npm run build`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | UI-06 | build | `npm run build` | ✅ | ⬜ pending |
| 08-01-02 | 01 | 1 | UI-07 | build | `npm run build` | ✅ | ⬜ pending |
| 08-01-03 | 01 | 1 | UI-07 | build | `npm run build` | ✅ | ⬜ pending |
| 08-02-01 | 02 | 1 | UI-08 | build | `npm run build` | ✅ | ⬜ pending |
| 08-02-02 | 02 | 1 | UI-05 | build | `npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Responsive layout at 1440x900 | UI-06 | Visual layout check | Resize browser to 1440x900, verify sidebar auto-collapses |
| Responsive layout at 1366x768 | UI-06 | Visual layout check | Resize browser to 1366x768, verify sidebar collapsed + tables scroll |
| Chinese text completeness | UI-07 | Visual scan for English strings | Navigate all pages, verify no English UI text remains |
| Steps workflow navigation | UI-08 | End-to-end flow | Complete upload→parse→verify→export and verify Steps reflect progress |
| Role-based menu filtering | UI-05 | Role switching | Log in as admin/hr/employee, verify menu items differ correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
