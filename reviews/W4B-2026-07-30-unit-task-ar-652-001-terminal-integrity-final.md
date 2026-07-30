---
title: W4b Terminal Integrity Final - TASK-AR-652 Independent Economic and Budget Review
date: 2026-07-30
created_at: 2026-07-30T18:38:20+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: ef08f44e3cc4a31b76774db449a797e13aa6132e
reviewed_commit: fcc0af91040a80b4528592a8a4a0cf0b6e3d6d24
reviewed_tree: e7d0df8f4c4b31286236e56a0df1cb777451bf06
implementation_commit: 8e34fcc0dc8290b95c1310f65151637c35cf4055
implementation_tree: 3deed20cbfc1ea4bdfc4b8fa47ffbfb61fb0ec07
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..fcc0af91040a80b4528592a8a4a0cf0b6e3d6d24
focused_repair_range: 3527e0df65c2764bd115804fb3a0de353582769f..8e34fcc0dc8290b95c1310f65151637c35cf4055
focused_candidate_range: ef08f44e3cc4a31b76774db449a797e13aa6132e..fcc0af91040a80b4528592a8a4a0cf0b6e3d6d24
verifier_agent_instance_id: qa-20260730-w4b-ar652-terminal-integrity-final
verified_by: qa-20260730-w4b-ar652-terminal-integrity-final
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_terminal_final
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-sdk-telemetry-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-terminal-economic-budget-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-terminal-economic-budget-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730182347.json
tags: [w4b, terminal-integrity, economic-integrity, budget-integrity, independent-verification, revise]
---

# W4b Terminal Integrity Final - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 2, P2: 0`

The exact candidate is not ready for approval. The repair closes the previously
reported error/skipped/unknown-usage examples, but adversarial verification
found two fail-open variants at the same release boundaries:

1. non-successful and nonterminal provider finish states omitted from the
   failure denylist still qualify as successful economic evidence; and
2. a caller-controlled receipt `source` string can release a real reservation
   as a pre-provider skip without proving that no provider call occurred.

Immediately before this report was written, the worktree and index were clean.
`HEAD` was
`fcc0af91040a80b4528592a8a4a0cf0b6e3d6d24`, tree
`e7d0df8f4c4b31286236e56a0df1cb777451bf06`.
The focused implementation was
`8e34fcc0dc8290b95c1310f65151637c35cf4055`, tree
`3deed20cbfc1ea4bdfc4b8fa47ffbfb61fb0ec07`.

The complete acceptance range
`da4177f6211b2a1a049ba25b62332b113a54cf97..fcc0af91040a80b4528592a8a4a0cf0b6e3d6d24`,
focused repair range
`3527e0df65c2764bd115804fb3a0de353582769f..8e34fcc0dc8290b95c1310f65151637c35cf4055`,
and prior-to-current candidate range
`ef08f44e3cc4a31b76774db449a797e13aa6132e..fcc0af91040a80b4528592a8a4a0cf0b6e3d6d24`
were reviewed independently.

Verifier `qa-20260730-w4b-ar652-terminal-integrity-final`, role
`qa-reviewer`, is distinct from worker
`le-20260730-123600-kst-ar652001`. Worker W4a and canonical VERIFY evidence
were read but not treated as authority.

## P1-1 - The success predicate accepts incomplete and nonterminal finish states

