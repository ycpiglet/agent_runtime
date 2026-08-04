---
schema_version: agent-runtime-review/v1
id: W4A-2026-08-03-unit-task-ar-659-001-recovery-commands
title: TASK-AR-659 Owner-Bound Recovery Commands W4a Self-Review
date: 2026-08-03
created_at: 2026-08-03T15:10:00+09:00
task_id: TASK-AR-659
unit_id: UNIT-TASK-AR-659-001
claim_id: CLAIM-20260803-143123-task-ar-659-cfc8
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4a
reviewer: le-20260803-143123-kst-cfc8
reviewer_role: worker
status: revise
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 1}
candidate_commit: 0d84449cc1c44a6bba234fb504c15ca5a14e1961
candidate_tree: d1d5c641ab05cb233c7f03f2124ace594549f336
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-659-001-20260803150038.json
compound_ref: agents/project/knowledge/compounds/records/COMPOUND-20260803-150241-give-every-claim-state-a-registered-exit-before-c0729965fea7.json
w4b_acceptance: false
release_authorized: false
tags: [w4a, task-ar-659, claim-authority, recovery, self-review]
---

# TASK-AR-659 owner-bound recovery commands W4a self-review

## Bottom Line

`REVISE — P0: 0, P1: 1, P2: 1.`

The unit's acceptance criteria are met and the registered verification passes
(4 commands, 397 tests). But this self-review found a real consistency defect
I introduced, so I am not signalling accept. An independent W4b must judge the
candidate, and the P1 below should be repaired first.

## What was built

| Surface | Change |
|---|---|
| `task_claim_dispatcher.py adopt` | Supplies `mutation_revision`/`scope_binding` to a legacy claim. Leaves status, progress, and lease untouched. Refuses a claim that already has both fields, so it cannot be used to rebind scope. |
| `task_claim_dispatcher.py terminalize` | Ends a provably dead claim regardless of mode. Preserves the file; not a release, completion, or acceptance. Refuses a live claim. |
| `task_claim_dispatcher.py activate-store` | Activates a checkout's claim store without a consumer `agent_runtime.yml`. |
| `claim_reaper.classify_claim` | Evaluates liveness before the orchestrator branch. Dead orchestrator claims report `orchestrator-claim-expired` and appear in a new `needs_owner_recovery` bucket. |

Both mutating commands refuse an unidentified caller, require a reason, and
record owner identity, `before`/`after` sha256, authority, and operation.

## Findings

### P1 — new mutations hold the store lock but skip snapshot verification

`scripts/task_claim_dispatcher.py` — `cmd_adopt` and `cmd_terminalize`.

Every other mutating path in this file pairs `claim_store.store_lock(root)`
with `claim_store.verify_snapshot(root, ...)` before writing: `create`
(`:2083` lock, `:2203` verify), `projection` (`:2894`), `release` (`:3128`
lock, `:3223` verify). `claim_reaper` does the same at `:168` and `:361`, and
raises `_ClaimStoreAuthorityChanged` when the check fails.

My two commands take the lock at `:3463` and `:3526` but never call
`verify_snapshot`. Failure scenario: the claim-store authority (marker
generation / witness) is replaced by another actor between the snapshot read
that `_find_claim_in_canonical_snapshot` consumes and the
`atomic_io.write_json_atomic` call. The lock alone does not prove the store
is still the same store, which is exactly the property `verify_snapshot`
exists to assert. The write would land against superseded authority instead
of failing closed.

This matters more than usual here: these are the commands that run when the
system is already in a degraded state, so they are the last place that should
skip an authority check. Repair is to mirror the established pattern.

### P2 — `activate-store` is not owner-bound

`scripts/task_claim_dispatcher.py` — `cmd_activate_store`.

Unlike `adopt` and `terminalize`, it takes no `--owner-id` and records no
recovery provenance. The justification is that it mutates no claim — it only
creates the per-checkout outer marker, and `adopt_legacy_store()` already
refuses to rebind an existing marker. I judge this acceptable, but it is an
asymmetry in a command family whose whole point is owner-bound provenance,
and W4b should rule on whether the activation ought to be attributable.

## Verified, not asserted

- Refusals exercised against **real** claims, not only fixtures: terminalize
  on the live AR-659 claim returned `claim lease is live (lease-valid)`;
  adopt with an empty owner returned `owner identity is required`; adopt on
  the terminalized AR-655 claim returned `already terminal ('expired')`.
- Reaper safety invariant intact: `test_orchestrator_claim_is_skipped` still
  passes, and `reaped`/`would_reap` stay empty for orchestrator claims.
- Two guard tests confirm a live and an already-terminalized orchestrator
  claim are **not** flagged for recovery, so the new bucket cannot inflate.
- The two refusal tests assert on the refusal message and exclude
  `invalid choice`, so they could not have passed vacuously during RED.
- Template mirror findings back to 0; host lock regenerated.

## Scope discipline

No network or distributed lease dependency. No release, acceptance, or
external-release authority added. No consumer project touched. No version,
tag, push, publish, or deploy action.

## Known limitation carried forward

`tests/test_claim_guard.py` remains at its pre-existing 21 failed / 15 passed
baseline on `main`. It is excluded from this unit's `verification:` list with
the reasoning recorded in the unit spec, and this candidate leaves the count
unchanged. It is not this unit's defect and is not claimed as fixed.

## Next

Repair the P1, re-run verification, then obtain an independent
context-isolated W4b. The unit is not accepted and no release is authorized.
