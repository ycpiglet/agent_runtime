---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-task-ar-661-existing-taskset-recovery-t3-replan
title: TASK-AR-661 Existing Taskset Recovery T3 Replan
date: 2026-08-09
created_at: 2026-08-09T12:20:00+09:00
task_id: TASK-AR-661
unit_id: UNIT-TASK-AR-661-001
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
review_kind: t3-replan
reviewer: codex-root-owner-approved-correction
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: ACCEPT_SCOPE_AMENDMENT
priority: P1
tags: [t3, taskset-recovery, work-identity, merge-loss]
---

# TASK-AR-661 Existing Taskset Recovery T3 Replan

## Reason

The initial correction registration safely reserved new collision-free IDs for
Scribe (`TASK-AR-662`) and Compound (`TASK-AR-663`), but staged them in the
correction taskset. A final authority audit established that their product work
belongs to `TASKSET-AR-V080-OPERABILITY-HARDENING`. Leaving them permanently in
the correction taskset would make the V080 ordered work definition incomplete.

The Runtime has no audited command for moving a newly reserved task into an
existing strict taskset while atomically updating task, unit, reservation,
taskset registry, initiative, plan-assumption identity, and a recovery receipt.
Manual low-level edits would repeat the defect being repaired.

## Accepted Amendment

Extend `UNIT-TASK-AR-661-001` with a RED-first existing-taskset recovery
transaction in root/template `work.py`. The transaction must:

1. require exact task and unit UUID CAS, current reservation binding, source
   collision identity, target taskset/initiative, expected registries, Owner
   attribution, and reason;
2. publish an immutable machine-readable recovery receipt before authority
   mutation and report committed, prepared, or indeterminate truthfully;
3. update all canonical records atomically or roll back before any partial
   authority is accepted;
4. refuse a path-only match when `task_uid` or unit `work_uid` differs;
5. leave the historical registration input, old task/unit files in Git
   history, terminal claim triplets, A2A records, reviews, and Compound records
   byte-identical;
6. stage the actual transition only after its implementation receives W4b.

The orchestrator will then use that command to move Task 662 and Task 663 into
the V080 taskset and initiative. Final ordered V080 membership is:

```text
[TASK-AR-652, TASK-AR-662, TASK-AR-663, TASK-AR-655,
 TASK-AR-656, TASK-AR-657, TASK-AR-658, TASK-AR-659]
```

The correction taskset will retain Tasks 660 and 661 only. The six
non-conflicting historical reservation rows remain the only direct ledger
restoration. The two colliding old reservations are represented solely by the
recovery mapping from old UUID/commit/reservation to new UUID/reservation.

## Additional Corrections

- Correct stale Host Required Merge Gates Task 654 metadata only from its own
  released claim and approved W4b, never from the colliding Compound evidence.
- Correct the TASK-AR-659 W4b aggregate and chronology through append-only
  correction evidence; do not rewrite the old review as though it were always
  correct.
- Re-anchor V080 and correction-plan assumptions with UUID-aware semantic
  identity after recovery.
- Refresh pointer and generated views only after canonical authority passes.

## Scope Boundary

This amendment does not authorize external CI, Windows evidence inference,
consumer changes, versioning, tagging, pushing, publishing, deployment, or
external release.