`_execution_succeeded()` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:296-307`
requires receipt status `completed`, no error, and outcome `ok`, then accepts
every finish reason not present in `FAILED_EXECUTION_FINISH`.
The denylist at lines 39-52 rejects `error`, `max_tokens`, `failed`,
`cancelled`, `timeout`, and related values, but does not reject
`incomplete`, `in_progress`, `queued`, or `requires_action`.

Those values are not hypothetical metadata outside the execution boundary.
The shipped Codex provider copies the response `status` directly into
`ProviderResult.finish_reason` at
`src/agent_runtime/templates/project/scripts/providers/codex.py:225-234`.
The public native bridge also accepts an independently supplied
`finish_reason` while its receipt status defaults to `completed` at
`src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py:672-715`.

### Independent public-path reproduction

An offline `codex_subagent_bridge.create_dispatch_packet()` /
`record_reply()` matrix used:

- one successful, observed 100-token/USD 0.10 baseline;
- one explicitly observed 15-token/USD 0.02 actual;
- matching registered provider telemetry;
- the packet's resolved model and reasoning;
- actual receipt status `completed`, no error, and each finish reason below.

| Actual finish reason | Finalized application | Finalized route | Token eligible | Money eligible |
| --- | --- | --- | ---: | ---: |
| `incomplete` | `applied` | `effective` | 1 | 1 |
| `in_progress` | `applied` | `effective` | 1 | 1 |
| `queued` | `applied` | `effective` | 1 | 1 |
| `requires_action` | `applied` | `effective` | 1 | 1 |

The report-time predicate made the same decision, so forged/stale route flags
were not needed for this reproduction. A separate baseline reproduction
recorded a `completed` baseline with `finish_reason=incomplete`; the finalizer
set `baseline_reference_status=verified`, and the comparison again produced
one token-eligible and one money-eligible row.

These are synthetic eligibility outputs only. They are not a token or monetary
savings claim.

The common former cases do fail closed: actual `error`, `skipped`,
nonterminal receipt status, completed-with-error, rejected outcome, and
`max_tokens` finish all produced zero token and monetary eligibility even
after `applied/effective/route_changed` was forged in memory. Failed baselines
were also rejected. The remaining defect is the denylist's incomplete
canonicalization of provider finish states.

### Required repair

- Normalize provider/native completion into one canonical successful execution
  state at the adapter boundary, or fail closed for unrecognized and
  non-success finish reasons when economic evidence is evaluated.
- Reject at least known incomplete/nonterminal values such as `incomplete`,
  `in_progress`, `queued`, and `requires_action` for both baseline and actual
  receipts.
- Add public bridge, finalizer, and report tests for those actual and baseline
  cases. Keep a fully observed successful control.

## P1-2 - Source-only pre-provider classification can erase a reservation

`PRE_PROVIDER_SKIP_SOURCES` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:53-60`
contains `routing_policy`, `budget_preflight`, both deterministic-preflight
sources, `session_budget_preflight`, and `claim_preflight`.
`_verified_pre_provider_skip()` at lines 346-374 checks only the receipt's
status, finish reason, source string, and absence of result/usage/cost fields.
It does not bind the source to the matching reservation's source, call phase,
preflight decision, or other authoritative no-call evidence.

`_budget_settlement_basis()` consequently returns `pre_provider_skip` at
lines 377-387. `_usage_from_records()` then discards the reservation at
lines 683-702, committing neither its ceiling nor usage.

Several whitelisted sources are structurally inconsistent with a matching
reservation in the shipped call paths:

- routing-policy and deterministic preflight run before reservation;
- a denied persistent budget preflight does not commit a reservation;
- only later no-call gates such as the auto-dispatch session-budget or
  post-reservation claim checks can legitimately settle an existing
  reservation as a no-call skip.

The settlement function does not distinguish those cases.

### Independent true restart reproduction

For each case, process one created canonical task and claim budgets of 10,
reserved the full 10 for `dispatch-one`, and appended a skipped, no-result,
unavailable-usage receipt. A genuinely fresh process then read the ledger and
attempted another ceiling-10 dispatch.

| Receipt source paired with an existing reservation | Settlement basis | Task committed | Claim committed | Fresh ceiling 10 |
| --- | --- | ---: | ---: | --- |
| `routing_policy` | `pre_provider_skip` | 0 | 0 | allowed |
| `budget_preflight` | `pre_provider_skip` | 0 | 0 | allowed |
| `deterministic_preflight_blocked` | `pre_provider_skip` | 0 | 0 | allowed |
| `deterministic_preflight_complete` | `pre_provider_skip` | 0 | 0 | allowed |
| `native_codex_reply` control | `conservative_ceiling` | 10 | 10 | blocked |

The first four source/reservation pairs cannot arise in the intended ordering,
yet the public receipt API accepts them and durable accounting forgets the
entire commitment. Repetition can therefore authorize unbounded unknown usage
across restarts.

The main conservative accounting repair otherwise works:

- completed/error/post-dispatch-skipped unknown usage retains the full ceiling;
- error and post-dispatch-skipped partial usage records four tokens plus a
  six-token conservative gap for both task and claim;
- authoritative observed zero settles to zero;
- `tokens` remains recorded usage and is never populated from a reservation;
- the stored `budget_settlement_basis` is recomputed during cumulative usage,
  so merely forging that stored field does not bypass accounting.

