---
title: W4b Recheck - TASK-AR-652 Independent Economic Routing Review
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
finding_counts: {P0: 0, P1: 4, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
repair_base: cf63d86e
implementation_commit: 8f65c0866977638d4ab0947235b3be9aac235bb8
reviewed_commit: 092f3e20c7545262a17b1bc3a7a19c535fbc73c4
reviewed_tree: ca08c74a9f6965919cde0a8d455dd0fa0c7c4603
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..092f3e20c7545262a17b1bc3a7a19c535fbc73c4
repair_review_range: cf63d86e..8f65c0866977638d4ab0947235b3be9aac235bb8
verified_by: codex-independent-task-ar-652-w4b-recheck
verifier_role: independent-auditor
independence_status: independent
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-followup.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730141633.json
tags: [w4b, recheck, independent-verification, model-routing, execution-receipts, persistent-budget, savings-integrity, revise]
---

# W4b Recheck - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 4, P2: 0.`

The exact clean candidate reviewed before this evidence file was added was
commit `092f3e20c7545262a17b1bc3a7a19c535fbc73c4`, tree
`ca08c74a9f6965919cde0a8d455dd0fa0c7c4603`. The complete acceptance range
was
`da4177f6211b2a1a049ba25b62332b113a54cf97..092f3e20c7545262a17b1bc3a7a19c535fbc73c4`;
the focused repair range was
`cf63d86e..8f65c0866977638d4ab0947235b3be9aac235bb8`.

The repair closes important mechanics: reservations are locked, duplicate
ledger identities fail closed, claim-loss and native failure paths can write
terminal receipts, council reservation is all-or-none, and referenced
baseline values are loaded from an immutable receipt. However, the ordinary
session and inbox paths still bypass those mechanics in four release-blocking
ways. All four prior P1 categories therefore remain open.

## P1-1 - The generic parent-session dispatch still bypasses role policy

`src/agent_runtime/templates/project/scripts/subagent_dispatch.py:63-77`
resolves the legacy free-form `--model` independently of the role policy.
`render_prompt()` uses that legacy result whenever no provider is supplied
(`:424-433,478-488`). Although `_cmd_dispatch()` also computes a role route,
it converts that route into the prompt-driving provider route only when
`--provider` is explicitly present (`:753-771`), while the parser defaults
the provider to an empty string (`:858-867`).

This is a documented parent-session execution surface, and its generated
prompt tells the parent which Agent-tool model to invoke. A Scribe can
therefore select a high tier without an escalation trigger or pass a raw
provider model:

```text
$ PYTHONDONTWRITEBYTECODE=1 python \
  src/agent_runtime/templates/project/scripts/subagent_dispatch.py \
  --role scribe --task-id TASK-OFFLINE \
  --intent 'archive bounded established facts' --model opus --dry-run
Agent tool model: opus
grade=Medium policy_tier=sonnet selected_tier=opus signals=manual_override

$ ... --role scribe ... --model vendor-ultra-expensive --dry-run
Agent tool model: vendor-ultra-expensive
grade=Medium policy_tier=sonnet selected_tier=vendor-ultra-expensive
signals=manual_override,raw_provider_model
```

The provider-aware Codex bridge now enforces role policy, but that does not
make the still-shipped generic surface safe. Required repair: bind every
session dispatch to `resolve_subagent_tier()`, reject raw provider models, and
deny or down-route unauthorized high requests even when `--provider` is
omitted. Add CLI-level negatives for Scribe high/raw requests without a
registered trigger.

## P1-2 - Canonical claim budgets are not automatically bound to normal messages

`eval_harness._budget_authority()` reads a claim record only when a caller
already supplies `claim_id` (`eval_harness.py:313-398`). The worker obtains
that ID and both explicit budgets only from message frontmatter
(`agent_worker.py:554-561,864-875`). The standard
`subagent_dispatch.emit_call_message()` schema contains neither a claim ID nor
task/claim budgets (`subagent_dispatch.py:521-625`).

The inbox adapter compounds the gap. `auto_dispatch.inbox_work_items()`
reconstructs a narrow item at `auto_dispatch.py:1049-1069` and discards
`claim_id`, `dispatch_id`, `task_token_budget`, `claim_token_budget`,
`escalation_triggers`, `eval_baseline_receipt_id`, and `eval_workload_id`.
An offline message containing every one of those fields produced:

```json
{"claim_id": null, "claim_token_budget": null, "dispatch_id": null,
 "escalation_triggers": null, "eval_baseline_receipt_id": null,
 "eval_workload_id": null, "task_token_budget": null}
```

A separate temporary-root fake-provider reproduction created an active
canonical `CLAIM-ZERO` for `TASK-ZERO` with `claim_token_budget: 0`, then
processed the normal task message without duplicating the claim ID:

```json
{"active_canonical_claim_budget": 0, "message_claim_id": null,
 "provider_calls": 1, "receipt_status": "completed",
 "receipt_claim_id": null, "budget_authority_source": "unconfigured",
 "budget_reason": "within_budget"}
```

Thus the zero canonical claim budget does not block the provider call unless
the dispatch caller redundantly propagates its authority. Required repair:
make claim identity part of the standard dispatch contract, preserve all
authority fields through inbox adaptation, and fail closed when a
claim-scoped dispatch cannot resolve an unambiguous active claim. Add an
end-to-end zero-claim-budget test starting from the ordinary emitted/inbox
message.

## P1-3 - Inbox replay changes dispatch identity, and policy rejection has no receipt

`auto_dispatch.run()` falls back to a fresh UUID at
`auto_dispatch.py:610-614`. Because the read-only inbox adapter drops both an
explicit `dispatch_id` and the stable message ID as dispatch identity, two
runs over the same still-open inbox message are treated as two billable
dispatches. An offline fake provider reproduced:

```json
{"source_message_id": "MSG-STABLE", "provider_call_count": 2,
 "provider_dispatch_ids": ["dispatch-77a12f23e9de",
                           "dispatch-653575920f76"],
 "receipt_dispatch_ids": ["dispatch-77a12f23e9de",
                          "dispatch-653575920f76"],
 "run_errors": [null, null]}
```

The same entry point resolves routing before reserving or entering any
receipt-producing error path (`auto_dispatch.py:619-643`). A message with
stable `dispatch_id: POLICY-RAW`, role `scribe`, and raw
`routing_model: vendor-ultra` raised:

```json
{"error": "ValueError: role-bound dispatch requires a PM tier or haiku/sonnet/opus compatibility tier",
 "ledger_exists": false, "receipt_count": 0}
```

Locked duplicate-receipt checks cannot prevent either gap: replay has a new
ID, and policy failure occurs before any terminal record. Required repair:
derive a stable dispatch ID from the immutable inbox message identity,
preserve an explicit ID when supplied, reject replay before a provider call,
and convert routing/policy rejection into exactly one skipped/error receipt.
Add repeated read-only inbox and invalid-routing terminal tests.

## P1-4 - Verified baseline values do not recompute route equivalence

`eval_harness._finalize_execution_receipt()` correctly replaces baseline
model, reasoning, token, and cost fields from the referenced immutable receipt
(`eval_harness.py:1101-1152`). It does not recompute `route_changed`,
`route_status`, or `application_status`. Those flags were calculated earlier
from caller-supplied comparison metadata
(`agent_worker.py:517-537,668-680`). The report then trusts the preserved
flags after checking only that a baseline reference was verified
(`eval_harness.py:1343-1363`).

An offline ledger reproduction recorded a baseline and actual execution with
the identical observed native route
`(claude-haiku-4-5, low)`. The actual call supplied forged comparison metadata
for `(claude-opus-4-8, high)` and caller-derived effective-route flags. The
finalizer corrected the baseline route but retained the flags:

```json
{"baseline_route": ["claude-haiku-4-5", "low"],
 "actual_route": ["claude-haiku-4-5", "low"],
 "finalized_baseline_route": ["claude-haiku-4-5", "low"],
 "baseline_reference_status": "verified",
 "route_changed": true, "route_status": "effective",
 "application_status": "applied",
 "token_delta": {"eligible_records": 1, "saved_tokens": 80,
                 "saved_rate": 0.8},
 "monetary_delta": {"eligible_records": 1, "verified": true,
                    "by_currency": {"USD": {
                      "saved_billed_cost": 0.08}}}}
```

This makes a route-equivalent execution eligible for both token and monetary
savings. Required repair: after resolving the immutable baseline, recompute
route identity from both observed `(model, reasoning_effort)` pairs, or make
the savings gate independently do that comparison. Caller-derived route flags
must never override immutable observed equivalence. Add a same-route
referenced-baseline negative with deliberately forged incoming flags.

## Positive controls and verification results

The following required and broad offline checks passed on the exact candidate:

- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider
  tests/test_model_routing.py tests/test_task_claim_dispatcher.py
  tests/test_doctor.py -q`: `106 passed in 27.05s`.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider`
  over the six required template routing/dispatch/bridge/worker/auto/eval
  modules: `146 passed in 1.53s`.
- `env -u ANTHROPIC_API_KEY PYTHONDONTWRITEBYTECODE=1 python -m pytest
  -p no:cacheprovider
  src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q`:
  `2 passed in 0.14s`.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -q`:
  `2979 passed, 3 skipped, 4 existing UI beta invalid-escape warnings in
  154.44s`.
- `python scripts/runtime_asset_usage.py --check`: 38 assets, 404 uses,
  0 blocks, 0 watches.
- `python scripts/template_mirror_gate.py --check`: 84 expected/common,
  81 identical, 3 intentional, 0 findings.
- `python scripts/regen_host_lock_if_needed.py --check`: host lock current.
- Root/template `cmp` for `model_routing.py` and
  `task_claim_dispatcher.py`: identical.
- `git diff --check
  da4177f6211b2a1a049ba25b62332b113a54cf97..092f3e20c7545262a17b1bc3a7a19c535fbc73c4`:
  pass.
- `python scripts/owner_governance_gate.py`: exit 0; only pre-existing
  non-blocking watches were reported.

Independent positive reproductions also confirmed that worker pre-process
claim loss writes one skipped `claim_lost` receipt without calling a provider;
single native spawn error/cancellation paths settle their reservations;
council reservation is all-or-none; all-member spawn errors can close one
receipt per member with zero verdicts; native replies without a bus parent can
record a receipt; duplicate and mismatched ledger identities fail closed; and
explicitly bound canonical zero budgets block the SDK helper before its fake
provider call.

The passing suites and positive controls validate those repaired components,
but they do not exercise the unsafe generic-session default, authority loss in
the inbox adapter, stable inbox replay identity, pre-reservation policy
failure, or same-observed-route forged-flag case above.

## Acceptance assessment

- Explicit role policy and high-tier authorization: **fail** on the generic
  parent-session surface (P1-1).
- One immutable execution receipt carrying truthful execution state: **fail**
  for inbox replay and routing-policy rejection (P1-3).
- Native model-plus-reasoning equivalence: **fail** after immutable baseline
  finalization (P1-4).
- Persistent task and claim budgets blocking before provider call: **fail**
  when the normal dispatch/inbox contract loses claim authority (P1-2).
- Savings unavailable without a trustworthy comparable baseline: the
  immutable reference requirement is improved, but **fail** because an
  equivalent referenced baseline can still be reported as changed and
  economically eligible (P1-4).

Regression-test adequacy is therefore insufficient for release despite the
green suite. Each P1 above has a bounded offline negative that the current
tests do not contain.

## Boundary and claim disposition

Only this W4b recheck evidence file was added by the independent verifier. No
implementation, task/unit record, review index, claim record, consumer
project, credential, environment setting, account, dependency, provider,
broker, database, notification, deployment, remote branch, push, tag,
version, publication, or release state was changed. No live provider or
network call was made, and no credential was read.

`CLAIM-20260730-123600-task-ar-652-ar652001` must remain unreleased. Because
the verdict is `REVISE`, the parent may close/release the claim only after a
future exact-candidate independent `APPROVE`; this verifier performs no claim
mutation or release.
