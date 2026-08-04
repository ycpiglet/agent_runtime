---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T18:05:00+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-sdk-telemetry-final.md
tags: [task-ar-652, w4b, replan, economic-integrity, budget-integrity]
---

# TASK-AR-652 terminal economic and budget-integrity replan

## Bottom Line

The fresh independent W4b approved the focused SDK provider-telemetry repair,
then found two complete-range P1 defects in the shared execution-receipt
boundary. Failed or skipped actual receipts can qualify as economic evidence,
and terminal receipts with unavailable usage erase their conservative budget
reservation. This replan keeps the existing unit, target-file footprint,
offline boundary, and claim. Both repairs belong in the shared
`eval_harness`; no provider or consumer subsystem is added.

## Reproduced Findings

### Failed actual receipts qualify

A completed observed baseline plus an actual receipt with explicit comparable
provider/model/reasoning, tokens, and cost produced one token-eligible and one
money-eligible row even when the actual status was `error` or `skipped`.
Finalization marked those rows `applied/effective` because neither the
finalizer nor report eligibility required successful actual execution.

### Unknown usage forgets budget commitment

With task and claim budgets of ten, a first process reserved ten tokens and
then wrote a completed receipt with unavailable usage. The ledger removed the
pending reservation and committed zero. A fresh process then reserved another
ten. The hard budget therefore forgot its conservative commitment across
restart.

## Decision

- Define one receipt-success predicate for economic evidence: status must be
  `completed`, error must be absent, outcome must be `ok`, and an explicit
  failure finish reason is not accepted.
- Apply the predicate symmetrically to baseline and actual receipts.
- Make finalization leave failed, skipped, nonterminal, or internally
  inconsistent actual receipts `application_status=unverified` and
  `route_status=unverified`.
- Recompute the same predicate at report time so stale or forged
  `applied/effective` flags cannot bypass it.
- Add public bridge, finalizer, and report negatives for `error`, `skipped`,
  unknown/nonterminal status, completed-with-error, and failed baseline
  variants. A completed error-free control remains eligible only when every
  other baseline and route condition is satisfied.
- Keep recorded token usage unchanged. Never turn a reservation ceiling into
  claimed actual usage.
- For budget commitment, retain a separate conservative unobserved component
  for receipts whose usage is unavailable or partial. Its per-dispatch value
  is the remaining gap between recorded tokens and the matching reservation
  ceiling, never less than zero.
- `tokens` continues to mean recorded usage; pending `reserved_tokens`
  continues to mean open reservations; `committed_tokens` additionally
  includes conservative unobserved settlement.
- A verified pre-provider skip with no result or usage may release its
  reservation. Completed or error provider-call paths with unavailable or
  partial usage remain conservatively committed. Explicitly observed zero
  usage may settle to zero.
- Record settlement basis on the receipt without breaking the existing
  reservation-status compatibility field.
- Add true fresh-process tests for task and claim budgets covering completed
  unknown, error unknown, partial usage, observed usage, and pre-provider skip.
- Regenerate the managed host lock for the changed packaged harness.

## Evidence Taxonomy Correction

The unit accumulated W4a, W4b, and replan Markdown files under
`evidence_refs`, while `work close` requires those entries to be passed JSON
verification records. Move review documents to `review_refs` and leave only
canonical `VERIFY-*.json` records under `evidence_refs`. This changes no
acceptance result; it restores the declared closeout taxonomy.

## Unrelated Full-Suite Discrepancy

The verifier saw one UI e2e null-`project.built_at` failure. The failing test
and served UI asset are byte-identical to the acceptance base, and the local
W4a full suite passed. Record the discrepancy in the W4b report but do not
change unrelated UI code in this repair.

## Invariants

- Failed, skipped, nonterminal, or internally inconsistent execution cannot
  support token or monetary eligibility.
- Missing usage remains unknown; budget commitment is conservative accounting,
  not inferred actual usage or an economic claim.
- Observed usage supersedes its reservation only when it is authoritative.
- No live provider, credential, account, dependency, consumer primary,
  database, broker, notification, deploy, push, tag, version, publication, or
  release is authorized.
- No token or monetary savings claim is made.
- The task claim remains `claimed` until a repaired clean candidate receives
  a new independent W4b approval.

## Verification Plan

1. Add failure-first public-path economic-status and two-process unknown-usage
   budget tests and capture their failures.
2. Apply the central finalizer/report and conservative-commitment repair.
3. Rerun all prior provider identity, SDK telemetry, assertion, budget,
   restart, replay, and equivalence controls.
4. Run the required root, template, SDK, taskset, lock, and full Runtime suites
   with credential variables removed.
5. Check runtime assets, template mirror, host lock, evidence index, taskset
   state, T3 assumptions, parity, compilation, diff, and Owner governance.
6. Record a new W4a against the exact implementation commit, then submit a
   clean final candidate to a fresh independent W4b.
