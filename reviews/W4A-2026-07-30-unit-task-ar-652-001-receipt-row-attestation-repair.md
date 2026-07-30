---
title: TASK-AR-652 UNIT-001 Receipt-Row Attestation Repair W4a
date: 2026-07-30
created_at: 2026-07-30T21:13:37+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: bf15acb8a3af6a7ee9de1581855457a6abd0f96e
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-economic-provenance-approval.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-receipt-row-attestation-replan.md
replan_commit: 749feec40dd33b3388a4736e63e089e429b46cb5
replan_tree: bbf2c5265885b1521c99b2dc9a32c303b2fc4d08
implementation_commit: 42ead90538b61b817fdbbccd992d896f35b26b1b
implementation_tree: 8f08cb6ee7768878ff87ed9f4786c4de07546efb
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730211246.json
tags: [w4a, economic-evidence, receipt-attestation, immutable-ledger, fail-closed]
---

# TASK-AR-652 UNIT-001 Receipt-Row Attestation Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`42ead90538b61b817fdbbccd992d896f35b26b1b`, tree
`8f08cb6ee7768878ff87ed9f4786c4de07546efb`, closes the receipt-mutation and
copy-strip P1 reproduced by the latest independent W4b. This is worker
self-review only. The claim remains claimed until a fresh independent agent
approves the exact clean final candidate.

The exact implementation ranges checked are:

- complete acceptance:
  `da4177f6211b2a1a049ba25b62332b113a54cf97..42ead90538b61b817fdbbccd992d896f35b26b1b`;
- focused receipt-attestation repair:
  `749feec40dd33b3388a4736e63e089e429b46cb5..42ead90538b61b817fdbbccd992d896f35b26b1b`;
- prior reviewed candidate through repair:
  `bf15acb8a3af6a7ee9de1581855457a6abd0f96e..42ead90538b61b817fdbbccd992d896f35b26b1b`.

`git diff --check` passed for all three ranges.

## P1 Closure

Economic provenance is now bound to the complete strict-ledger receipt value:

- `ValidatedOutcomeRecords` revalidates the complete supplied ledger even
  when constructed directly.
- The exposed outcome rows must be the exact identity-preserving filtered
  members of that validated ledger. Omitting or substituting a row raises
  `ReceiptIntegrityError`.
- Every execution receipt receives a canonical full-record SHA-256
  attestation. Object identity is used only to locate that attestation.
- Reservation, no-provider settlement, and provider-call-start records are
  stored as canonical immutable JSON snapshots inside a read-only mapping, so
  caller-held hidden-record dictionaries cannot alter the validated context.
- Before any economic or route field is trusted, the current receipt digest
  must equal the strict-ledger digest. Any post-read change makes the row
  ineligible.
- A plain `agent-runtime-execution-receipt/v1` list has no validated entry and
  always fails economic eligibility. Removing reservation-derived fields can
  no longer self-declare legacy status.
- Historical unreserved execution receipts remain compatible only after they
  are actually read from, or constructed as the exact outcome view of, a
  complete validated strict ledger.
- Ordinary legacy outcome rows without the execution-receipt schema retain
  their existing non-economic scoreboard behavior.

The previous provider-call, reservation, settlement, budget-authority,
provider, execution-surface, transition, derived-field, restart, and
no-provider skip checks remain intact.

## Failure-First and Adversarial Evidence

- Before implementation, the new selected matrix produced
  `21 failed, 16 passed`.
- After repair, the initial selected matrix passed `37`.
- The expanded post-read mutation matrix passed `67`. It covers complete token
  components, billed cost, currency, configured and observed provider/model/
  reasoning fields, telemetry statuses, terminal status/error/finish/outcome,
  task/claim/workload/baseline identities, route fields, source, reservation
  derivations, dispatch/receipt IDs, and the immutable flag on both baseline
  and actual rows.
- A reserved copied pair with all five derived budget fields removed produces
  zero token and monetary eligibility.
- An untouched execution-receipt pair copied to a plain list produces zero
  eligibility.
- A genuinely unreserved historical pair read from a strict ledger retains
  one eligible token and monetary comparison.
- Direct construction with incomplete outcome membership or a corrupt
  duplicate-dispatch ledger raises `ReceiptIntegrityError`.
- A valid direct construction is positive before receipt mutation and
  ineligible afterward.
- Mutating caller-held reservation and call-start dictionaries after
  construction does not change the immutable validated snapshot.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730211246.json`.
- Required root routing/claim/Doctor suite: `108 passed`.
- Required six-module consumer-template suite: `383 passed`.
- SDK fake-provider and adapter suite: `5 passed`.
- Eval-harness suite: `223 passed`.
- Taskset plus managed-host lock suites: `35 passed` (`12 + 23`); lock check
  is current.
- Full Runtime suite: `2982 passed, 3 skipped, 4 warnings`; the warnings are
  the pre-existing UI beta invalid-escape warnings.
- Compilation of the changed production and test Python files passed.
- Template mirror remains `84 common / 81 identical / 3 intentional / 0
  findings`.
- Runtime asset usage remains `38 assets / 404 uses / 0 blocks / 0 watches`.
- Evidence index, plan-assumption, taskset work, and Owner-governance gates
  pass after metadata refresh.

All provider paths used fake, dummy, synthetic, temporary, or in-memory data.
Credential variables were removed from verification commands. No credential
value was read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests establish evidence
eligibility and fail-closed exclusion behavior only.

## Boundary

The claim file retained SHA-256
`997dbf33dbb7cc8e660614dcb037476106ecf473ee6a568bbcd69ff7a0aa37ce`
and remains `claimed`, phase `wave-claimed`, under worker
`le-20260730-123600-kst-ar652001`.

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must approve the exact
clean candidate before claim release, W5 integration, W6 closeout, or
TASK-AR-653 dispatch.
