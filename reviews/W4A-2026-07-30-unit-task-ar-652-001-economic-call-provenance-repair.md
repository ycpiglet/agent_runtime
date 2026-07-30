---
title: TASK-AR-652 UNIT-001 Economic Call-Provenance Repair W4a
date: 2026-07-30
created_at: 2026-07-30T20:45:00+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: 88caa8b7ed65aac53a03550169e824e273a6624d
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-call-provenance-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-economic-call-provenance-replan.md
replan_commit: 4ef0f96a92e3a364b794c987cbcc59ddb675b222
implementation_commit: edfe564b76415f3324654d9d223671a58ccdb276
implementation_tree: 80c340ab02213f781e1899598e7a4015ec205855
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730204330.json
tags: [w4a, economic-evidence, provider-call-provenance, ledger-integrity, restart]
---

# TASK-AR-652 UNIT-001 Economic Call-Provenance Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`edfe564b76415f3324654d9d223671a58ccdb276`, tree
`80c340ab02213f781e1899598e7a4015ec205855`, closes the economic-evidence P1
and complete-range whitespace P2 from the latest independent review. This is
worker/orchestrator self-review only. The claim remains claimed until a fresh
independent verifier approves the exact clean final candidate.

The exact diff ranges checked are:

- complete acceptance:
  `da4177f6211b2a1a049ba25b62332b113a54cf97..edfe564b76415f3324654d9d223671a58ccdb276`;
- focused economic repair:
  `4ef0f96a92e3a364b794c987cbcc59ddb675b222..edfe564b76415f3324654d9d223671a58ccdb276`;
- prior reviewed candidate through repair:
  `88caa8b7ed65aac53a03550169e824e273a6624d..edfe564b76415f3324654d9d223671a58ccdb276`.

`git diff --check` passed for all three ranges. The extra EOF blank in
`reviews/W4B-2026-07-30-unit-task-ar-652-001-provenance-final.md` is removed.

## P1 Closure

Reserved economic evidence now uses strict-ledger call provenance:

- `read_outcomes()` still hides reservations, no-provider settlements, and
  call-start markers from user-facing rows, but returns a list-compatible
  outcome collection carrying the validated ledger relationships in memory.
- `report()` requires that context for every receipt claiming a reservation.
  Copying reserved rows into an unattested plain list makes both baseline and
  actual evidence fail closed.
- Both baseline and actual eligibility recompute the reservation, marker,
  authority fingerprint, provider, execution surface, provider-result status,
  source transition, and `observed_usage` settlement relationship.
- Missing baseline provenance reports
  `baseline_provider_call_provenance_unverified`; missing actual provenance
  reports `actual_provider_call_provenance_unverified`.
- A reserved baseline without a matching marker is also rejected while the
  actual receipt is finalized, so its baseline-reference status cannot claim
  verified provenance.
- Truly unreserved legacy receipts retain explicit compatibility and continue
  through the pre-existing success, workload, route, token, and billed-cost
  checks.

Persisted derived fields are now ledger-bound:

- Strict ledger validation recomputes reservation ID, no-provider settlement
  ID, call-start ID, reservation status, and settlement basis for every new
  execution receipt.
- A forged, stale, missing, or contradictory derived value raises
  `ReceiptIntegrityError`; stored `observed_usage` or a stored marker ID is
  never sufficient by itself.
- Historical unreserved execution receipts written before derived budget
  fields existed remain readable. New unreserved receipts with derived fields
  must match the explicit `not_required_or_unreserved` state.
- Invalid and orphan markers continue to fail strict ledger validation before
  any report can be emitted.

## Failure-First and Adversarial Evidence

- Before implementation, the focused new matrix produced
  `10 failed, 2 passed`. The failures were the reproduced false-positive
  economic comparisons, unattested copied rows, unbound derived fields, and
  native bridge authorization omissions.
- After repair, the focused economic, native bridge, finish-state,
  derived-field, and marker-integrity matrix passes `28`.
- A true fresh process excludes pairs where both markers are missing, only the
  baseline marker is missing, or only the actual marker is missing.
- The positive fresh-process public-ledger control with matching baseline and
  actual markers retains one token and one monetary eligible record.
- Native Codex bridge controls cover baseline authorization missing, actual
  authorization missing, and both authorizations present. Only the
  both-authorized pair is eligible.
- A marked skipped actual remains conservative and economically ineligible
  after restart.
- Fresh-process corruption controls reject orphan markers, reservation and
  authority mismatches, wrong provider, wrong execution surface, wrong source
  transition, and forged reservation, call-start, status, or settlement-basis
  derivations.
- Direct unreserved legacy pairs retain token and billed-cost compatibility,
  proving that the migration rule is deliberate rather than an accidental
  blanket denial.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730204330.json`.
- Required root suite: `108 passed`.
- Required six-module consumer-template suite: `310 passed`.
- SDK fake-provider and adapter suite: `5 passed`.
- Focused economic/adversarial suite: `28 passed`.
- Eval-harness and native-bridge aggregate: `186 passed`.
- Taskset governance suite: `12 passed`.
- Managed-host lock suite: `23 passed`; lock check is current.
- Full Runtime suite: `2982 passed, 3 skipped`; the four warnings are the
  pre-existing UI beta invalid-escape warnings.
- Compilation of the changed production and test Python files passed.
- Template mirror remains `84 common / 81 identical / 3 intentional / 0
  findings`.
- Runtime asset usage remains `38 assets / 404 uses / 0 blocks / 0 watches`.
- Evidence index, taskset work, plan-assumption, state-sync, and Owner
  governance checks pass after metadata refresh.

All provider paths used fake, dummy, synthetic, or in-memory observations.
Credential variables were removed from verification commands. No credential
value was read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests prove evidence
eligibility and conservative budget-accounting behavior only.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must approve the exact
clean candidate before claim release or task advancement.
