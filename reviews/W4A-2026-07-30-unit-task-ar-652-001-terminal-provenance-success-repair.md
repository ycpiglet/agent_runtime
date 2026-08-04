---
title: TASK-AR-652 UNIT-001 Terminal Success and Settlement Provenance Repair W4a
date: 2026-07-30
created_at: 2026-07-30T19:02:04+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: fcc0af91040a80b4528592a8a4a0cf0b6e3d6d24
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-terminal-integrity-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-terminal-provenance-success-replan.md
replan_commit: a70dfeefc59418cff987e296a93fb4061aae96b2
implementation_commit: 8534f2a13a8d059168c4d9ae8b3718a0862f4eee
implementation_tree: 354e1b74aa2e99634937e55bc282ce7fdf21dfa5
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730190052.json
tags: [w4a, terminal-success, settlement-provenance, budget-integrity, restart]
---

# TASK-AR-652 UNIT-001 Terminal Success and Settlement Provenance Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`8534f2a13a8d059168c4d9ae8b3718a0862f4eee`, tree
`354e1b74aa2e99634937e55bc282ce7fdf21dfa5`, closes both P1 findings from
the latest independent review. This is worker/orchestrator self-review only.
The claim remains claimed until a fresh independent verifier approves the
exact final candidate.

The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..8534f2a13a8d059168c4d9ae8b3718a0862f4eee`.
The focused repair range is
`a70dfeefc59418cff987e296a93fb4061aae96b2..8534f2a13a8d059168c4d9ae8b3718a0862f4eee`.

## P1 Closure

Economic execution success is now a positive classification. Status must be
`completed`, error must be absent, outcome must be `ok`, and the normalized
finish value must be one of `stop`, `completed`, `end_turn`,
`stop_sequence`, or `success`.

- `incomplete`, `in_progress`, `queued`, `requires_action`, an unknown finish,
  truncation, failure, timeout, cancellation, and skipped values fail closed.
- The predicate is applied symmetrically to actual and baseline receipts
  during finalization and recomputed at report time.
- Public native bridge tests cover all supported success spellings plus
  nonterminal and unknown negatives.
- Caller-forged `applied`, `effective`, and route-changed fields cannot make a
  non-success execution economically eligible.
- The existing provider identity, token-component, billed-cost, SDK telemetry,
  and fully observed success controls remain intact.

Budget release no longer relies on the terminal receipt's source string.

- Generic execution receipts always leave an existing reservation at observed
  usage or the conservative ceiling; they cannot claim a no-call release.
- A new immutable `agent-runtime-no-provider-settlement/v1` ledger record is
  appended atomically with its skipped receipt.
- The settlement binds the complete reservation fingerprint, reservation ID,
  dispatch, task, claim, budget-authority fingerprint, reservation source, and
  receipt source.
- Only `auto_dispatch -> session_budget_preflight` and
  `auto_dispatch -> claim_preflight` are valid no-provider transitions.
- Routing policy, denied budget preflight, deterministic preflight,
  agent-worker pre-claim, and arbitrary generic receipt paths cannot release a
  matching reservation.
- Provider/model/reasoning observations, token components, token totals, or
  billed-cost observations invalidate a no-provider settlement.
- Missing, duplicate, orphaned, mismatched, or tampered settlement provenance
  makes the ledger fail closed.
- Cumulative task and claim accounting recomputes the settlement basis from
  the reservation/settlement/receipt triple; a forged stored
  `budget_settlement_basis` does not release commitment.

## Failure-First and Adversarial Evidence

- The new actual, baseline, finalizer, public bridge, and fresh-process
  provenance matrix first produced `28 failed, 14 passed`.
- The 28 failures were exactly the five nonterminal/unknown finish variants at
  four economic boundaries plus eight generic source/reservation release
  variants.
- After repair, the expanded focused matrix passes `50`.
- Fresh-process task and claim tests prove all impossible and generic source
  pairs retain ten committed tokens and block a second reservation.
- Dedicated controls prove both legitimate auto-dispatch transitions release
  exactly one reservation and allow a second reservation after restart.
- Direct execution-surface tests prove the shipped session-budget and
  claim-lost branches emit the dedicated settlement and perform no provider
  call.
- Reservation-fingerprint tampering, provider observation on a no-call path,
  an invalid source transition, and a forged stored settlement basis are
  independently rejected or conservatively retained.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730190052.json`.
- Required root suite: `108 passed`.
- Required six-module consumer-template suite: `256 passed`.
- SDK fake-provider suite: `3 passed`.
- Taskset governance suite: `12 passed`.
- Managed-host lock suite: `23 passed`; lock check is current.
- Full Runtime suite: `2982 passed, 3 skipped`; the four warnings are the
  pre-existing UI beta invalid-escape warnings.
- In-memory compilation of all five changed Python files passed.
- Template mirror remains `84 common / 81 identical / 3 intentional / 0
  findings`.
- Runtime asset usage remains `38 assets / 404 uses / 0 blocks / 0 watches`.
- Evidence index and taskset work gates report zero findings.
- Integrated Owner governance passed at the implementation commit.

All provider paths used fake, dummy, synthetic, or in-memory providers.
Credential variables were removed from verification commands. No credential
value was read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests prove eligibility and
budget-accounting behavior only.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must approve the exact
clean candidate before claim release or task advancement.
