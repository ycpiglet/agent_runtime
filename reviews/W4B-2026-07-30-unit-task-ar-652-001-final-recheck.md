---
title: W4b Final Recheck - TASK-AR-652 Independent Economic Routing Review
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 3, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_commit: dc48733bffeaccc98ce0eeb771dc7635f0843f36
reviewed_tree: 66e238008709d0f99d8fb9d6117e3d512ab2288c
implementation_commit: 8be79762a8caef498010e690ff939d8f8a1a99fe
implementation_tree: dfd833721015a6e5a2bf7aacc333cdca25d5353f
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..dc48733bffeaccc98ce0eeb771dc7635f0843f36
focused_repair_range: afbf77246906746b0ad3f7dac545e64d6a63acde..8be79762a8caef498010e690ff939d8f8a1a99fe
verified_by: codex-independent-task-ar-652-w4b-final-recheck
verifier_task: /root/task_ar_652_w4b_final_recheck
verifier_role: independent-auditor
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-recheck.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-recheck-followup.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730150652.json
tags: [w4b, final-recheck, independent-verification, model-routing, execution-receipts, persistent-budget, savings-integrity, revise]
---

# W4b Final Recheck - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 3, P2: 0.`

Before this report was created, the worktree was clean and the exact reviewed
candidate resolved to commit
`dc48733bffeaccc98ce0eeb771dc7635f0843f36`, tree
`66e238008709d0f99d8fb9d6117e3d512ab2288c`. The implementation commit is
`8be79762a8caef498010e690ff939d8f8a1a99fe`, tree
`dfd833721015a6e5a2bf7aacc333cdca25d5353f`. The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..dc48733bffeaccc98ce0eeb771dc7635f0843f36`;
the focused second-repair range is
`afbf77246906746b0ad3f7dac545e64d6a63acde..8be79762a8caef498010e690ff939d8f8a1a99fe`.

The repair materially closes the ordinary CLI, legacy-routing, inbox
authority, replay, policy-terminal, and same-observed-route cases named in the
prior W4b. Independent offline controls reproduced each of those positives.
It does not close the complete authority and economic-evidence boundaries:
pre-resolved route dictionaries remain executable authority, a native baseline
with no observed reasoning is accepted as comparable economic evidence, and
the exact candidate fails its integrated Owner governance gate.

## P1-1 - Pre-resolved dictionaries can still bypass the Scribe role policy

`subagent_dispatch.render_prompt()` says every executable prompt is role-bound,
but at `src/agent_runtime/templates/project/scripts/subagent_dispatch.py:428`
through `:442` it accepts `tier_route` and `provider_route` wholesale and calls
the role/provider resolvers only when those dictionaries are absent.
`emit_call_message()` repeats the same trust decision at `:534` through `:555`.
There is no consistency check tying the supplied tier to `role_id`, a
registered escalation trigger, or the provider mapping.

This matters because `render_prompt()` is the documented contract that tells
the parent session which model and reasoning to spawn. An offline direct
reproduction supplied a Scribe with no trigger and caller-created route
dictionaries. The executable prompt contained:

```json
{
  "role": "scribe",
  "selected_pm_tier": "planner_high",
  "resolved_request_model": "gpt-5.6-sol",
  "reasoning_effort": "high"
}
```

The message-emission reproduction persisted the same authority:

```json
{
  "to": "subagent-scribe",
  "requested_model_tier": "planner_high",
  "selected_model_tier": "planner_high",
  "resolved_model": "gpt-5.6-sol",
  "reasoning_effort": "high",
  "role_policy_id": "forged",
  "high_tier_authorized": "true",
  "registered_escalation_reason": "none"
}
```

The ordinary CLI control is safe: a no-provider Scribe `--model opus` resolves
to `worker_low` / `gpt-5.6-terra`, a raw model exits 2 in argument parsing, and
legacy `routing=` input is re-resolved and bounded. Those controls do not make
the parallel `tier_route=` / `provider_route=` authority safe.

Required repair: derive the executable tier from `role_id`, requested tier,
and registered triggers at the final prompt/message boundary. Treat supplied
route dictionaries as assertions only, reject any mismatch with the
independently resolved route, and add direct forged-high and forged-raw
dictionary negatives for both prompt rendering and message emission.

## P1-2 - Missing observed baseline reasoning is reported as verified savings

The immutable baseline validator at
`src/agent_runtime/templates/project/scripts/eval_harness.py:1220` through
`:1227` requires completed status, an observed model, and observed tokens, but
does not require observed reasoning when the native resolved route includes
reasoning. The finalizer then creates a baseline identity containing
`reasoning_effort=None` at `:1253` through `:1256` and compares it as though it
were complete. The reporting validator repeats the omission at `:1467` through
`:1474`.

An offline ledger reproduction recorded:

- baseline: native Codex, observed model `gpt-5.6-sol`, 100 observed tokens,
  USD 0.10 billed cost, but no observed reasoning effort;
- actual: the same observed model, observed/resolved reasoning `low`, 15
  observed tokens, and USD 0.02 billed cost;
- same immutable workload and a real baseline receipt reference.

The candidate produced:

```json
{
  "baseline_reference_status": "verified",
  "baseline_reasoning_effort": null,
  "application_status": "applied",
  "route_changed": true,
  "route_status": "effective",
  "token_eligible_records": 1,
  "saved_tokens": 85,
  "monetary_eligible_records": 1,
  "saved_billed_cost_usd": 0.08
}
```

This is not a comparable observed native route. Absence of baseline reasoning
cannot prove that `(gpt-5.6-sol, low)` differs from the baseline; the baseline
could have used the same reasoning. It violates the acceptance requirement
that native equivalence compare model plus reasoning and that savings remain
unavailable without an observed comparable baseline.

Required repair: when reasoning is part of the resolved/native route identity,
require observed reasoning on both baseline and actual receipts. An incomplete
identity must remain `unverified` and be excluded from token and monetary
deltas. Preserve `None` only for a provider whose authoritative route schema
explicitly declares reasoning unsupported. Add finalizer and report-level
negatives for a referenced baseline with missing observed reasoning.

## P1-3 - The exact candidate fails integrated Owner governance

The W4a states that integrated Owner governance passed, but an independent
execution on the exact clean candidate returned exit 1:

```text
owner-governance: result: scripts/taskset_work_gate.py --check -> 1
```

The isolated failing gate reports exactly one finding:

```text
taskset-work-gate: fail
findings=1
- BACKLOG-BOARD.md: stale:content-mismatch:
  run python scripts/backlog_board.py --write
