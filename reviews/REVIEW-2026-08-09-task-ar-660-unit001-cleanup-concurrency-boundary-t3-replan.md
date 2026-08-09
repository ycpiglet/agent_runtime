---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-task-ar-660-unit001-cleanup-concurrency-boundary-t3-replan
title: TASK-AR-660 Unit 001 Cleanup Concurrency Boundary T3 Replan
date: 2026-08-09
created_at: 2026-08-09T19:23:45+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-20260809-125520-task-ar-660-491d
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
tier: T3
reviewer: le-20260809-130000-kst-ar660001
reviewer_role: orchestrator
status: accepted
signal: pass
score: 100
verdict: ACCEPT_BOUNDED_COOPERATIVE_CLEANUP_CONTRACT
priority: P1
owner_approval_ref: owner instruction to proceed with all approved recovery work, 2026-08-09
release_authorized: false
tags: [task-ar-660, unit-001, t3-replan, atomic-io, cleanup, concurrency-boundary, cooperative-lock]
---

# TASK-AR-660 Unit 001 cleanup concurrency boundary T3 replan

## Bottom Line

Accept the parent-identity repair with an explicit bounded-concurrency contract.
The precommit callback may adversarially mutate any relevant path before it
returns or raises, and rejection cleanup must detect and preserve those
callback-complete mutations. After the callback returns or raises, however,
fallback pathname cleanup requires a quiescent interval or participation in the
same cooperative process-shared lock until cleanup finishes.

## Clarified Concurrency Contract

The supported hostile interval includes all mutations performed by the callback
itself. The callback may remove, replace, rename, populate, or alias the prepared
sidecar, an operation-created parent, or any lexical ancestor before returning
or raising. Cleanup receives no deletion authority merely because a pathname or
device/inode pair still exists: it must revalidate the exact sidecar and the
complete root-to-leaf non-alias chain after the callback outcome is known.

Once post-callback validation begins, correctness requires one of these bounded
conditions through the final cleanup mutation:

1. the relevant namespace is quiescent; or
2. every concurrent participant holds the same cooperative process-shared lock.

Production Owner recovery operations satisfy the second condition by holding
the process-shared claim-store lock across the recovery transaction, including
the precommit callback and its rejection cleanup. The contract does not claim
race-free compare-delete behavior against an arbitrary filesystem writer that
ignores that lock and mutates a validated component between the final metadata
check and a fallback pathname unlink or `rmdir`.

## Signal

| Surface | State | Evidence |
| --- | --- | --- |
| Callback-hostile mutation interval | required | callback mutations before return or raise are inside the supported threat model |
| Post-callback cleanup interval | bounded | namespace must be quiescent or protected by the cooperative process-shared lock |
| Production recovery commands | covered | recovery mutations hold the process-shared claim-store lock through callback and cleanup |
| Arbitrary noncooperating writer | excluded | no atomic compare-delete guarantee is claimed for fallback pathname operations |
| Native handle-backed compare-delete | deferred | separate future task, not an implicit requirement of Unit 001 |

## Action

Implement conservative callback-rejection cleanup under this boundary. Any
missing, replaced, aliased, generation-changed, or otherwise uncertain sidecar
or directory forfeits deletion authority. Preserve the stable-tree rollback and
the original callback ordering and exception identity. Tests may mutate paths
inside the callback adversarially; they must not model an unbounded writer that
continues racing cleanup after the callback without acquiring the cooperative
lock and then treat that excluded race as a supported guarantee.

A stronger implementation that pins every ancestor and performs native
handle-backed compare-delete, including a Windows handle implementation, must
be registered and scoped as a separate future task. It is not silently added to
the Unit 001 footprint or acceptance criteria.

## Acceptance Clarification

Unit 001 acceptance means:

- callback-complete path mutations are detected before cleanup authority is
  exercised;
- cleanup is correct during the subsequent quiescent or cooperatively locked
  interval used by production recovery operations;
- no claim is made against arbitrary noncooperating writers racing after the
  final validation; and
- the limitation is stated in handoff and independent W4b evidence rather than
  hidden behind a platform-independent atomicity claim.

## Decision

`ACCEPT` this concurrency clarification without expanding the current code or
test footprint. Continue Unit 001 implementation and verification against the
bounded contract. Native handle-backed compare-delete remains separate future
work.

This decision grants no Unit 002 work, main-claim release, acceptance,
completion, external CI, consumer mutation, credential access, push, tag,
publish, deploy, or other external release authority.

## Next Steps

Link this record from Unit 001 inputs, state the bounded contract in acceptance
and handoff, and require the next W4b to judge the candidate against this exact
threat boundary.
