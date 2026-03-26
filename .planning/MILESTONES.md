# Milestones

## v1.0 Brownfield Hardening Baseline (Shipped: 2026-03-26)

**Phases completed:** 4 phases, 6 plans

**Key accomplishments:**

- Non-local auth startup now fails fast on default passwords and predictable auth secrets when the guardrail is correctly configured.
- Streamed upload enforcement now rejects oversized payloads during write-time and cleans up partial artifacts on the covered backend paths.
- Dual-template export verification now runs from repo-controlled fixtures or explicit configured paths.
- Supported local and deployment workflows are now explicit, and rescue tooling is isolated under `scripts/operations/rescue/`.

**Known gaps accepted at closeout:**

- The canonical deployment path is miswired: documented env names do not match the security guardrail settings contract, and `runtime_environment` is not explicitly turned non-local in the supported path.
- The primary quick-aggregate UI path goes through `/api/v1/aggregate/stream`, which buffers uploads before the Phase 2 streamed limit enforcement runs.
- Phase 1 and Phase 2 do not have formal `VERIFICATION.md` artifacts, so the milestone audit remains `gaps_found`.
- The full Phase 3 Windows rerun remains timeout-prone and should be revisited in the next milestone.

**Archives:**

- `milestones/v1.0-ROADMAP.md`
- `milestones/v1.0-REQUIREMENTS.md`
- `v1.0-MILESTONE-AUDIT.md`

---