```

A read-only render diff showed dynamic generated time, active WIP age, weekly
throughput, and trailing-newline differences. This verifier did not regenerate
`BACKLOG-BOARD.md`: it is orchestrator-owned shared SSoT and the task expressly
forbids that write. Regardless of whether the drift is attributed to the W4a
recording commit or time-sensitive board generation, the exact candidate does
not have the green governance evidence claimed by W4a and cannot pass W4b.

Required repair: the serial projection owner must restore a stable,
current generated board and make the freshness check deterministic across the
W4a-to-W4b interval, then attach a fresh exact-candidate governance result.

## Independent reproduction of the four prior P1 boundaries

### 1. Generic no-provider and legacy Scribe routing

- `subagent_dispatch.py --role scribe ... --model opus --dry-run` returned 0
  and rendered `selected_pm_tier=worker_low`,
  `resolved_request_model=gpt-5.6-terra`.
- A raw `--model vendor/raw-expensive-model` exited 2 before dispatch.
- `emit_call_message(..., routing={"selected_tier": "opus"})` persisted
  `worker_low` / `gpt-5.6-terra`.
- Legacy raw routing raised `ValueError` before emission.
- The separate pre-resolved dictionary authority remains unsafe as P1-1.

### 2. Ordinary message authority, canonical claim, and zero budget

- An ordinary emitted call preserved `dispatch_id`, `claim_id`, task and claim
  budgets, workload ID, baseline receipt ID, and escalation triggers through
  `inbox_work_items()`; `subagent-scribe` normalized to `scribe`.
- With no claim ID in the ordinary message, the one active canonical claim was
  automatically bound.
- Canonical task budget 100 plus claim budget 0 blocked before the fake
  provider with `claim_budget_insufficient`; provider calls were 0 and the
  terminal receipt carried the canonical claim ID.
- Adding a second active claim for the task failed closed as
  `receipt_ledger_untrusted`, with the underlying error naming multiple active
  claim authorities; provider calls remained 0.
- A two-process restart proof recorded 5 tokens in process one. Process two
  attempted a ceiling of 6 against task/claim budgets of 10 and returned
  `task_budget_insufficient`, with both durable committed totals equal to 5.

### 3. Stable inbox replay and routing-policy terminals

- Re-reading the same still-open inbox message produced the same message-backed
  dispatch ID. Two runs made exactly one fake-provider call and left exactly
  one receipt; the replay returned `duplicate_dispatch_id`.
- Auto-dispatch raw routing made zero provider calls and wrote one skipped
  `routing_policy` receipt.
- Worker raw routing made zero provider calls, wrote one skipped
  `routing_policy` receipt and one bounded reply, and changed the claimed
  source message to `answered`.

### 4. Same-observed-route forged savings flags

- An immutable baseline and actual receipt both observed
  `(gpt-5.6-sol, high)`.
- The actual call supplied forged expensive baseline fields plus
  `model_changed=true`, `route_changed=true`, `route_status=effective`, and
  `application_status=applied`.
- Finalization replaced the forged fields, set `route_changed=false` and
  `route_status=ineffective_equivalent`, and both token and monetary eligible
  record counts remained 0.
- The incomplete-reasoning variant remains unsafe as P1-2.

## Complete acceptance assessment

- Explicit role policies for Scribe, exploration, implementation, review, and
  audit: the canonical resolver matrix is explicit and its normal callers
  choose the expected tiers, but the executable dictionary bypass makes the
  end-to-end criterion **fail**.
- High-tier authorization: the CLI and legacy-input negatives pass, but
  supplied route dictionaries can assert high authorization with no registered
  reason, so the criterion **fails**.
- Requested/resolved/observed routing, usage, cost, and source in one immutable
  receipt: positive completion and skip paths are present; configured intent
  alone leaves observations and usage unavailable. This mechanical criterion
  **passes** for the exercised runtime surfaces.
- Native model-plus-reasoning equivalence: exact observed same-route
  recomputation passes, but an incomplete baseline reasoning identity is
  treated as a verified change, so the criterion **fails**.
- Persistent task/claim budgets and pre-provider blocking: unique binding,
  ambiguity, zero-budget, reservation identity, and process-restart controls
  **pass**.
- Savings unavailable without an observed comparable baseline: immutable
  reference and workload checks pass, but missing baseline reasoning still
  contributes to token and monetary savings, so the criterion **fails**.
- Exact-candidate governance: **fails** on stale `BACKLOG-BOARD.md`.

## Verification command outcomes

- Candidate identity and cleanliness before report:
  `dc48733bffeaccc98ce0eeb771dc7635f0843f36`,
  tree `66e238008709d0f99d8fb9d6117e3d512ab2288c`, empty
  `git status --short --untracked-files=all`.
- Required root suite, with bytecode/cache disabled and live credential
  variables removed: `106 passed in 27.25s`.
- Required six-module template suite under the same offline controls:
  `160 passed in 2.16s`.
- SDK helper suite using its fake providers only: `2 passed in 0.15s`.
- Full Runtime suite: `2979 passed, 3 skipped, 4 pre-existing UI beta
  invalid-escape warnings in 156.57s`.
- `python scripts/runtime_asset_usage.py --check`: pass; 38 assets, 404 uses,
  0 blocks, 0 watches.
- `python scripts/template_mirror_gate.py --check`: 84 expected/common, 81
  identical, 3 intentional, 0 findings.
- `python scripts/regen_host_lock_if_needed.py --check`: current.
- Root/template byte comparison for `model_routing.py` and
  `task_claim_dispatcher.py`: identical.
- In-memory compilation of all 10 changed executable Python modules: pass.
- `git diff --check` for both the complete acceptance range and focused repair
  range, plus working-tree and index checks: pass.
- `python scripts/owner_governance_gate.py`: exit 1 solely because
  `scripts/taskset_work_gate.py --check` returned the stale-board finding
  described in P1-3.

No live provider or network call was made. All execution controls used dummy
or in-memory fake providers. Credential variables were removed from test
commands; no credential or provider account was read or used. Temporary files
were confined to automatically cleaned system temporary directories.

## Boundary and claim disposition

Only this W4b final-recheck report was added. No implementation, task/unit
record, claim, handoff, log, board, index, registry, consumer project,
credential, environment setting, dependency, provider, account, broker,
database, notification, deployment, remote branch, push, tag, version,
publication, or release state was changed.

`CLAIM-20260730-123600-task-ar-652-ar652001` remains `claimed` and unreleased.
This verifier did not run release, closeout, merge, commit, or push. The claim
may advance only after the P1 findings are repaired and a fresh independent
W4b approves a new exact clean candidate.
