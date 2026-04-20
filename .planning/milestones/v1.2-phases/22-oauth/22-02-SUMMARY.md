---
phase: 22-oauth
plan: 02
subsystem: frontend-oauth
tags: [feishu, oauth, login, candidate-modal]
dependency_graph:
  requires: [22-01]
  provides: [feishu-oauth-frontend-flow, candidate-select-modal]
  affects: [Login.tsx, feishu.ts]
tech_stack:
  added: []
  patterns: [union-type-api-response, modal-candidate-selection]
key_files:
  created:
    - frontend/src/components/CandidateSelectModal.tsx
  modified:
    - frontend/src/services/feishu.ts
    - frontend/src/pages/Login.tsx
decisions:
  - "URL code/state params cleared immediately after OAuth callback read to prevent re-trigger on refresh"
  - "Modal closable/maskClosable disabled during bind loading to prevent partial state"
metrics:
  duration: 142s
  completed: "2026-04-16"
  tasks_completed: 1
  tasks_total: 2
  checkpoint_at: task-2
---

# Phase 22 Plan 02: Feishu OAuth Frontend Flow + Candidate Modal Summary

**One-liner:** Frontend OAuth callback handling with four-status dispatch and candidate selection modal for multi-match scenarios.

## What Was Done

### Task 1: feishu.ts API Extension + CandidateSelectModal + Login.tsx Integration (73c94ca)

**feishu.ts changes:**
- Added `Candidate` interface with `employee_master_id`, `person_name`, `department`, `employee_id_masked`
- Added `FeishuOAuthResult` discriminated union type covering `matched | auto_bound | new_user | pending_candidates`
- Updated `feishuOAuthCallback` return type from fixed shape to `FeishuOAuthResult`
- Added `confirmFeishuBind(pendingToken, employeeMasterId)` API function

**CandidateSelectModal.tsx (new):**
- Ant Design Modal + List component
- Displays candidates with person_name (title) and department + masked employee_id (description)
- Props: open, candidates, feishuName, loading, onSelect, onCancel
- Click-to-select UX, disabled during loading

**Login.tsx changes:**
- Added candidate state management (candidates, pendingToken, pendingFeishuName, showCandidateModal, bindLoading)
- OAuth callback useEffect now dispatches on `result.status`:
  - `pending_candidates` -> opens CandidateSelectModal
  - `matched | auto_bound | new_user` -> writeAuthSession + redirect (existing behavior)
- Added `handleCandidateSelect` function calling confirmFeishuBind then writeAuthSession
- URL code/state params cleared via `window.history.replaceState` before API call
- CandidateSelectModal rendered in JSX

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- ESLint: 0 errors (2 pre-existing warnings unrelated to this plan)
- TypeScript: tsc --noEmit passes
- Vite build: successful
- All 7 acceptance criteria grep checks passed

## Checkpoint Status

Task 2 (checkpoint:human-verify) not yet executed - requires manual verification of Feishu OAuth login flow.

## Self-Check: PASSED
