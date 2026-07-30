---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T20:59:12+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-economic-provenance-approval.md
tags: [task-ar-652, w4b, replan, economic-evidence, receipt-attestation]
---

# TASK-AR-652 receipt-row attestation replan

## Bottom Line

The fresh independent W4b confirmed the prior provider-call provenance repair,
then reproduced one remaining P1. `ValidatedOutcomeRecords` binds validated
reservation, settlement, and call-start records to a receipt only by Python
object identity. It does not bind the complete receipt value that passed
strict ledger validation. A caller can therefore mutate the same dictionary,
or copy a reserved receipt and remove its five derived budget fields, and
produce eligible token and monetary savings that no longer match the ledger.

This replan keeps the current unit, offline scope, worktree, and active claim.
It narrows the repair to immutable receipt-row attestation and an explicit
strict-ledger compatibility boundary.

## Reproduced Finding

The independent verifier loaded a valid synthetic baseline and actual from a
strict ledger. The untouched rows reported 85 saved tokens and USD 0.08. After
changing the returned actual dictionary in memory, without changing the
ledger or provenance objects, the same report claimed 99 saved tokens and USD
0.10. Copying the validated rows into plain dictionaries, deleting only the
five reservation-derived fields, also restored one eligible comparison.

No provider, credential, account, consumer primary, or external system was
used.

## Decision

- Canonically digest the complete execution receipt accepted by strict ledger
  validation and bind that digest to its economic provenance entry.
- Store provenance records in an immutable representation so caller-held
  reservation or marker dictionaries cannot change the attested context after
  validation.
- Before any economic or identity field is consumed, require the current
  receipt digest to equal the attested digest.
- For `agent-runtime-execution-receipt/v1`, missing provenance is always
  ineligible. Absence of caller-controlled budget fields is not evidence that
  a receipt is historical or unreserved.
- Preserve historical unreserved compatibility only when a strict ledger
  validation explicitly produces an attestation entry with no reservation.
- Make direct `ValidatedOutcomeRecords` construction validate the complete
  supplied ledger and prove that the exposed outcome rows are the exact
  filtered rows from that ledger. `read_outcomes()` remains the normal
  factory.
- Keep ordinary legacy outcome rows that do not claim the execution-receipt
  schema on their existing reporting path.
- Keep the previous reservation, settlement, provider-call marker, transition,
  budget-authority, provider, execution-surface, and derived-field integrity
  checks unchanged.

## Failure-First Matrix

- Mutate each economic or identity-bearing field on the same validated actual
  and baseline dictionaries after `read_outcomes()`: token components, billed
  cost, currency, provider/model/reasoning observations, status, finish
  reason, outcome, workload, baseline receipt ID, route fields, source,
  dispatch identity, and receipt identity. Every mutation must yield zero
  eligible token and monetary comparisons.
- Copy validated reserved rows into plain dictionaries, remove all five
  reservation-derived fields, and require zero eligibility.
- Copy untouched execution receipts into a plain list and require zero
  eligibility even when the values still match the ledger.
- Read a genuinely unreserved historical execution-receipt pair from a strict
  ledger and retain its compatible eligible comparison.
- Reject a directly constructed validated collection when its outcome rows are
  not the exact filtered members of its fully validated ledger.
- Accept direct construction only when the complete ledger validates and the
  outcome membership is exact, then enforce the same mutation digest.
- Retain positive reserved baseline/actual controls with matching call markers
  across restart and native Codex bridge execution.

## Invariants

- Economic evidence is a function of the immutable ledger value, never a
  mutable post-read dictionary.
- Object identity is only an index lookup; the canonical receipt digest is the
  attestation.
- New execution receipts cannot self-declare legacy status by deleting fields.
- Missing or changed provenance may exclude evidence but can never manufacture
  savings.
- Historical compatibility is granted by strict validation, not by a plain
  list or caller-supplied absence.
- No live provider, credential, dependency, consumer primary, database,
  broker, order, notification, deploy, push, tag, version, publication, or
  release action is authorized.
- No token or monetary savings claim is made.
- The task claim remains `claimed` until a repaired clean candidate receives a
  fresh independent W4b `APPROVE` verdict with no P0/P1.

## Verification Plan

1. Record this replan and the blocking W4b in unit metadata, the evidence
   index, and the T3 assumption snapshot while preserving the active claim.
2. Add the mutation, copy-strip, plain-list, strict-unreserved, and constructor
   failure-first tests and capture their expected failures.
3. Implement canonical full-row digest attestation and immutable provenance
   storage in the packaged `eval_harness`.
4. Require validated provenance for every execution-receipt economic path and
   preserve only strict-ledger unreserved compatibility.
5. Rerun the complete prior provider identity, telemetry, terminal integrity,
   budget/restart, marker, bridge, routing, and economic matrices.
6. Run required root, template, SDK, taskset, lock, asset, mirror, compilation,
   full Runtime, exact diff-range, and Owner-governance checks.
7. Record a new canonical VERIFY and W4a against exact commits, then request a
   fresh independent W4b. Release the claim only after approval.
