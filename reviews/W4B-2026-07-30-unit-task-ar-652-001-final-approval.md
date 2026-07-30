---
title: W4b Final Approval - TASK-AR-652 Independent Economic Routing Review
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_commit: fd06f7be04a678a5c306a1582a8086b5b9666bbd
reviewed_tree: 550bffd2914b80799be8f686aff6e2def4e54c12
implementation_commit: 94ac7332f48e20e5098044fa5801152bb836bb28
implementation_tree: cbc76a9dff7424ab981d38f7c992de5a52214958
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..fd06f7be04a678a5c306a1582a8086b5b9666bbd
focused_repair_range: dc48733bffeaccc98ce0eeb771dc7635f0843f36..94ac7332f48e20e5098044fa5801152bb836bb28
verified_by: codex-independent-task-ar-652-w4b-final-approval
verifier_task: /root/task_ar_652_w4b_final_approval
verifier_role: independent-auditor
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-recheck.md
scope_amendment: reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-scope-amendment.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-final-followup.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730155247.json
tags: [w4b, final-approval, independent-verification, model-routing, execution-receipts, savings-integrity, governance, revise]
---

# W4b Final Approval - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 2, P2: 0.`

Before this report was created, the worktree was clean and the exact
documented candidate resolved to commit
`fd06f7be04a678a5c306a1582a8086b5b9666bbd`, tree
`550bffd2914b80799be8f686aff6e2def4e54c12`. The implementation commit is
`94ac7332f48e20e5098044fa5801152bb836bb28`, tree
`cbc76a9dff7424ab981d38f7c992de5a52214958`. The complete acceptance range is
`da4177f6211b2a1a049ba25b62332b113a54cf97..fd06f7be04a678a5c306a1582a8086b5b9666bbd`;
the focused final-repair range is
`dc48733bffeaccc98ce0eeb771dc7635f0843f36..94ac7332f48e20e5098044fa5801152bb836bb28`.

This verifier is
`codex-independent-task-ar-652-w4b-final-approval`
(`/root/task_ar_652_w4b_final_approval`, role `independent-auditor`), which is
distinct from worker `le-20260730-123600-kst-ar652001`. The worker's
conclusions were not assumed: the acceptance surfaces, prior findings, fake
provider paths, exact governance candidate, and drift controls were inspected
and reproduced independently.

The final repair closes the full forged-high/raw cases and the time-only board
drift reported by the prior W4b. Two assertion-integrity gaps remain. Partial
route dictionaries can still become executable tier/provider inputs, and a
native receipt can self-assert `resolved_reasoning_source=unsupported` to make
missing observed reasoning savings-eligible.

## P1-1 - Partial route assertions still become executable authority

The new `_assert_route_matches()` correctly rejects mismatching fields that a
caller supplies. The authority derivation immediately before that check still
uses assertion data as input:

- `src/agent_runtime/templates/project/scripts/subagent_dispatch.py:497-500`
  falls back to `tier_route["requested_tier"]` when `render_prompt()` has no
  explicit requested tier.
- `src/agent_runtime/templates/project/scripts/subagent_dispatch.py:507-510`
  falls back to `provider_route["provider"]` when either final boundary has no
  explicit provider.

That means a partial dictionary can omit every field that would expose a
mismatch, seed the authoritative resolver with its asserted value, and then
compare equal to the authority it just selected.

An offline direct reproduction against both final boundaries showed:

1. The intended full negatives pass. A Scribe supplied with the Auditor's full
   high route was rejected by both `render_prompt()` and
   `emit_call_message()`. A Scribe route whose resolved model was changed to
   `vendor/raw-expensive-model` was also rejected by both.
2. `render_prompt(..., tier_route={"requested_tier":
   "reviewer_standard"})` was accepted without a trusted requested-tier
   argument. The executable Scribe prompt selected
   `reviewer_standard`, `gpt-5.6-sol`, reasoning `high`, instead of the Scribe
   default `worker_low`, `gpt-5.6-terra`, reasoning `low`.
3. `provider_route={"provider": "codex-agent"}` was accepted by both
   `render_prompt()` and `emit_call_message()` without a trusted provider
   argument. The prompt/message authority changed from native Codex to
   `codex-agent` and resolved `gpt-5.2-codex`.
4. A mixed partial tier/provider assertion was accepted by `render_prompt()`
   and selected `reviewer_standard` on `codex-agent`.
5. Explicit trigger and provider mismatches did reject. An escalated route
   without the explicit `data_integrity` authority input failed, while the
   same route with the explicit trigger passed. An asserted `codex-agent`
   provider with explicit `provider="native-codex"` failed.

