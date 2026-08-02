---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-claim-authority-continuity-final
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: independent-audit
reviewer: codex-task-ar-654-claim-authority-continuity-auditor
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 2, P2: 1}
candidate_commit: 2f4ec606ad460efd556780c905240b26571c1986
candidate_tree: 5dc072f194adedc024e98eb2259bbc0a1459931f
independence_status: independent
release_authorized: false
created_at: 2026-08-02T14:31:04+09:00
tags: [task-ar-654, independent-audit, claim-authority, continuity, bounded-error, revise]
---

# TASK-AR-654 claim-authority continuity final audit

## Verdict

`REVISE — P0: 0, P1: 2, P2: 1.`

Exact candidate `2f4ec606ad460efd556780c905240b26571c1986`, tree
`5dc072f194adedc024e98eb2259bbc0a1459931f`, correctly rejects the component
aliases, missing intermediate parents, unreadable enumeration, and claim-entry
loop covered by its new regressions. It retains two realistic ways to omit
active authority before an otherwise successful close mutation, plus one
unbounded claim parser exception. The audit used disposable fixtures and made
no repository change.

## P1-1 — Noncanonical status casing hides an active claim

`task_claim_dispatcher._is_active()` normalizes status with
`strip().lower()`, while `closure_gate._active_claims()` compares the stripped
but case-preserving value directly to its lowercase active-status set. A valid
active repeated-failure claim whose only changed field was
`"status": "Claimed"` therefore had contradictory meanings across the two
Runtime authorities:

```text
dispatcher_active=True
work_close_returncode=0
unit_mutated=True
claim_mutated=False
compound_present=False
```

Unknown or noncanonical statuses must never be silently interpreted as
inactive. Closure must either normalize a string value consistently or report
a claim-integrity finding before mutation. Non-string status values must also
be invalid rather than coerced.

Stable signature:

`defect:claim-status-casing-hides-active-repeated-failur:43313896c2b45087`

## P1-2 — A direct store replacement loses all remembered authority

The component checks prove that the path currently named `task_claims` is a
direct directory, but they retain no durable identity showing that this is the
same initialized store that previously held claims. Moving a populated direct
store aside and creating a new direct empty directory at the same path
produced:

```text
active_claims=[]
findings=[]
work_close_returncode=0
unit_mutated=True
hidden_claim_mutated=False
```

The same omission was reproduced by swapping the directory between canonical
resolution and enumeration. Allowing a genuinely never-used final store to be
absent or empty remains required, so path-shape checks alone cannot distinguish
the two states. The Runtime needs a persistent, independently located store
generation/initialization witness, plus before/after identity validation or a
shared mutation boundary, so replacement during validation cannot present an
initialized store as never used.

Stable signature:

`defect:direct-claim-store-replacement-hides-canonical-a:7477bae20f4a3c1f`

## P2-1 — Deep claim JSON escapes bounded handling

A canonical direct claim file containing an approximately 1,000-level nested
JSON value caused `json.loads()` to raise `RecursionError`. The current handler
catches `OSError`, `UnicodeError`, and `json.JSONDecodeError` only, so actual
work close terminated with a Python traceback rather than a bounded
`active-claim-invalid-json:<name>` finding. Unit and claim bytes were not
changed, so this is fail-closed but operationally unbounded.

Catch `RecursionError` and JSON integer-limit `ValueError`, add a claim-specific
raw-byte bound, and add both direct and actual-close regressions that prohibit
traceback and mutation.

Stable signature:

`defect:deep-active-claim-json-escapes-bounded-handling:6694294b2602e0ce`

## Maintained evidence

The seven focused component cases run by the auditor passed. Source and
consumer-template scripts were identical and the host lock was current. The
later fixture-only commit `5bdd3ef1` did not change production code and does
not resolve any finding in this report.

## Release decision

Do not close, release, merge, or publish TASK-AR-654 from this candidate. Add
failure-first regressions, a durable store-continuity contract, fresh full
machine evidence, an append-only Compound, and an entirely new W4 sequence.
