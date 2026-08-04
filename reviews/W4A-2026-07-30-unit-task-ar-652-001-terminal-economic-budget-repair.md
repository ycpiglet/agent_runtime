---
title: TASK-AR-652 UNIT-001 Terminal Economic and Budget Integrity Repair W4a
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: ef08f44e3cc4a31b76774db449a797e13aa6132e
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-sdk-telemetry-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-terminal-economic-budget-replan.md
replan_commit: 3527e0df65c2764bd115804fb3a0de353582769f
implementation_commit: 8e34fcc0dc8290b95c1310f65151637c35cf4055
implementation_tree: 3deed20cbfc1ea4bdfc4b8fa47ffbfb61fb0ec07
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730182347.json
tags: [w4a, economic-integrity, budget-integrity, receipt-integrity, restart]
---

# TASK-AR-652 UNIT-001 Terminal Economic and Budget Integrity Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`8e34fcc0dc8290b95c1310f65151637c35cf4055`, tree
`3deed20cbfc1ea4bdfc4b8fa47ffbfb61fb0ec07`, closes both P1 findings from
the latest independent review. This is worker/orchestrator self-review only.
The claim remains claimed until a fresh independent verifier approves the
exact final candidate.

The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..8e34fcc0dc8290b95c1310f65151637c35cf4055`.
The focused repair follows replan commit
`3527e0df65c2764bd115804fb3a0de353582769f`.

## P1 Closure

Economic eligibility now uses one execution-success predicate for both sides
of a comparison. A receipt is successful only when its status is completed,
its error is absent, its outcome is `ok`, and its finish reason is not an
explicit failure signal.

- Failed, skipped, nonterminal, completed-with-error, failed-outcome, and
  failed-finish actual rows finalize as `unverified`.
- The report recomputes success, so forged `applied/effective` fields do not
  bypass the guard.
- Failed baselines are invalid both during finalization and report-time
  reconstruction.
- Token evidence requires observed input/output components whose sum matches
  the total.
- Monetary evidence requires explicitly observed, finite, non-negative billed
  cost with a currency.
- A fully observed successful public `record_reply` control remains eligible;
  the tests make no savings claim.

Persistent budget accounting no longer forgets unknown terminal usage.

- `tokens` remains recorded usage and is never filled from a reservation.
- Open reservations remain `reserved_tokens`.
- Completed, error, or post-dispatch skipped receipts with unavailable usage
  retain the gap between recorded tokens and their reservation ceiling as
  `conservative_unobserved_tokens`.
- `committed_tokens` is recorded usage plus open reservations plus that
  conservative gap.
- Authoritatively observed usage, including observed zero, settles to the
  observed value.
- Explicit no-provider-call paths with no result, usage, or billed cost may
  release their reservation.
- Each receipt records `budget_settlement_basis` while preserving the existing
  `budget_reservation_status` field.

## Failure-First Evidence

- The terminal status, failed-baseline, public bridge, and restart tests first
  produced `19 failed`.
- The additional incomplete-token and unobserved-cost negatives first
  produced `4 failed`.
- The original fresh-process reproduction allowed a second reservation after
  completed unknown usage; the repaired task and claim accounting each retain
  the full conservative commitment.
- Fresh-process tests cover completed unknown, error unknown, post-dispatch
  skipped unknown, partial usage, observed usage, and an explicit pre-provider
  skip release control.
- After repair, the focused matrix passes `24`.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730182347.json`.
- Required root suite: `108 passed`.
- Required six-module consumer-template suite: `218 passed`.
- SDK fake-provider suite: `3 passed`.
- Taskset governance suite: `12 passed`.
- Managed-host lock suite: `23 passed`; lock check is current.
- Full Runtime suite: `2982 passed, 3 skipped`; the four warnings are the
  pre-existing UI beta invalid-escape warnings.
- The prior independent UI e2e race did not reproduce on this implementation
  commit.
- Integrated Owner governance passed at the implementation commit.

All provider paths used fake, dummy, or in-memory providers. Credential
variables were removed from verification commands. No credential value was
read and no live provider or network endpoint was called.

No token or monetary savings claim is made. The tests prove eligibility and
accounting behavior only.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or release state changed. Independent W4b must approve the exact
clean candidate before claim release or task advancement.
