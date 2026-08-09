---
schema_version: agent-runtime-review/v1
id: ROLE-REVIEW-2026-08-09-TASK-AR-660-INDEPENDENT-AUDITOR-PREFLIGHT
title: TASK-AR-660 Unit 001 Independent Auditor Pre-W4b P1 Audit
date: 2026-08-09
created_at: 2026-08-09T16:00:00+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-REVIEW-TASK-AR-660-independent-auditor-closeout
review_kind: pre_w4b_p1_audit
reviewer: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-closeout
reviewer_role: independent-auditor
status: blocked
signal: block
score: 0
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
audited_commit: d45f766b1a76fda2937ce3307fe933e8f5b4f9c8
candidate_commit: d45f766b1a76fda2937ce3307fe933e8f5b4f9c8
independence_status: distinct_agent_shared_parent_context
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_repair_and_fresh_independent_w4b
tags: [task-ar-660, unit-001, pre-w4b, p1, recovery-actor, toctou, fail-closed]
---

# TASK-AR-660 Unit 001 independent-auditor pre-W4b audit

## Summary

`REVISE — P0: 0, P1: 1, P2: 0.`

Audited commit `d45f766b1a76fda2937ce3307fe933e8f5b4f9c8` does not keep the
registered recovery actor stable through the recovery transaction. The exact
actor record can disappear after its initial read and before the claim-store
lock is acquired, yet the command still publishes prepared and committed
receipts and mutates the recovery subject.

This is a pre-W4b P1 audit, not W4b acceptance. The reviewer is a distinct
agent, but it inherited shared parent context. `w4b_acceptance` is therefore
false, release is not authorized, and the claim must remain held.

## Signal

| Surface | Result | Evidence |
| --- | --- | --- |
| Exact actor lookup | pass only at initial read | Direct bounded registry read validates the requested filename and payload. |
| Transaction-time actor authority | block | The record can disappear after lookup and before receipt publication or subject mutation. |
| Required attribution gate | block | A non-empty but unregistered event instance is accepted and the gate reports pass. |

## P1 — Recovery actor authority has a post-resolution TOCTOU gap

### Evidence

`scripts/task_claim_dispatcher.py` resolves `_registered_recovery_actor()`
before entering the claim-store transaction:

- `cmd_adopt`: actor resolution precedes `claim_store.store_lock`;
- `cmd_terminalize`: actor resolution precedes `claim_store.store_lock`; and
- `cmd_activate_store`: actor resolution precedes the internally locked store
  activation transaction.

The resolver proves that one direct, bounded instance record was stable only
during that read. It returns detached role, display-name, and callsite strings;
the command does not bind the record's inode/digest to the subsequent store
transaction or revalidate the actor at the final precommit boundary.

An isolated temporary-host reproduction used the real dispatcher and real
registry resolver:

1. Create a canonical, expired terminalization candidate and its registered
   agent-instance record.
2. Wrap the real `_registered_recovery_actor()` only to unlink that exact
   instance JSON immediately after the resolver returns and before
   `cmd_terminalize` acquires the claim-store lock.
3. Invoke the real owner-bound `terminalize` command with the exact instance
   ID.
4. Inspect the claim, receipt store, instance path, pane event, and attribution
   gate result.

Observed result:

```text
terminalize return code: 0
claim status: expired
actor record present at mutation: false
receipt states: [prepared, committed]
derived pane event: recorded with the now-unregistered instance ID
attribution gate return code: 0 (pass)
```

The same command ordering exists in adopt and activate-store, so both retain
the same authority gap even though terminalize is the concrete reproduced
case. Existing tests cover actor absence before the initial lookup and a
filename/payload mismatch, but do not exercise disappearance or replacement
between resolution and recovery precommit.

### Impact

The T3 contract requires a missing, unknown, mismatched, aliased, or unstable
actor to fail closed before receipt publication or subject mutation. This
counterexample crosses both boundaries with an actor that is no longer a
registered authority at mutation time. The resulting durable claim/receipt
truth and derived event disagree with the registry truth.

The attribution gate does not catch the disagreement. Its pane-event path
accepts any non-empty instance field without proving that the value resolves
to an exact registered instance record. Consequently the current required
gate reports pass for the reproduced unregistered event.

## Action

### Required RED

Add failure-first tests for all three recovery commands that interpose after a
successful actor read and before recovery precommit. At minimum, cover:

- unlinking the actor record;
- atomically replacing it with an unknown or filename/payload-mismatched
  record; and
- changing canonical role or callsite authority.

Every case must assert a non-zero command result, exact subject byte identity,
no new prepared/committed/indeterminate receipt, and unchanged pane-event
bytes. Add an attribution-gate regression proving that a post-cutoff event
with a non-empty but unregistered instance ID blocks instead of passing.

### Fix conditions

- Resolve and validate the actor under the same cooperative claim-store lock
  that protects the recovery transaction.
- Bind the validated actor record identity or digest through the final
  precommit boundary so a replacement cannot be laundered between validation
  and receipt publication.
- Preserve the human Owner as `owner_id`/`recovered_by` and the registered
  runtime instance as event actor; do not merge the identities.
- Keep receipt-first ordering and all existing non-retry-safe durability
  semantics unchanged.
- Mirror the dispatcher and attribution-gate repair into the generated-host
  template, regenerate the managed host lock, and rerun the exact Unit 001
  suites and gates.

## Risks / Blockers

- The same ordering is present in adopt, terminalize, and activate-store; a
  terminalize reproduction is sufficient to reject the shared transaction
  pattern, but all three commands need RED coverage.
- The current attribution gate masks the resulting registry/event
  disagreement, so its green result is not acceptance evidence for this case.
- Fixing only the derived event would leave receipt and subject mutation
  authority unchanged; the actor must remain bound through recovery
  precommit.

## Decision

`REVISE`. Keep Unit 001 and its claim open. Do not treat this preflight as
W4b, do not release the claim, and do not integrate the candidate until the
P1 counterexample is RED-first repaired and independently re-audited.

## Next Steps

1. Commit the failure-first transaction and attribution-gate regressions.
2. Repair actor stability under the recovery transaction lock and preserve
   root/template parity.
3. Rerun the exact Unit 001 suites, receipt, identity, attribution, template,
   RBAC, and parallel-worktree gates on a clean candidate.
4. Request a fresh independent W4b with no shared parent context.

## Boundary

No W4b acceptance, claim release, merge, version change, tag, push, package
publication, deployment, consumer mutation, credential access, or external CI
action is authorized. A repaired clean candidate requires a fresh independent
W4b review.