### Required repair

- Do not treat a receipt source string alone as proof that no provider call
  occurred.
- Bind release to a valid reservation-source/receipt-source phase transition
  and authoritative no-call evidence, or use a dedicated no-call settlement
  operation emitted only by the pre-provider branch.
- At minimum, a matching reservation must make pre-reservation-only sources
  (`routing_policy`, `budget_preflight`, and deterministic preflight) invalid
  for release.
- Add fresh-process task and claim negatives for impossible source/reservation
  pairs and forged `budget_settlement_basis`, alongside legitimate
  post-reservation no-call controls.

## Other acceptance checks

Provider identity and SDK telemetry remained fail closed:

- configured and observed provider identities must both be registered and
  match;
- native Codex aliases normalize together, `codex`/`codex-agent` normalize
  together, and bare/unknown providers remain unverified;
- the SDK helper preserves missing result provider telemetry as null and only
  an explicit matching result provider completes the observation.

Role-tier routing remained explicit:

- Scribe, research, and bounded implementation select `worker_low`;
- review selects `reviewer_standard`;
- audit and planning have registered high-tier role-policy reasons;
- a low/standard role's high request is denied without a registered trigger
  and is allowed with a trigger such as `security`.

Token and billed-cost evidence remained authoritative. Independent forged
record matrices rejected missing token components, mismatched component sums,
unavailable token status, unavailable billed-cost status, non-finite cost,
and incomplete baseline token telemetry. The fully observed success control
remained eligible.

## Verification commands and results

Every Python, test, and gate command ran with
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`,
`AZURE_OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`AWS_SESSION_TOKEN` removed. Bytecode and pytest cache writes were disabled.
No repository or template `.env` file existed.

Required and regression suites:

- root routing/claim/doctor suite: `108 passed in 27.86s`;
- combined six-module template suite, SDK suite, taskset suite, and managed
  host lock suite: `256 passed in 4.64s` (`218 + 3 + 12 + 23`);
- full Runtime suite: `2982 passed, 3 skipped, 4 warnings in 156.94s`;
- the four warnings were the pre-existing UI beta invalid-escape warnings.

Independent adversarial checks:

- public bridge terminal-finish matrix: four omitted non-success finish values
  each finalized `applied/effective` and produced token/money eligibility;
- baseline incomplete-finish control: baseline verified and both economic
  paths eligible;
- former status/error/outcome/max-token matrix: all negatives rejected and
  successful control eligible;
- token-component and billed-cost observation matrix: all forged/incomplete
  negatives rejected;
- true fresh-process settlement matrix: ordinary unknown/partial usage
  conservative, observed zero authoritative, but four impossible whitelisted
  source/reservation pairs released both budgets;
- role-tier, escalation-trigger, and canonical provider identity matrix:
  expected policy decisions.

Repository gates and static checks:

- Runtime assets: 38 assets, 404 uses, 0 blocks, 0 watches;
- template mirror: 84 common, 81 identical, 3 intentional, 0 findings;
- managed-host lock: current;
- evidence index: 0 findings;
- root and packaged taskset gates: 0 findings;
- T3 plan-assumption gate: 0 findings;
- integrated Owner governance: exit 0 with only non-blocking watches and
  advisories;
- root/template SHA-256 parity for `model_routing.py`,
  `task_claim_dispatcher.py`, and `taskset_work_gate.py`: exact;
- in-memory compilation of all 22 Python files changed in the acceptance
  range: pass;
- `git diff --check` for the complete range, focused repair, focused candidate,
  worktree, and index: pass.

All execution controls used fake, synthetic, dummy, or in-memory data. No live
provider or network endpoint was called, no credential value was read, and no
dependency was installed.

## Boundary and claim disposition

Only this W4b report was added. No implementation, test, unit/task/claim,
plan, index, lock, consumer primary, credential, provider account, package,
broker, order, database migration, notification, deployment, remote branch,
tag, version, publication, or release state was changed.

`CLAIM-20260730-123600-task-ar-652-ar652001` remains `claimed` and unreleased.
This verifier did not run claim release, closeout, merge, commit, push,
deployment, or publication. A repaired exact clean candidate requires another
fresh independent W4b before release.

## Final verdict

REVISE — P0: 0, P1: 2, P2: 0
