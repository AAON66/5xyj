---
phase: 16
reviewers: [codex]
reviewed_at: 2026-04-07T08:00:00Z
plans_reviewed: [16-01-PLAN.md, 16-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 16

## Codex Review

**Plan 16-01: Backend**

**Summary**
Plan 16-01 is pointed at the right backend gaps and the wave ordering is good, but it is still incomplete for the actual frontend dependency chain. It fixes the obvious `must_change_password` bugs and adds the missing self-service endpoint, yet it does not repair the authenticated-profile contract that the frontend already relies on after reload.

**Strengths**
- It targets real defects already present in user_service.py.
- The dependency order is correct: backend API first, frontend second.
- The self-protection rules match D-11 and are backed by tests.
- It stays within scope and does not introduce unnecessary dependencies.

**Concerns**
- `HIGH`: The plan does not include fixing `/auth/me`. Current auth.py returns `display_name=role_display_name(...)` and drops the persisted `must_change_password`; meanwhile AuthProvider.tsx overwrites session state from that payload on restore. That will break forced-password UX after refresh.
- `HIGH`: The plan assumes `change-password` works for any authenticated user, but employee auth currently comes from three-factor verification and employee portal access; there is no employee password-backed `User` record to change.
- `MEDIUM`: The D-11 invariant is planned only at endpoint level. Service methods in user_service.py would still be callable elsewhere without that protection.
- `MEDIUM`: The tests miss the `/auth/me` regression path entirely, so the suite would still pass while the frontend remains broken on reload.

**Suggestions**
- Add `/auth/me` repair into 16-01: return real `display_name` and `must_change_password` for admin/hr, and explicitly define employee behavior.
- Clarify ACCT-04 scope now: either it is admin/hr-only, or Phase 16 needs an employee credential model first.
- Add backend tests for `/auth/me` for admin, hr, and employee.
- Consider moving self-protection into a shared service guard so future routes cannot bypass it.
- Consider making username immutable in backend too, since UI intends to disable editing but user_service.py still allows it.

**Risk Assessment**
`MEDIUM-HIGH`. The main tasks are correct, but two missing contract issues, `/auth/me` and employee password scope, can still block the whole phase.

---

**Plan 16-02: Frontend**

**Summary**
Plan 16-02 matches the UI decisions well and uses the existing app structure cleanly, but it depends on backend/session behavior that is not yet covered by Plan 16-01. The page itself is straightforward; the risky part is auth-state synchronization and role scoping.

**Strengths**
- It follows the current route/layout structure in App.tsx and MainLayout.tsx.
- Reusing AntD Table + Modal CRUD is the right level of complexity.
- The admin-only `/users` route is correctly separated from shared authenticated layout concerns.
- The non-autonomous checkpoint is appropriate for a user-facing auth flow.

**Concerns**
- `HIGH`: The plan does not say how a successful password change updates local auth state. Current session state is held in AuthProvider.tsx and refreshed from AuthProvider.tsx; without an explicit session update or refetch, the forced modal can stay stuck or reappear.
- `HIGH`: It adds "修改密码" into the shared header menu in MainLayout.tsx, but that layout is also used by employee routes. Employee sessions are not password-backed under the current backend model.
- `MEDIUM`: Error handling is underspecified. Duplicate username `409`, wrong old password `400`, and self-protection `403` should produce form-level feedback, not just generic toasts.
- `MEDIUM`: Verification is too light. `npx tsc --noEmit` plus manual checks does not cover the repo-required `lint`/`build`, and it misses the critical refresh scenario for forced password change.
- `LOW`: Deriving `currentUserId` from the table payload is workable now, but comparing by `username` or returning `user_id` from `/auth/me` would be cleaner.

**Suggestions**
- Add an explicit auth-session sync step after password change: update local session or refetch `/auth/me`.
- Gate the header "修改密码" entry to roles that actually have password accounts, unless Phase 16 also changes employee auth.
- Add explicit UX handling for `400/403/409` using the existing API error normalization path.
- Expand verification to include `npm run lint`, `npm run build`, and the flow: `must_change_password=true -> reload -> still blocked -> change password -> reload cleared`.

**Risk Assessment**
`MEDIUM`. The UI work is manageable, but auth/session edge cases can create broken flows unless the backend contract is tightened first.

---

## Consensus Summary

Since only one external reviewer (Codex) was available, this section reflects Codex's independent assessment.

### Agreed Strengths
- Correct wave ordering (backend first, frontend second)
- D-11 self-protection properly planned with tests
- Zero new dependencies, stays within scope
- Table + Modal CRUD pattern is appropriate

### Agreed Concerns

1. **HIGH — `/auth/me` endpoint does not return `must_change_password`:** The current `/auth/me` endpoint drops `must_change_password` from its response. After page refresh, AuthProvider refetches from `/auth/me` and overwrites local session state, which would break the forced-change-password modal flow. Plan 16-01 must fix this.

2. **HIGH — Employee role scoping for ACCT-04:** The `change-password` endpoint assumes a password-backed User record, but employees authenticate via three-factor verification (工号+身份证+姓名), not username/password. The "修改密码" header menu item would appear for employee sessions too. Need to scope ACCT-04 to admin/hr only, or hide the menu item for employees.

3. **HIGH — Auth session sync after password change:** Plan 16-02 Task 2 mentions updating `writeAuthSession` but the plan doesn't address how AuthProvider's in-memory state stays consistent. Need explicit refetch or event-based sync.

4. **MEDIUM — Error handling specificity:** Duplicate username (409), wrong old password (400), and self-protection (403) should produce form-level feedback, not generic toasts.

### Divergent Views
N/A — single reviewer.