This is not merely incomplete metadata checking. The accepted values are
rendered into the parent spawn contract or persisted into the executable
subagent call message. It violates the scope amendment's requirement that
supplied tier/provider dictionaries are assertions only and the task
requirement that cheap roles resolve through their explicit role policy.

Required repair: derive `requested_tier` only from a separate trusted argument
(or the role default when absent), and derive `provider` only from a separate
trusted argument (or the documented default when absent). Never use either
assertion dictionary to choose the authority against which it is checked. Add
partial and mixed assertion negatives for both prompt rendering and message
emission, including a registered alternate provider whose internally
consistent route would otherwise pass.

## P1-2 - A native receipt can forge `unsupported` reasoning authority

`_route_observation_complete()` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:1146-1157`
returns true as soon as the receipt string
`resolved_reasoning_source` equals `unsupported`. It does not establish that
the provider's authoritative route schema actually lacks reasoning, and it
does not reject the internally contradictory case where
`resolved_reasoning_effort` is populated.

The finalizer and reporting gate both consume this helper. Independent offline
reproductions demonstrated both failure modes:

- A baseline claimed provider `native-codex`, resolved model
  `gpt-5.6-sol`, resolved reasoning `high`, and
  `resolved_reasoning_source=unsupported`, while omitting observed reasoning.
  The actual receipt observed the same model at reasoning `low`, 15 tokens and
  USD 0.02 against the baseline's 100 tokens and USD 0.10. The finalizer
  accepted the baseline as `verified`, marked the actual `applied` and
  `effective`, and the report produced one token-eligible and one
  money-eligible record: 85 saved tokens and USD 0.08 saved billed cost.
- A report-level forged native actual omitted observed reasoning, asserted
  `resolved_reasoning_source=unsupported`, and supplied
  `baseline_reference_status=verified`, `application_status=applied`,
  `route_changed=true`, and `route_status=effective`. The original finalizer
  had classified this actual as `not_applied`; the report-level gate accepted
  the forged row anyway and again reported 85 saved tokens and USD 0.08.

The controls distinguish the intended exception:

- With the normal native `adapter_default:*` reasoning source, missing
  baseline reasoning produced
  `baseline_route_observation_incomplete`; missing actual reasoning produced
  `application_status=unverified`. Token and monetary eligibility were zero
  in both cases.
- A real `codex-agent` provider route resolved by `model_routing` carried
  `reasoning_effort=None` and `reasoning_source=unsupported`. Different
  observed provider-worker models remained comparable and eligible, proving
  that the legitimate unsupported-reasoning path can remain functional.

Required repair: make `unsupported` an authoritative provider-route property,
not a receipt assertion. At minimum, a record with a non-null
`resolved_reasoning_effort` must require observed reasoning regardless of its
source string. The finalizer and report must also bind the unsupported state
to a trusted provider/route schema so a native receipt cannot self-declare it.
Add baseline and actual negatives for native/resolved routes that forge the
source, at both finalization and report levels, for token and money evidence.

## Disposition of the third latest P1 - exact-candidate governance

The board/governance repair passes.

- The exact root and packaged `taskset_work_gate.py --check` commands both
  returned 0 with zero findings.
- A fresh temporary-root reproduction changed only the
  `Throughput (7d)` projection; both root and packaged gates returned 0.
- Separate task status, task addition, and active-claim addition drifts each
  returned 1 with `BACKLOG-BOARD.md: stale:content-mismatch` on both root and
  packaged gates.
- The integrated exact-candidate `owner_governance_gate.py` returned 0.
- The committed board content, root/package gate parity, template mirror, host
  lock, evidence index, and T3 assumptions all passed their gates.

This closes the prior governance P1 without masking record-derived drift.

## Regression sampling of the four prior repaired boundaries

### Ordinary CLI and legacy role policy

- The Scribe CLI with `--model opus --dry-run` returned 0 and remained
  `worker_low` / `gpt-5.6-terra`.
- A raw CLI model returned 2 during argument validation.
- Legacy `routing={"selected_tier": "opus"}` emitted
  `worker_low` / `gpt-5.6-terra`; a legacy raw model raised before emission.
- Legitimate Codex single and council dry-run packets remained
  `pending_parent_spawn`. The single Scribe route was native
  `worker_low`; a two-member Scribe/Auditor council rendered two call messages
  with the expected native role routes.

### Claim and durable budget authority

- An ordinary emitted message preserved dispatch ID, claim ID, task/claim
  budgets, workload ID, baseline receipt ID, role, task, and escalation
  triggers through `inbox_work_items()`.
- A unique canonical active claim with task budget 100 and claim budget 0
  blocked a fake provider before its call. Provider calls were zero, the error
  was `claim_budget_insufficient`, and the terminal receipt retained the
  canonical claim ID and `budget_preflight` source.
- The required template suite also reran the persistent restart, ambiguous
  claim, reservation identity, zero/invalid budget, and atomic reservation
  tests.

### Replay and policy-terminal receipts

- Replaying the same dispatch made one fake-provider call total, preserved one
  immutable receipt, and returned `duplicate_dispatch_id` on the replay.
- A raw auto-dispatch route made zero provider calls and wrote exactly one
  skipped `routing_policy` receipt.
- The required template suite reran the worker-side raw-route terminal control,
  including bounded reply and source-message closure.

### Same-observed-route forged flags

- Baseline and actual both observed `(gpt-5.6-sol, high)`.
- The actual supplied a forged expensive baseline plus
  `model_changed=true`, `route_changed=true`, `route_status=effective`, and
  `application_status=applied`.
- Finalization replaced the forged baseline, set `route_changed=false` and
  `route_status=ineffective_equivalent`, and left both token and monetary
  eligible counts at zero.

## Complete acceptance assessment

- Explicit role policy for Scribe, exploration, implementation, review, and
  audit: the normal role matrix and CLI/Codex callers pass, but partial
  assertion dictionaries can alter the executable Scribe tier/provider, so
  the end-to-end criterion **fails**.
- High-tier authorization: the full forged-high and missing-trigger controls
  reject, and legitimate explicit escalation works. This narrower criterion
  **passes**, while P1-1 still violates assertion-only authority and the cheap
  role lane.
- Immutable receipt of requested/resolved/observed routing, usage, cost, and
  source: completion and terminal paths persist the fields, and configuration
  is not treated as observation. The exercised mechanical criterion **passes**.
- Native model-plus-reasoning equivalence: ordinary missing-reasoning and exact
  same-route controls pass, but a native/resolved receipt can forge the
  unsupported source and become comparable, so the criterion **fails**.
- Persistent task/claim budgets and pre-provider blocking: canonical claim,
  zero-budget, ambiguity, restart, and replay controls **pass**.
- Savings unavailable without an observed comparable baseline: ordinary
  incomplete routes are excluded, but the native unsupported-source forgery
  creates token and monetary deltas, so the criterion **fails**.
- Exact-candidate owner governance and generated-board drift policy: **passes**.

## Verification command outcomes

- Pre-report candidate identity and cleanliness: clean
  `fd06f7be04a678a5c306a1582a8086b5b9666bbd`, tree
  `550bffd2914b80799be8f686aff6e2def4e54c12`; implementation tree
  `cbc76a9dff7424ab981d38f7c992de5a52214958`.
- Required root suite:
  `106 passed in 27.90s`.
- Required six-module template suite:
  `166 passed in 2.38s`.
- Required SDK fake-provider suite:
  `2 passed in 0.14s`.
- Taskset governance suite:
  `12 passed in 0.48s`.
- Full Runtime suite:
  `2980 passed, 3 skipped, 4 pre-existing UI beta invalid-escape warnings in
  167.02s`.
- Integrated Owner governance: exit 0. This includes successful taskset,
  evidence-index, template-mirror, runtime-asset, and all other blocking
  checks; non-blocking watch/advisory output did not change the result.
- Runtime asset usage:
  38 assets, 404 uses, 0 blocks, 0 watches.
- Template mirror:
  84 expected/common, 81 identical, 3 intentional, 0 findings.
- Managed-host lock:
  current.
- T3 plan-assumption check for
  `TASKSET-AR-V080-OPERABILITY-HARDENING`:
  pass with zero findings.
- Root/template byte parity:
  `model_routing.py`, `task_claim_dispatcher.py`, and
  `taskset_work_gate.py` are identical to their packaged mirrors.
- In-memory compilation of all 22 Python files changed across the complete
  acceptance range:
  pass.
- `git diff --check` for the complete acceptance range, focused final-repair
  range, working tree, and index:
  pass.

All execution controls used dummy, fake, or in-memory providers. Credential
variables, including the present `GEMINI_API_KEY` variable, were removed from
verification commands. No credential value was read, no live provider or
network endpoint was called, and temporary artifacts were confined to
automatically cleaned temporary directories.

## Boundary and claim disposition

Only this W4b report was added. No implementation, task/unit record, claim,
handoff, log, board, review index, plan assumption, registry, managed asset,
host lock, consumer project, credential, environment setting, dependency,
provider, account, broker, database, notification, deployment, remote branch,
tag, version, publication, or release state was changed.

`CLAIM-20260730-123600-task-ar-652-ar652001` remains `claimed` and unreleased.
This verifier did not run claim release, closeout, merge, commit, push, deploy,
or publication. The claim may advance only after both P1 findings are repaired
and a fresh independent W4b approves a new exact clean candidate.
