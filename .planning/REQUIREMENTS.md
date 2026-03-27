# Requirements: v1.1 Audit Gap Closure

**Defined:** 2026-03-27
**Audit Source:** `.planning/v1.0-MILESTONE-AUDIT.md`
**Coverage:** 0/8 complete | 0/8 verified | 8 pending

## Milestone Goal

Close the v1.0 milestone audit gaps, repair the broken supported entrypaths, and restore enough verification traceability for a future re-audit to pass cleanly.

## Requirements

### Must

- [ ] **SEC-01**: The supported deployment path must require the actual non-local admin and HR password settings contract so operators cannot reach production-like deployments with default credentials through the documented path.
- [ ] **SEC-02**: The supported deployment path must require the actual non-local auth secret settings contract so operators cannot reach production-like deployments with a predictable signing secret through the documented path.
- [ ] **PIPE-01**: The primary quick aggregate UI entrypath must enforce upload limits while bytes stream from the client instead of buffering before the authoritative guardrail runs.
- [ ] **PIPE-02**: Oversized quick aggregate uploads on the supported UI path must fail with explainable API responses and no ambiguous persisted artifacts.
- [ ] **PIPE-03**: Upload hardening must carry formal verification evidence that the supported quick aggregate path preserves the current import-to-export pipeline contract.
- [ ] **OPS-01**: The repository must document one canonical deployment path whose environment contract actually wires into the implemented non-local guardrails.

### Should

- [ ] **VER-01**: Verified export regression work must expose machine-checkable requirement-completion metadata so future audits can confirm coverage without manual inference from prose summaries.
- [ ] **VER-02**: Phase summaries and verification artifacts must fail the evidence chain loudly when requirement-completion metadata is missing, rather than silently weakening audit confidence.

## Traceability

| Requirement | Priority | Phase | Status | Notes |
|-------------|----------|-------|--------|-------|
| SEC-01 | must | Phase 5 | Pending | Reset from archived v1.0 gap: documented deployment env names drifted from the guardrail settings contract |
| SEC-02 | must | Phase 5 | Pending | Reset from archived v1.0 gap: supported deployment path did not guarantee a non-default auth secret contract |
| OPS-01 | must | Phase 5 | Pending | Reset from archived v1.0 gap: canonical deployment workflow was documented, but its env wiring was incorrect |
| PIPE-01 | must | Phase 6 | Pending | Reset from archived v1.0 gap: the supported quick aggregate entrypath buffered uploads before the stream-time limit check |
| PIPE-02 | must | Phase 6 | Pending | Reset from archived v1.0 gap: oversized `/aggregate/stream` behavior was not proven on the primary UI path |
| PIPE-03 | must | Phase 7 | Pending | Reset from archived v1.0 gap: formal Phase 2 verification evidence was missing |
| VER-01 | should | Phase 7 | Pending | Carried forward from partial v1.0 audit status: Phase 3 summaries lacked machine-checkable requirements-completed metadata |
| VER-02 | should | Phase 7 | Pending | Carried forward from partial v1.0 audit status: audit automation could not confirm summary metadata coverage |

## Deferred Optional

- Windows Phase 3 reruns remain timeout-prone in this environment. Treat runtime splitting or timeout budgeting as follow-up debt after Phases 5-7 are planned and executed.
