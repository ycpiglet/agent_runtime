---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-transaction-truth-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T18:41:09+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/AUDIT-2026-08-02-task-ar-654-preverify-transaction-truth.md
  - reviews/REVIEW-2026-08-02-task-ar-654-authority-seams-t3-replan.md
tags: [task-ar-654, t3, transaction-truth, canonical-status, complete-snapshot]
---

# TASK-AR-654 transaction-truth T3 replan

## Decision

The authority-seam plan remains valid but is refined by the preverify audit.
Before machine Verify, the implementation must additionally satisfy all of the
following:

1. exclusive publication returns an identity token captured from the opened
   object before commit, so dispatcher and role rollback registration has no
   fallible post-commit path read;
2. errors from closing already-used parent or lock descriptors cannot reverse
   a transaction result after durable authority has committed, while every
   pre-commit open, validation, write, flush, fsync, link, and rename failure
   remains fail-closed;
3. store snapshot verification compares the complete entry set after final
   validation, including non-witness claims;
4. W0 status and workload collection use the same bounded, locked, canonical
   claim reader as closeout and refuse integrity-invalid stores;
5. decoded JSON numbers are finite even when exponent parsing overflows;
6. sync reports migration and template application from the observed
   post-operation state, including committed write-then-error outcomes; and
7. role idempotency requires stable authority metadata such as `team_id` while
   explicitly allowing only documented lifecycle fields to vary.

## Failure-first evidence requirement

Each new seam requires a RED on the immediately preceding candidate before the
fix is accepted. At minimum the matrix covers dispatcher and role ownership
capture, atomic parent close, claim-store lock close, non-witness snapshot
mutation, W0 duplicate-key/unknown-status authority, exponent overflow,
migration-only/apply-safe/write-then-error sync reporting, and missing stable
role metadata. Positive controls must keep normal publication, valid status,
stable snapshot, supported append suffix, and ordinary initialized-store
behavior working.

## Compound consequence

Task, unit, and active claim now declare forty signatures with exact parity.
The next append-only Compound must cover the previously uncovered twenty-four
plus the two new signatures above, for twenty-six uncovered signatures. The
four refined signatures remain represented by their existing registered IDs;
no duplicate signature is introduced for the same bounded failure family.
After creation, independently assert that every registered signature is in the
union of valid linked Compounds.

## Verification and release boundary

The locally green 4208-test baseline predates these regressions and is
superseded. After RED-to-GREEN repair, rerun the focused suites, the complete
Runtime suite, all mirror/lock/Compound/work/Owner gates, and then fresh
`work verify --timeout 900` on a committed implementation candidate. Preserve
that machine evidence but keep the unit failed and claim held until native
Windows Python 3.10, 3.11, and 3.12 evidence exists.

No approval exists for CI dispatch, versioning, tagging, publication, push,
deployment, consumer mutation, or any external release action. Archive-aware
Scribe, TASK-AR-655 heartbeat, and Bean Wiki/Allimbot pilots remain separate.
