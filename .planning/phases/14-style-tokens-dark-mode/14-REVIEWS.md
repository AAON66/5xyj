---
phase: 14
reviewers: [codex]
reviewed_at: 2026-04-06T00:00:00Z
plans_reviewed: [14-01-PLAN.md, 14-02-PLAN.md, 14-03-PLAN.md, 14-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 14

## Codex Review

### Plan 14-01
**Summary**
This is the right foundation split for the phase: theme construction, mode state, token helpers, FOUC prevention, and layout wiring are in the right wave. The main weakness is bootstrap consistency: the head script, React provider, and root background handling are close, but not yet defined as one coherent source of truth.

**Strengths**
- Clear interfaces for Wave 2 consumers. `useSemanticColors`, `useCardStatusColors`, `getChartColors`, and `useThemeMode` make later page migration straightforward.
- Good attention to real browser issues: `localStorage` tampering is bounded, Safari/private-mode failures are considered, and FOUC is handled up front.
- Keeping Sider permanently dark is explicitly encoded instead of left to incidental token behavior.

**Concerns**
- `HIGH`: The planned `index.html` script sets `html/body` dark backgrounds, but the provider plan only updates `data-theme` and `localStorage`. If the user later switches back to light mode, those inline dark backgrounds can remain stale. That is an easy path to the exact "半白半黑" failure this phase is meant to prevent.
- `MEDIUM`: The research says React should bootstrap from `<html data-theme>`, but the plan's `readInitialMode()` reads `localStorage`/`matchMedia` again instead. That creates two boot paths that can diverge.
- `MEDIUM`: `getChartColors(isDark)` is based on fixed dark values, not live AntD token output. That can make table/status colors slightly inconsistent with components using `theme.useToken()`.

**Suggestions**
- Make React initialize from `document.documentElement.dataset.theme` first, then fall back only if absent.
- Move root background control to a tiny `data-theme` CSS rule or explicitly reset `html/body` background on every mode change.
- Memoize `buildTheme(mode)` in `main.tsx`, and validate `DARK_CHART_COLORS` against actual token output before locking them in.

**Risk Assessment**: `MEDIUM`

### Plan 14-02
**Summary**
This is a sensible low-risk migration wave. The file set matches the current hardcoded-color hotspots well, and the hook-vs-pure-function split is practical. The main issue is that verification is a bit too optimistic for a parallel wave.

**Strengths**
- The targeted files line up with the live color inventory in routed entry/core pages.
- Disjoint write scope from 14-03 is good; this is parallelizable without much merge risk.
- Using `useCardStatusColors` for border semantics is cleaner than repeating token unpacking in each page.

**Concerns**
- `MEDIUM`: Portal.tsx is exported but not actually routed in App.tsx. It is valid cleanup, but it is weaker evidence of user-visible success than the active routes.
- `LOW`: Only the last task runs `build`. In a parallel wave, type/build validation should happen once after the whole plan lands, not only in one subtask.
- `LOW`: The checks are mostly "grep these exact literals out." That works for today's files, but it is brittle against shorthand forms or newly introduced literals.

**Suggestions**
- Mark Portal.tsx as non-blocking cleanup if execution time is tight; prioritize active routes first.
- Add a wave-end `npm run build` after both 14-02 and 14-03 are merged.
- Use route-based smoke verification with actual current paths.

**Risk Assessment**: `LOW-MEDIUM`

### Plan 14-03
**Summary**
This is the hardest migration wave, and it correctly focuses on the real edge cases: module-level status maps, diff highlighting, and React Flow background tokens. The design is strong, but the acceptance criteria are not strict enough to prove the work is actually complete.

**Strengths**
- Good identification of non-hook contexts where plain token hooks cannot be used directly.
- PeriodCompare semantic mapping is thoughtful and consistent with the phase decisions.
- Explicitly tokenizing React Flow Background is the right call; that component is an easy place to miss dark-mode drift.

**Concerns**
- `HIGH`: The acceptance checks miss real literals that exist today. Examples: `#3370FF` and `#f0f0f0` in Compare.tsx, `#FFF1F0` in PeriodCompare.tsx, and the module-level status hexes in FeishuSync.tsx.
- `MEDIUM`: Moving top-level status/column config into components is correct, but if it is not wrapped in `useMemo`, table renders can churn more than necessary.
- `MEDIUM`: Same consistency risk as 14-01: fixed `chartColors` dark values may not exactly match AntD dark tokens.

**Suggestions**
- Replace the per-file literal grep lists with a generic hex audit for each touched file.
- Add explicit checks for the currently missed values above before calling the plan complete.
- Prefer memoized factory functions like `buildColumns(colors)` and `buildStatusMap(colors)` to keep stable references.

**Risk Assessment**: `MEDIUM`

### Plan 14-04
**Summary**
This is the right phase gate in principle, but it is currently the weakest plan. The cleanup idea is good, and the human checkpoint is necessary, but the audit script and manual checklist are both loose enough to produce false confidence.

**Strengths**
- Making the last wave non-autonomous is correct; UX-02 needs a real visual checkpoint.
- Deleting dead styles.css after proving zero imports is good cleanup.
- Adding a reusable hardcoded-color audit script is the right long-term move.

**Concerns**
- `HIGH`: `check-hardcoded-colors.sh` only catches narrow inline-style patterns. It will miss multiline style objects, `border: '1px solid #...'`, `stroke: '#...'`, and module constants.
- `HIGH`: The manual route checklist does not match the actual router in App.tsx. Real routes are `/aggregate`, `/anomaly-detection`, `/feishu-sync`, `/feishu-mapping/:configId`, `/workspace/admin`, and `/workspace/hr`; the checklist uses several invalid paths.
- `MEDIUM`: The checkpoint omits prerequisites: valid admin/HR access, seeded data for compare/anomaly pages, and a real configId for the Feishu mapping page.
- `MEDIUM`: The allowlist story is inconsistent. 14-01 intentionally introduces `#1F1F1F` in `index.html`, but 14-04's documented whitelist does not acknowledge it.

**Suggestions**
- Make the audit generic: scan `frontend/src` and `frontend/index.html` for `#[0-9A-Fa-f]{3,8}`, then subtract a very small explicit allowlist by file and value.
- Rewrite the human checklist against real routes from App.tsx, and state how to reach `/feishu-mapping/:configId`.
- Add a short prerequisites section: admin login, HR login, seeded batches/anomalies/compare data, one Feishu config.

**Risk Assessment**: `HIGH`

---

## Consensus Summary

### Agreed Strengths
- Wave structure is sound: infrastructure first (W1), parallel migration (W2), gate (W3)
- Hook/pure-function split (useSemanticColors vs getChartColors) is practical and well-designed
- FOUC prevention and Safari localStorage edge cases are addressed proactively
- Sider deep-dark permanence is explicitly encoded
- File ownership is disjoint across parallel plans

### Agreed Concerns (Single Reviewer — Treat as Findings)
1. **HIGH — FOUC script can leave stale inline backgrounds** when switching back to light mode (affects 14-01)
2. **HIGH — Acceptance criteria miss real hex literals** in Compare.tsx, PeriodCompare.tsx, FeishuSync.tsx (affects 14-03)
3. **HIGH — Audit script too narrow** to catch multiline styles, border shorthands, module constants (affects 14-04)
4. **HIGH — Manual route checklist uses invalid paths** not matching App.tsx router (affects 14-04)
5. **MEDIUM — Dual boot path divergence** between index.html script and React provider readInitialMode (affects 14-01)
6. **MEDIUM — chartColors fixed dark values** may drift from live AntD token output (affects 14-01, 14-03)
7. **MEDIUM — index.html #1F1F1F not in whitelist** of 14-04 audit (affects 14-04)

### Divergent Views
N/A — single reviewer. Consider adding Gemini or another CLI for independent cross-validation.
