---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-heartbeat-expiry-t3-replan
title: TASK-AR-655 heartbeat and expiry T3 scope amendment
date: 2026-08-03
created_at: 2026-08-03T01:22:02+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: codex-root-task-ar-655-orchestrator
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: ADD_CAS_MUTATION_RECEIPT_AND_SHARED_LIVENESS_CONSUMERS
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 0c3048ae5acd877ca8f6cc949ae66b69decb9cd7
candidate_tree: 018a483df964bd2b6e8582f890f2a9eb02803647
release_authorized: false
tags: [task-ar-655, t3-replan, heartbeat, renewal, expiry, doctor, ui]
---

# TASK-AR-655 heartbeat and expiry T3 scope amendment

## Decision

Accept the independent audit and extend the existing unit before RED. The
original local-only boundary remains: this is a durable checkout claim
protocol, not a network lease service, Git publisher, or automatic pointer
writer.

## Added source and test authority

- Add the root/template instance registry pair and its identity test so the
  mutation receipt can prove the auxiliary instance timestamp.
- Add Doctor and its test so expired and indeterminate task claims are visible
  at the same release-blocking boundary as state sync.
- Add the orchestrator atomic-write test so its progress wrapper is proven to
  call the dispatcher heartbeat path rather than write claim or pointer state.
- Add UI console assets and their focused design-asset test so browser WIP uses
  server-derived liveness rather than raw status.
- Add this audit and replan to the task, unit, and active claim authority.

## Scope boundaries

Transport and audit-preservation tools such as claim guard remain lifecycle
neutral. Dispatch/conflict tools continue to retain a status-active expired or
indeterminate claim until the reaper performs the explicit terminal
transition; they must not create a second owner automatically. Historical
claim trace lookups remain lifecycle neutral. This unit changes only mutation,
blocking, cleanup protection, and presentation surfaces named in its
acceptance.

## Implementation order

1. Register the four exact Compound signatures and added footprint everywhere.
2. Commit only RED contract tests and mark unit verification failed.
3. Add shared grace resolution and `ClaimLiveness` to the three mirrored claim
   store sources.
4. Add create scope binding/revision plus owner-checked heartbeat and renewal.
5. Update the instance registry and add the orchestrator claim-progress wrapper.
6. Adopt the classifier in reaper, state sync, parallel continuity, worktree
   lifecycle, UI state, UI console, and Doctor.
7. Run the focused cross-surface matrix, full registered verification, mirror
   and host-lock gates, then official Verify.
8. Perform exact Compound lookup again and append one immutable mitigation
   record before W4a/W4b/skeptic review.

The active claim remains claimed. No external action or release is authorized.
