---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-authority-seams-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T18:25:27+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/AUDIT-2026-08-02-task-ar-654-precommit-authority-seams.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-transaction-continuity-t3-replan.md
tags: [task-ar-654, t3, authority-seam, compound-coverage, strict-json, truthful-state]
---

# TASK-AR-654 authority-seam T3 replan

## Decision

The claim transaction contract remains valid but is incomplete at six seams.
The final local implementation candidate must additionally satisfy:

1. publication returns committed success once the destination exists and
   treats later sidecar cleanup as best effort;
2. dispatcher and role rollback remove only captured identity-and-byte-matching
   objects created by the current call;
3. every authority-bearing active, released, and witness claim uses the shared
   bounded canonical reader and known lifecycle vocabulary;
4. valid Compounds must collectively cover every normalized defect signature
   declared by the current task, unit, and selected claim authority;
5. shared JSON rejects non-finite constants and duplicate keys;
6. overlay idempotency validates the deterministic handoff/log seed prefix but
   preserves the intentional append-only suffix contract;
7. sync reports committed migration and exact applied template count on partial
   failure; and
8. native Windows junction tests select all four atomic APIs across Python
   3.10, 3.11, and 3.12 in the existing targeted workflow.

## Failure-first evidence requirement

The new canonical-reader, witness-status, partial-Compound-coverage, strict
JSON, atomic cleanup, competing-overlay rollback, corrupted artifact, Windows
junction, and partial-sync tests must fail on their immediately preceding
implementation and pass after repair. Positive compatibility must retain
overwrite last-writer-wins, exclusive create one-winner, valid released claim,
normal initialized store, and permitted handoff/log append behavior.

## Compound and verification consequence

The next append-only Compound must directly include both work IDs and the
complete uncovered-signature set. At this replan point the set is the prior
eighteen plus the six audit signatures, for twenty-four. A separate assertion
must prove:

`registered task signatures - union(valid linked Compound signatures) == ∅`.

The standard Compound store/index check alone does not prove that condition.
Fresh `work verify` must include the complete Runtime suite with a 900-second
timeout, but its local pass does not satisfy native Windows release evidence.
Keep the unit open and the claim held after local Verify.

## Scope and stop boundary

The additional scope is limited to the shared claim-store reader, closure/work
Compound coverage, atomic publication, role overlay, sync reporting, their
source/template mirrors, focused tests, host lock, lifecycle evidence, and the
already registered Windows workflow. Archive-aware Scribe, TASK-AR-655
heartbeat, consumer pilots, and advisory UI convergence remain separate.

No Owner approval exists for CI dispatch, versioning, tagging, publication,
push, deployment, consumer mutation, or external release execution.
