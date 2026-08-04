---
title: TASK-AR-652 UNIT-001 Second Recheck Repair W4a
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
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-recheck.md
repair_base: afbf7724
implementation_commit: 8be79762a8caef498010e690ff939d8f8a1a99fe
implementation_tree: dfd833721015a6e5a2bf7aacc333cdca25d5353f
verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730150652.json
tags: [w4a, second-recheck, model-routing, inbox-authority, replay-safety, execution-receipts, savings-integrity]
---

# TASK-AR-652 UNIT-001 Second Recheck Repair W4a

## Verdict

`PASS_PENDING_INDEPENDENT_W4B_RECHECK — P0: 0, P1: 0, P2: 0.`

Implementation commit
`8be79762a8caef498010e690ff939d8f8a1a99fe`, tree
`dfd833721015a6e5a2bf7aacc333cdca25d5353f`, closes the four P1 findings in
the second independent W4b report. This is orchestrator self-review only. The
active claim remains claimed and the unit remains in progress until a fresh
independent verifier reviews the exact candidate.

The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..8be79762a8caef498010e690ff939d8f8a1a99fe`.
The focused second-repair range is
`afbf7724..8be79762a8caef498010e690ff939d8f8a1a99fe`.

## P1 closure map

| W4b finding | Repair and negative proof |
| --- | --- |
| P1-1 generic parent-session role-policy bypass | `render_prompt()`, `emit_call_message()`, and the CLI now always resolve through `resolve_subagent_tier()` and a provider-aware route. The CLI defaults to `native-codex`, accepts only PM/compatibility tiers, and rejects raw model names in argument parsing. A no-provider Scribe `opus` request is down-routed to `worker_low` / `gpt-5.6-terra`; a raw model exits 2 before dispatch. Legacy routing passed to message emission is role-bounded again rather than copied into an executable call contract. |
| P1-2 claim and budget authority lost through normal messages | Standard call frontmatter now carries a stable dispatch ID and optional claim, task/claim budgets, workload, baseline receipt, and escalation triggers. Native single/council bridges propagate the effective budget authority. The inbox adapter preserves those fields and normalizes `subagent-*` recipients. Budget preflight automatically binds the one active canonical claim for the task, rejects multiple active matches, uses the resolved claim for cumulative usage/reservation, and carries it into the terminal receipt. An ordinary emitted message with no duplicated claim ID is blocked before the fake provider by an active canonical zero budget. |
| P1-3 replay identity and missing policy terminal | Inbox work derives its dispatch ID from explicit frontmatter or the immutable message ID. Re-reading the same still-open message therefore hits the durable duplicate identity before a second provider call. Auto-dispatch and worker routing failures become skipped `routing_policy` receipts, with the worker also writing a bounded reply and closing its message claim. Raw-route and repeated-open-inbox tests prove zero provider calls / one terminal receipt and exactly one provider call / one receipt respectively. |
| P1-4 forged equivalent-route savings | After resolving an immutable baseline receipt, the finalizer recomputes application, model change, route change, and route status from resolved intent plus the actual and baseline observed `(model, reasoning_effort)` identities. The reporting gate independently compares those immutable observations. Identical observed routes are forced to `ineffective_equivalent` and remain ineligible even when every incoming comparison flag and baseline field claims an effective expensive-to-cheap change. |

## Failure-first evidence

- The first focused run after adding the four W4b boundary tests produced
  `16 failed, 96 passed`; every failure mapped to one of the reported bypasses.
- A separate worker raw-route lifecycle test failed at the pre-receipt
  `ValueError`, reproducing the claimed-message orphan edge before its repair.
- The final six-module template suite passes `160` tests, including:
  generic CLI high/raw negatives; standard message authority preservation;
  unique and ambiguous claim resolution; reservation-to-receipt claim
  identity; still-open inbox replay; auto and worker policy terminals; and
  forged same-route savings exclusion.
- All provider behavior used dummy or in-memory fake providers. No credential
  was read and no live provider was invoked.

## Verification

- Canonical work evidence:
  `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730150652.json`.
- Required root suite: `106 passed`.
- Required consumer-template suite: `160 passed`.
- SDK bypass suite: `2 passed`.
- Full Runtime suite: `2979 passed, 3 skipped`; the only warnings are the four
  pre-existing UI beta invalid-escape warnings.
- `runtime_asset_usage.py --check`: 38 assets, 404 uses, 0 blocks, 0 watches.
- `template_mirror_gate.py --check`: 84 expected/common, 81 identical,
  3 intentional, 0 findings.
- Host lock regeneration/check, Python compilation, `git diff --check`, and
  integrated owner governance: pass.
- Direct CLI controls confirm Scribe `opus` resolves to
  `worker_low` / `gpt-5.6-terra`, while a raw model is rejected with exit 2.

No token or monetary savings claim is made: the tests prove eligibility rules
and fail-closed behavior, not live economic performance.

## Boundary

No consumer primary, credential, provider account, package, broker, order,
database migration, notification, deployment, remote branch, tag, version,
publication, or product release was changed. Independent W4b must review this
exact candidate before the claim may be released or TASK-AR-652 may advance.
