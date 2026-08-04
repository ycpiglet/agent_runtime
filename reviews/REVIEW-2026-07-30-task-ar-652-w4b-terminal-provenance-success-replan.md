---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T18:44:14+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-terminal-integrity-final.md
tags: [task-ar-652, w4b, replan, terminal-success, settlement-provenance]
---

# TASK-AR-652 terminal-success and settlement-provenance replan

## Bottom Line

The fresh independent W4b verified that the prior error, skipped, partial
usage, unknown usage, provider-identity, and SDK telemetry repairs remain
effective, then reproduced two fail-open variants at the same economic and
budget boundaries. The economic success predicate uses a failure denylist, so
unknown or nonterminal finish values can qualify. Budget release trusts a
receipt source string without a durable, reservation-bound no-call
settlement. This replan keeps the current unit, offline boundary, worktree,
and claim, and replaces both fail-open classifications with positive,
structured evidence.

## Reproduced Findings

### Nonterminal finish values qualify as successful

Completed, error-free, outcome-ok actual receipts with `incomplete`,
`in_progress`, `queued`, or `requires_action` finish values finalized as
`applied/effective` and contributed to both token and monetary eligibility.
The same defect allowed an incomplete baseline to become verified. These
values were absent from the failure denylist even though they do not prove a
terminal successful execution.

### Source-only no-call claims erase a reservation

A process reserved the full task and claim budget, then wrote a skipped,
unobserved receipt using `routing_policy`, `budget_preflight`, or either
deterministic-preflight source. The current source allowlist classified each
as a pre-provider skip and released the reservation. A fresh process could
reserve the full budget again. Those sources run before reservation in the
shipped execution ordering and therefore cannot legitimately settle a
matching reservation.

## Decision

- Replace the economic finish failure denylist with a normalized successful
  finish allowlist. A receipt supports economic evidence only when its status
  is `completed`, error is absent, outcome is `ok`, and its finish value is a
  recognized terminal success.
- Recognize the Runtime's supported terminal success spellings only:
  `stop`, `completed`, `end_turn`, `stop_sequence`, and `success`.
  Unrecognized, empty, incomplete, queued, in-progress, action-required,
  truncation, failure, cancellation, timeout, and skipped values fail closed.
- Apply the same predicate to baseline verification, actual finalization, and
  report-time recomputation. Caller-supplied route flags never override it.
- Add public bridge, finalizer, and report matrices for actual and baseline
  nonterminal/unknown finish values, with observed successful controls for
  supported provider spellings.
- Generic execution receipts must never release an existing reservation from
  their `source` value alone.
- Add a dedicated immutable no-provider-call settlement record and a narrow
  recording operation. It must atomically bind one pending reservation to one
  skipped terminal receipt and copy provenance from the ledger rather than
  trusting a receipt-supplied reservation identifier or budget preflight.
- Permit only the shipped post-reservation transitions:
  `auto_dispatch -> session_budget_preflight` and
  `auto_dispatch -> claim_preflight`. Routing policy, denied budget
  preflight, deterministic preflight, agent-worker pre-claim, provider error,
  and arbitrary sources cannot release a matching reservation.
- Validate settlement identity, reservation identity, dispatch, task, claim,
  authority fingerprint, transition, and the absence of provider, token, and
  billed-cost observations. Invalid, duplicate, orphaned, or contradictory
  settlements fail closed.
- Cumulative task and claim usage may report `pre_provider_skip` only from a
  validated settlement/receipt/reservation triple. Otherwise the reservation
  remains pending or settles to the conservative ceiling.
- Update `auto_dispatch` to use the dedicated operation for its two legitimate
  post-reservation no-call branches. Other execution surfaces keep the generic
  receipt path.
- Add true fresh-process task-and-claim tests for every impossible source
  pair, forged stored settlement basis, missing/mismatched provenance, and
  both legitimate auto-dispatch transitions.
- Regenerate the managed host lock for the changed packaged Runtime assets.

## Invariants

- Only a positively recognized terminal success can support token or monetary
  eligibility.
- A source string, caller-supplied preflight object, or stored settlement-basis
  field is not authoritative evidence that no provider call occurred.
- Missing or partial usage remains unknown and conservatively committed; it is
  never converted into claimed actual usage.
- A valid no-call settlement releases exactly one matching reservation and
  cannot be replayed for another dispatch, task, claim, or authority.
- No live provider, credential, account, dependency, consumer primary,
  database, broker, notification, deploy, push, tag, version, publication, or
  release action is authorized.
- No token or monetary savings claim is made.
- The task claim remains `claimed` until a repaired clean candidate receives a
  new independent W4b approval.

## Verification Plan

1. Record this replan and the blocking W4b in the unit, evidence index, and T3
   assumption snapshot while keeping the claim active.
2. Add failure-first public bridge/finalizer/report finish matrices and
   fresh-process settlement-provenance matrices; capture the expected
   failures before implementation.
3. Implement the terminal-success allowlist, immutable settlement schema,
   ledger validation, dedicated no-call API, cumulative-accounting binding,
   and the two auto-dispatch integrations.
4. Rerun all prior provider identity, SDK telemetry, economic assertion,
   budget/restart, replay, role-tier, and equivalence controls.
5. Run the required root, template, SDK, taskset, lock, and full Runtime suites
   with credential variables removed.
6. Check runtime assets, template mirror, host lock, evidence index, taskset
   state, T3 assumptions, root/template parity, compilation, diff, and Owner
   governance.
7. Record a new canonical VERIFY and W4a against exact commits, then submit a
   clean candidate to a fresh independent W4b. Release the claim only after an
   `APPROVE` verdict with no task-scope P0/P1.
