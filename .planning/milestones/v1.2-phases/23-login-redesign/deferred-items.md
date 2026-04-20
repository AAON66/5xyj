# Phase 23 Deferred Items

Discoveries made during execution that are **out of scope** for Phase 23 (login redesign) and should be addressed in a dedicated phase.

## Pre-existing E2E failures (unrelated to Phase 23 changes)

Discovered during Plan 03 Task 2 acceptance gate (`npm run test:e2e` full regression).

**Verification:** Each failure was reproduced against the ORIGINAL `Login.tsx` (pre-Phase 23) by stashing the Plan 03 Task 2 changes and rerunning. All 13 failures persisted → **not introduced by Phase 23**.

| # | Test | File | Likely cause |
|---|------|------|--------------|
| 1 | `PeriodCompare renders shared diff viewer and paginates on the server` | `compare-diff.spec.ts:326` | Backend / shared diff viewer route regression |
| 2 | `Compare reuses the shared diff viewer and keeps local filters on the current page` | `compare-diff.spec.ts:363` | Same as 1 |
| 3 | `Feishu settings save flow refreshes sync state without exposing the secret` | `feishu-settings.spec.ts:248` | Feishu settings route regression |
| 4 | `Feishu settings mobile drawer still supports creating a sync config` | `feishu-settings.spec.ts:282` | Same as 3 |
| 5 | `FeishuSync shows a settings CTA when runtime sync is disabled` | `feishu-settings.spec.ts:300` | Same as 3 |
| 6 | `simple aggregate mobile flow submits burden source and fusion rule payload` | `fusion-aggregate.spec.ts:258` | Fusion aggregate mobile flow regression |
| 7 | `mobile dashboard uses stacked cards and drawer navigation closes after route change` | `responsive.spec.ts:616` | Mobile dashboard `.ant-card` filter for `导入批次` not visible after login |
| 8 | `employee self-service renders mobile card flow with latest record expanded by default` | `responsive.spec.ts:636` | Employee self-service mobile regression |
| 9 | `data management mobile filter drawer keeps draft state until apply` | `responsive.spec.ts:650` | Data management mobile drawer regression |
| 10 | `mobile workflow pages expose a single sticky primary action and results page switches to next step after validation` | `responsive.spec.ts:678` | Mobile workflow regression |
| 11 | `compare page remains operable on compact viewport and can load compare results` | `responsive.spec.ts:700` | Compare page viewport regression |
| 12 | `period compare keeps fixed columns and horizontal scrolling on narrow screens` | `responsive.spec.ts:714` | Period compare responsive regression |
| 13 | `feishu settings remains operable on tablet and phone widths` | `responsive.spec.ts:731` | Feishu settings responsive regression |

**Suggested follow-up phase:** A dedicated "Responsive + post-auth route regression" phase should:

1. Verify whether all 13 failures share a common root cause (likely a shared helper that injects an authenticated session)
2. Audit the mock/fixture setup for these `-auth-session` seeded tests — several of them mount dashboard / settings / compare routes that depend on data that may no longer be seeded identically
3. Triage whether the regression was introduced by Phase 22 (the most recent completed phase) or earlier

**Phase 23 impact:** Zero. Plan 01 Wave 0 login-redesign.spec.ts 5/5 PASS. Plan 03 Task 2 acceptance criteria are met by the 5-test fast-feedback gate + build chunk splitting (`dist/assets/ParticleWave-*.js` confirmed present).
