---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-postcommit-projection-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T19:21:52+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/AUDIT-2026-08-02-task-ar-654-combined-green-precommit.md
  - reviews/REVIEW-2026-08-02-task-ar-654-transaction-truth-t3-replan.md
tags: [task-ar-654, t3, post-commit, projection, marker-recovery]
---

# TASK-AR-654 post-commit and projection T3 replan

## Decision

The transaction-truth acceptance remains unchanged and directly covers the six
current findings. The next candidate must additionally demonstrate:

1. durable closeout success cannot be converted to claim-integrity failure by
   a later generated-view error; the caller receives committed truth plus a
   bounded projection warning and retry guidance;
2. sync returns nonzero whenever required template application is not observed
   committed or the post-operation plan retains applicable updates, while a
   successful migration-only operation remains exit zero;
3. opt-in claim SCM persistence is isolated as a post-commit warning even when
   the helper raises before it can report its own best-effort result;
4. incomplete or unknown marker rollback preserves the witness claim and its
   artifacts for recovery, and only a proven marker rollback permits witness
   deletion;
5. dispatcher projection reads one locked verified claim snapshot and cannot
   re-emit a claim released before the projection snapshot; and
6. `work status` derives active rows and inflight claim indexing from the same
   canonical snapshot rather than two independently timed raw reads.

## Failure-first matrix

Record RED before repair for generated-view failure after closeout, sync
not-applied/remaining-update exit status, raising SCM helper after claim commit,
inner-marker cleanup failure, release/projection interleaving, and W0
active/inflight snapshot contradiction. Retain positive controls for clean
closeout, migration-only sync, non-authorized SCM mode, complete marker
rollback, static projection, and ordinary W0 output.

## Scope

The bounded implementation scope adds `scripts/inflight_overlay.py` and its
template/test to the already registered work/dispatcher/role/sync assets. The
task remains at forty signatures, with twenty-six still uncovered before the
fresh Compound. The four adjacent release blockers in the triggering audit are
explicitly deferred to TASK-AR-655, TASK-AR-657, and TASK-AR-651; this replan
does not authorize implementing them under TASK-AR-654.

## Release boundary

All previous local passes are superseded. Fresh focused/full tests, an exact
implementation commit, machine Verify, complete Compound union coverage, and
fresh W4 are still required. Native Windows execution remains pending Owner
approval. No external release action is authorized.
