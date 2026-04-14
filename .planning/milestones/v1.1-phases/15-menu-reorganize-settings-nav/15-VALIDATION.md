---
phase: 15
slug: menu-reorganize-settings-nav
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend) |
| **Config file** | `frontend/vite.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | UX-04 | — | N/A | manual | Browser check: menu groups visible | — | ⬜ pending |
| 15-01-02 | 01 | 1 | UX-04 | — | N/A | unit | `cd frontend && npx vitest run` | ❌ W0 | ⬜ pending |
| 15-02-01 | 02 | 1 | UX-04 | — | N/A | manual | Browser check: localStorage persistence | — | ⬜ pending |
| 15-03-01 | 03 | 2 | UX-05 | — | N/A | manual | Browser check: settings search works | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Menu groups render correctly with icons | UX-04 | Visual layout verification | Open app, verify 3 groups visible in sidebar |
| Collapse/expand state persists across navigation | UX-04 | Requires browser interaction | Collapse a group, navigate away, return — group stays collapsed |
| Settings search filters cards | UX-05 | Requires browser interaction | Type keyword in search box, verify non-matching cards hidden |
| Settings search highlights matching text | UX-05 | Visual verification | Type keyword, verify highlight styling on matching cards |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
