---
title: TASK-AR-652 UNIT-001 Economic Routing Repair Follow-up W4a
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
reviewer: le-20260730-123600-kst-ar652001
status: passed
signal: pass
verdict: PASS_PENDING_INDEPENDENT_W4B_RECHECK
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001.md
repair_base: cf63d86e
candidate_commit: 8f65c0866977638d4ab0947235b3be9aac235bb8
candidate_tree: 212a980d3bca4b60eb0c961a5ce2109c241cecf9
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730141633.json
tags: [w4a, followup, model-routing, execution-receipts, budget-reservation, savings-integrity]
---

# TASK-AR-652 UNIT-001 Economic Routing Repair Follow-up W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B_RECHECK — P0: 0, P1: 0, P2: 0.`

Implementation commit `8f65c0866977638d4ab0947235b3be9aac235bb8`
addresses all four P1 findings in the prior independent W4b. This is
orchestrator self-review only; the active claim remains unreleased until a
fresh independent verifier reviews the exact repair.

The full acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..8f65c0866977638d4ab0947235b3be9aac235bb8`.
The focused repair range is
`cf63d86e..8f65c0866977638d4ab0947235b3be9aac235bb8`.

## P1 closure map

| Prior finding | Repair evidence |
| --- | --- |
| P1-1 role policy bypass | Worker and auto-dispatch resolve role policy for every item, including implicit `auto`; raw provider-model overrides are rejected; untriggered high-tier requests are down-routed; Scribe is executable in the native bridge; known `backend`, `uiux`, `ci-cd`, `timeline`, and `beta-tester` worker roles now resolve through explicit policy instead of generic fallback. |
| P1-2 non-authoritative, non-atomic budget | Claim JSON and task records are canonical budget authorities; explicit values may narrow but not broaden them. Lock-protected reservations include pending usage and reject duplicate dispatches. Council reservations are all-or-none. Native packets carry a mandatory immediate pre-spawn authorization check that revalidates claim authority. Completion, error, cancellation, and skip paths settle reservations with terminal receipts. |
| P1-3 receipt and ledger bypasses | Claim loss, deterministic completion/block, budget/policy skip, provider error, parentless native replies, council member error/skip, and the live SDK verification surface write terminal receipts without requiring a successful provider call. Council receipt batches append atomically. The ledger rejects duplicate receipt, reservation, and per-kind dispatch identities plus reservation/receipt task or claim mismatch before preflight. |
| P1-4 forgeable savings baseline | An economic comparison must reference an earlier immutable completed receipt with the same workload identity and observed model/token usage. Baseline tokens and billed cost are read from that receipt, not copied from caller metadata. Missing, mismatched, or unobserved references clear caller-supplied baseline fields and remain ineligible. Legacy/unreferenced rows do not contribute to savings totals. |

## Failure-first and boundary proofs

- Concurrent reservations against a task budget allow only one affordable
  dispatch; duplicate dispatch reservations allow only one side effect.
- A two-member council whose aggregate ceilings exceed the task budget creates
  no partial reservation and emits no spawn packet.
- Dry-run planning reports `planned` reservations without mutating the ledger.
- Releasing a canonical claim after packet creation causes the pre-spawn guard
  to deny execution.
- A council with only spawn errors can record zero verdicts while closing one
  error receipt per member.
- A native reply with no message-bus parent still records its execution receipt.
- A caller-supplied missing baseline receipt cannot preserve forged model,
  token, or cost comparison fields.
- The SDK helper reserves before its provider call, records both successful and
  error terminals, and honors a canonical zero budget without calling the
  provider.

An abruptly abandoned external parent process can still leave a pending
reservation; this unit does not falsely convert an unobserved outcome into a
terminal receipt. The packet requires success/cancellation/spawn-error
settlement, while automatic stale-process recovery belongs to the planned
claim heartbeat/reaper hardening in `TASK-AR-655`.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730141633.json`.
- Required root suite: `106 passed`.
- Required consumer-template suite: `146 passed`.
- SDK bypass suite: `2 passed`.
- Combined changed-template suite, including SDK: `148 passed`.
- Full Runtime suite: `2979 passed, 3 skipped, 4 existing UI beta
  invalid-escape warnings`.
- `runtime_asset_usage.py --check`: 38 assets, 404 uses, 0 blocks, 0 watches.
- `template_mirror_gate.py --check`: 84 expected/common, 81 identical,
  3 intentional, 0 findings.
- Host lock regeneration/check, root/template parity, Python compilation,
  `git diff --check`, and integrated owner governance: pass.

All provider behavior was exercised with offline fakes. No live provider was
called and no economic savings claim is made.

## Boundary

No consumer primary, credential, account setting, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or product release was changed. Independent W4b must review the
exact candidate and fresh evidence before the claim may be released.
