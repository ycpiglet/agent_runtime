---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-654
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
signal: pass
priority: P1
created_at: 2026-08-02T23:26:00+09:00
reviewer: codex-root-task-ar-654-orchestrator
implementation_commit: 94589d6839f84056ac9ce770c7c5fdb0124e33bd
implementation_tree: 5c80db780dd6625ee3cec3c1592ce2b4bde93784
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802231400.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-232400-bind-ancestor-identity-and-release-provenance-at-e8e801007dc0.json
release_authorized: false
tags: [task-ar-654, compound, scope-amendment, adverse-w4b, append-only, coverage]
---

# TASK-AR-654 adverse-W4b Compound scope amendment

## Bottom line

Implementation `94589d6839f84056ac9ce770c7c5fdb0124e33bd`, tree
`5c80db780dd6625ee3cec3c1592ce2b4bde93784`, passed the fresh registered
Verify. The resulting append-only Compound binds the three adverse-W4b repair
lanes to their actual regressions without editing any earlier Compound record.

## Exact prevention record

The new record is:

`agents/project/knowledge/compounds/records/COMPOUND-20260802-232400-bind-ancestor-identity-and-release-provenance-at-e8e801007dc0.json`

SHA-256:
`321fa612833cee76b1286992cdbea5b38a426ef26ff61fe34b6b7e9885612b27`.

It links both `TASK-AR-654` and `UNIT-TASK-AR-654-001`, has
`status: mitigated`, `recurrence_count: 4`, and contains exactly these ordered
signatures:

1. `defect:atomic-publication-accepts-aliased-parent-compon:e89f4bf8d6bd13c4`
2. `defect:container-valued-core-claim-identity-permits-dup:53594ebe603a7c1f`
3. `defect:incomplete-role-overlay-is-accepted-as-idempoten:88dc7419f9159bb4`

The first and third signatures intentionally recur in an earlier immutable
Compound. Their inclusion records that the prior prevention was insufficient
for an existing direct parent and a released overlay's status-specific
provenance. The second signature had no canonical prior match and was the only
uncovered member of the 41-signature task/unit/claim authority before this
record. Append-only overlap is therefore evidence of recurrence, not a rewrite
or duplicate replacement.

## Verification binding

Fresh evidence
`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802231400.json` has
SHA-256
`0c9b4893b5c7a3bb593c84a7b4012c16f9b80598c73f4af9691afaf7f159e88d`
and records five passing commands:

- full Runtime: `4295 passed, 11 skipped`;
- focused governance: `1252 passed, 2 skipped`;
- runtime asset usage: pass;
- template mirror: `86` common, `83` identical, `3` intentional, zero
  findings; and
- managed host lock: current.

The prevention references are the exact atomic, claim-store, W0/status,
dispatcher-create, and role-routing regression files. The source references are
the adverse W4b, its accepted T3 replan, and the immutable evidence/contract
correction.

## Coverage and disposition

Task, unit, and active claim retain the same ordered 41 unique signatures;
their sorted-newline SHA-256 is
`da6a60b5f42c6ca4fbe46a4fcdb4b30b8fca0fa29b1e89a7ff860fc4a40bad60`.
After adding this fifth explicit Compound reference, the linked-record union
covers all 41 signatures with no uncovered or extraneous signature. Earlier
records remain byte-identical.

This is prevention evidence, not W4 acceptance. The unit remains
`verification_status: failed`, the claim remains held, and a new exact-candidate
W4a, distinct W4b, conditional skeptic review, native Windows evidence, Scribe
debt, and adjacent release blockers remain pending. No closeout, claim release,
consumer mutation, CI dispatch, push, tag, versioning, publication, deployment,
or external release is authorized.
