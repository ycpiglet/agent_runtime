---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-re-w4b-dispatch-t3-replan
title: TASK-AR-655 Re-W4b Dispatch T3 Replan
date: 2026-08-03
created_at: 2026-08-03T16:47:00+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
tier: T3
reviewer: le-20260803-164700-kst-ar655rew4b
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: ACCEPT_TASK_AR_655_RE_W4B_DISPATCH
priority: P1
predecessor_ref: reviews/W4B-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
blocker_closed_by: reviews/W4B-2026-08-03-unit-task-ar-659-001-recovery-commands-final.md
release_authorized: false
tags: [task-ar-655, t3-replan, re-w4b, reanchor, dispatch]
---

# TASK-AR-655 re-W4b dispatch T3 replan

## Bottom Line

`ACCEPT` re-dispatch of TASK-AR-655 for independent re-verification, and
re-record the drifted anchor.

## Why the anchor drifted

One anchor moved: `tests/test_task_claim_dispatcher.py`. TASK-AR-659 landed on
this branch and added its regression tests there, including the four-point
liveness-evidence boundary. This is the taskset's own completed work changing a
file the taskset anchors, not an external actor.

## Why AR-655 can be re-verified now

The prior W4b returned `REVISE — P1 1`. Its blocking finding was that claims
created before the `mutation_revision` / `scope_binding` fields could neither
heartbeat nor renew, with the active TASK-AR-655 claim as a
production-shaped counterexample.

TASK-AR-659 closed exactly that defect: `adopt` brings a pre-mutation-field
claim under the current contract so heartbeat and renew reach it again, and a
test asserts an adopted legacy claim is actually renewable. That work carries
its own 4-round independent W4b `ACCEPT`.

Two conditions the prior attempt failed are also now satisfied:

1. The prior W4b report materialised 23 seconds **after** its claim's lease
   expired, so it could not serve as approval evidence. This dispatch creates a
   fresh 120-minute claim and the review must complete inside it.
2. The prior claim was `mode: orchestrator`, which the reaper skips
   unconditionally. The new claim is `mode: worker`, so it is both renewable
   and reapable.

## Plan assumptions unchanged

Local claim authority only; no network or distributed lease; no release,
acceptance, or external-release authority; the reaper still never auto-reaps an
orchestrator claim.

## Decision

`ACCEPT` re-dispatch, re-record the taskset anchors against this record, and
obtain an independent context-isolated W4b for UNIT-TASK-AR-655-001 while the
claim is live. No release authorization.
