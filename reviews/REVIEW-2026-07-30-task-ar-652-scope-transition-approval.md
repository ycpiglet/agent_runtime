---
type: planning
title: TASK-AR-652 operability taskset scope transition approval
date: 2026-07-30
signal: pass
score: 100
task_id: TASK-AR-652
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
tags: [planning-record, task-ar-652, scope-transition, owner-directive, selective-routing]
---

# TASK-AR-652 operability taskset scope transition approval

## Bottom line

The Owner instructed the registered Agent Runtime hardening and next-version
plan to proceed ("절차대로 진행해줘", followed by "진행"). The completed v0.8
adoption taskset already points to `TASK-AR-652` as the first operability task.
This is durable approval to move from
`TASKSET-AR-V080-ADOPTION-ENFORCEMENT` into
`TASKSET-AR-V080-OPERABILITY-HARDENING`.

## Decision

- Record `scope_transition_approved: true` on
  `CLAIM-20260730-123600-task-ar-652-ar652001` before its first persistence.
- Apply the deterministic task/unit/pointer projection emitted by
  `task_claim_dispatcher.py projection`.
- Preserve the first failed manual commit as evidence that the boundary,
  identity, RBAC, and projection gates worked.
- Do not use the transitional boundary escape.

## Selective overlay decision

The configured every-wave progress-scout hook produced an overlay claim but
did not dispatch a real agent instance. Persisting that claim would violate
identity and RBAC truth and would recreate the token-waste pattern this task is
meant to remove. Cancel that unpersisted overlay and keep the main worker claim.
Future waves use the supported `AR_SCOUT_COUNCIL=0` kill switch unless a
specific registered trigger and execution instance require the scout.

This does not waive independent W4b. TASK-AR-652 still requires a different
agent instance to verify and release the worker claim.
