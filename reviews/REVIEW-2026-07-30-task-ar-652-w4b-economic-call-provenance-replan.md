---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T20:27:00+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-call-provenance-final.md
tags: [task-ar-652, w4b, replan, economic-evidence, call-provenance]
---

# TASK-AR-652 economic call-provenance replan

## Bottom Line

The fresh independent W4b verified the provider-call marker at the persistent
budget boundary, then reproduced a remaining fail-open economic boundary. A
reserved baseline and reserved actual can both lack a call-start marker,
retain their conservative reservation ceilings, and nevertheless produce an
eligible token and billed-cost comparison. The report sees filtered receipt
rows but not the validated reservation and marker graph, so it trusts
caller-supplied observations that persistent accounting correctly distrusts.

This replan keeps the current unit, offline boundary, worktree, and active
claim. It extends the same durable provider-call provenance used by budget
settlement into baseline verification and economic eligibility.

## Reproduced Finding

The independent true-restart fixture reserved 200 tokens for a synthetic
baseline and 200 for a synthetic actual, recorded observed token and billed
cost fields without any provider-call marker, and then re-read the durable
ledger in a new process. Persistent accounting committed the full 400-token
ceiling, but the economic report emitted one eligible token record and one
eligible monetary record. No provider was called.

The complete acceptance range also contains one extra blank line at the end
of the prior W4b report. That whitespace defect must be removed and the next
W4a must name every exact range checked.

## Decision

- Treat a receipt with a durable budget reservation as new-runtime evidence.
  Its token or billed-cost observations are economically eligible only when
  the validated ledger contains the same matching call-start provenance that
  permits `observed_usage` settlement.
- Recompute reserved-receipt provenance from the strict ledger's reservation,
  call-start marker, receipt, budget-authority fingerprint, provider,
  execution surface, status, and source transition. Filtering markers out of
  user-facing rows must not discard this report context.
- Bind every persisted execution receipt's derived reservation, no-provider
  settlement, call-start, reservation-status, and settlement-basis fields to
  the records actually present in the strict ledger. A forged or stale
  derived field is an integrity failure, not economic evidence.
- Make `read_outcomes()` return ordinary list-compatible outcome rows together
  with validated, in-memory ledger provenance. `report()` must use that
  context for reserved rows. Copying or manually constructing a reserved row
  without validated context fails closed.
- Keep explicit compatibility for truly unreserved legacy execution
  receipts. Their existing observation, success, workload, route, and
  baseline checks continue to apply because historical unreserved ledgers
  have no reservation or marker graph to validate.
- Require both a reserved actual and its reserved baseline to have validated
  matching markers before either token or monetary savings is eligible.
- Use distinct exclusion reasons for missing actual and missing baseline
  provider-call provenance so operational diagnosis remains actionable.
- Preserve strict ledger rejection for orphan, replayed, malformed, wrong
  reservation, wrong authority, wrong provider, wrong execution surface, and
  wrong transition markers. An integrity-rejected ledger cannot emit an
  economic report.
- Keep the dedicated pre-provider skip path economically ineligible. A
  no-provider settlement proves that no billable comparison may be claimed.
- Regenerate the managed-host lock after packaged Runtime assets change.

## Failure-First Matrix

- A public durable-ledger baseline and actual with reservations, observed
  tokens and billed costs, but no call-start markers must reproduce the
  current false positive before implementation, including after a fresh
  process restart.
- Missing marker on only the actual and missing marker on only the baseline
  must each produce zero token and monetary eligible records after restart.
- A reserved skipped result, provider-error result, or copied reserved rows
  without validated ledger context must not enter economic evidence.
- Orphan, mismatched reservation, wrong authority, wrong provider, wrong
  execution surface, wrong source transition, forged linkage, and forged
  settlement-basis ledgers must fail strict fresh-process reading and cannot
  emit a report.
- A positive public-ledger control with valid markers for both baseline and
  actual must retain one eligible token and monetary comparison.
- A positive native Codex bridge control must reserve, authorize, record
  matching native replies for both baseline and actual, survive restart, and
  retain one eligible comparison.
- Truly unreserved legacy receipt pairs must retain their existing compatible
  report behavior, while adding a reservation identifier to copied rows
  without validated context must make them ineligible.

## Invariants

- Persistent accounting and economic reporting use the same call-provenance
  truth for every reserved receipt.
- A stored settlement basis or call-start identifier is never sufficient
  without the validated ledger records that derive it.
- Both sides of a savings comparison must prove their own provider call.
- Missing provenance may over-reserve and exclude evidence, but can never
  under-account or manufacture savings.
- Strict ledger corruption fails closed before reporting.
- Historical unreserved compatibility is explicit and cannot be used by new
  reserved execution surfaces as an escape hatch.
- No live provider, credential, account, dependency, consumer primary,
  database, broker, notification, deploy, push, tag, version, publication, or
  release action is authorized.
- No token or monetary savings claim is made.
- The task claim remains `claimed` until the repaired clean candidate receives
  a new independent W4b `APPROVE` verdict with no task-scope P0/P1.

## Verification Plan

1. Record this replan and the blocking W4b in the unit, evidence index, and T3
   assumption snapshot while keeping the claim active.
2. Add the public-ledger, native-bridge, strict-integrity, copied-context, and
   unreserved-compatibility failure-first matrix; capture the expected
   failures before implementation.
3. Bind persisted derived fields during strict validation and carry validated
   ledger provenance from `read_outcomes()` into `report()`.
4. Gate baseline, actual token, and actual monetary eligibility on that
   provenance while preserving the explicit unreserved compatibility rule.
5. Rerun every prior provider identity, SDK telemetry, terminal-success,
   no-provider settlement, budget/restart, replay, role-tier, equivalence, and
   economic-report control.
6. Run the required root, template, SDK, taskset, lock, and full Runtime suites
   with credential variables removed.
7. Check Runtime assets, template mirror, host lock, evidence index, taskset
   state, T3 assumptions, compilation, complete and focused diff ranges, and
   Owner governance.
8. Record a new canonical VERIFY and W4a against exact commits, then submit a
   clean candidate to a fresh independent W4b. Release the claim only after
   approval.
