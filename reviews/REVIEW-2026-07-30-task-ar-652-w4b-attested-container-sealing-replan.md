---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T21:31:06+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-receipt-attestation-approval.md
tags: [task-ar-652, w4b, replan, economic-evidence, immutable-container, sealed-provenance]
---

# TASK-AR-652 attested-container sealing replan

## Bottom Line

Fresh independent W4b confirmed that complete receipt-value digests and hidden
ledger snapshots now fail closed under row mutation. It then reproduced two
remaining P1s at the container boundary:

1. `ValidatedOutcomeRecords` validates exact ledger membership only during
   construction. Reusing an already-attested actual object through mutable
   list operations multiplies eligible comparisons and aggregate savings.
2. The read-only mapping is held in a writable `_economic_provenance` slot.
   Replacing that slot with a caller-computed digest and the original hidden
   snapshots re-attests a mutated row.

This replan keeps the current unit, offline scope, worktree, and active claim.
It seals collection membership and provenance authority together without
changing routing, provider, budget, or consumer behavior.

## Reproduced Findings

With one valid reserved baseline/actual pair, the untouched report showed one
eligible comparison, 85 saved tokens, and USD 0.08. Appending the same actual
object doubled the totals; extending it twice tripled them. Insert, slice
assignment, and list multiplication reproduced the same class of inflation.

On a fresh validated view, mutating the actual receipt correctly reduced
eligibility to zero. Replacing `_economic_provenance` with a new mapping whose
digest matched the mutation restored one eligible comparison and manufactured
99 saved tokens and USD 0.10.

No credential, provider, network, account, consumer primary, or external
system was used.

## Decision

- Preserve the exact ordered outcome objects accepted by the complete ledger
  validation as a private immutable membership snapshot.
- Deny normal structural mutation of the validated view, including item and
  slice assignment, deletion, append, extend, insert, pop, remove, clear,
  reverse, sort, `+=`, and `*=`.
- Before economic provenance is returned to `report()`, compare the current
  collection against the immutable membership snapshot by length, order, and
  object identity. A direct `list` base-method bypass must therefore fail
  closed even when it bypasses overridden mutators.
- Move provenance authority out of the caller-replaceable
  `_economic_provenance` slot. Seal constructor-created membership and
  provenance in private state and expose only an internal validation method.
- Reject attribute replacement after construction. A replacement public or
  former-private provenance mapping must never become reporting authority.
- Keep the complete per-receipt digest comparison. Membership validation
  prevents structural reuse; the existing digest prevents mutation of an
  original row.
- Preserve strict-ledger historical unreserved compatibility and all existing
  reservation, settlement, provider-call-start, terminal-success,
  budget-authority, route, telemetry, and false-savings checks.

## Failure-First Matrix

- On a valid positive pair, require every ordinary structural mutator to raise:
  `append`, `extend`, `insert`, `+=`, `*=`, item assignment, slice assignment,
  item deletion, slice deletion, `pop`, `remove`, `clear`, `reverse`, and
  `sort`.
- Bypass overrides with direct base methods such as `list.append`,
  `list.extend`, `list.__setitem__`, `list.__delitem__`, and
  `list.__imul__`; reporting must then produce zero economic eligibility.
- Duplicate an already-attested actual through each applicable path and prove
  that eligible counts, saved tokens, and billed-cost savings cannot increase.
- Remove or reorder ledger members through direct base methods and require the
  same fail-closed reporting result.
- Mutate an actual row, then try ordinary assignment to
  `_economic_provenance` and to the sealed provenance attribute. Assignment
  must be rejected and eligibility must remain zero.
- Retain the complete 112-field row-mutation matrix, plain-list and copy-strip
  negatives, direct-constructor integrity checks, hidden provenance snapshot
  mutations, and historical unreserved positive control.

## Invariants

- Economic evidence is consumed only from the exact ordered outcome view that
  passed complete ledger validation.
- A validated receipt object may contribute at most once.
- Neither list structure nor provenance authority may be replaced after
  construction.
- Receipt-value mutation still fails the canonical digest.
- Direct use of mutable `list` base methods may corrupt the caller's view but
  can never make that view economically eligible.
- Missing, changed, or structurally detached provenance may exclude evidence
  but can never manufacture savings.
- No live provider, credential, dependency, consumer primary, database,
  broker, order, notification, deploy, push, tag, version, publication, or
  release action is authorized.
- No token or monetary savings claim is made.
- The task claim remains `claimed` until a repaired clean candidate receives a
  fresh independent W4b `APPROVE` verdict with no P0/P1.

## Verification Plan

1. Record this replan and the blocking W4b in unit metadata, the evidence
   index, and the T3 assumption snapshot while preserving the active claim.
2. Add the structural-mutation and provenance-replacement failure-first tests
   and capture their expected failures.
3. Implement a sealed membership/provenance representation plus report-time
   exact-membership validation in the packaged `eval_harness`.
4. Rerun the expanded adversarial matrix and full eval-harness suite.
5. Run required root, template, SDK, taskset, lock, asset, mirror, compilation,
   full Runtime, exact-range, and Owner-governance checks.
6. Record new canonical VERIFY and W4a evidence against exact commits, then
   request a new fresh independent W4b. Release the claim only after approval.
