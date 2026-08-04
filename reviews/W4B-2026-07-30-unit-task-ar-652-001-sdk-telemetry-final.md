---
title: W4b SDK Telemetry Final - TASK-AR-652 Independent Economic Routing Review
date: 2026-07-30
created_at: 2026-07-30T18:00:38+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
prior_candidate: 2c143d3a269f21e40f62351790baf1d2cd527561
reviewed_commit: ef08f44e3cc4a31b76774db449a797e13aa6132e
reviewed_tree: a3811fc8e2c464b853a62d138085055310f0dac9
implementation_commit: 56fd7789561ebceacd89d5efb3b4ef3f51019ac0
implementation_tree: 520eec2a1c6b4906fb91bec7997db4f5ba1baa19
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..ef08f44e3cc4a31b76774db449a797e13aa6132e
focused_repair_range: 7b3cba22c02e111aaedb729e8438dd3df3ecbbac..56fd7789561ebceacd89d5efb3b4ef3f51019ac0
focused_candidate_range: 2c143d3a269f21e40f62351790baf1d2cd527561..ef08f44e3cc4a31b76774db449a797e13aa6132e
verifier_agent_instance_id: qa-20260730-w4b-ar652-sdk-final
verified_by: qa-20260730-w4b-ar652-sdk-final
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_sdk_final
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-provider-identity.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-sdk-telemetry-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-sdk-telemetry-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730173228.json
tags: [w4b, sdk-telemetry, independent-verification, execution-receipts, economic-integrity, budget-integrity, revise]
---

# W4b SDK Telemetry Final - UNIT-TASK-AR-652-001

## Independent verdict

The exact candidate is not ready for approval. The focused SDK telemetry
repair passes, but complete-range adversarial verification found two
release-blocking P1 defects in the shared receipt/economic and persistent
budget boundaries.

Immediately before this report was added, the worktree and index were clean.
The exact candidate was commit
`ef08f44e3cc4a31b76774db449a797e13aa6132e`, tree
`a3811fc8e2c464b853a62d138085055310f0dac9`. The focused implementation was
commit `56fd7789561ebceacd89d5efb3b4ef3f51019ac0`, tree
`520eec2a1c6b4906fb91bec7997db4f5ba1baa19`.

The complete range
`da4177f6211b2a1a049ba25b62332b113a54cf97..ef08f44e3cc4a31b76774db449a797e13aa6132e`,
focused SDK implementation
`7b3cba22c02e111aaedb729e8438dd3df3ecbbac..56fd7789561ebceacd89d5efb3b4ef3f51019ac0`,
and focused candidate
`2c143d3a269f21e40f62351790baf1d2cd527561..ef08f44e3cc4a31b76774db449a797e13aa6132e`
were reviewed independently.

Verifier `qa-20260730-w4b-ar652-sdk-final`, role `qa-reviewer`, is distinct
from worker `le-20260730-123600-kst-ar652001`. Worker W4a and canonical VERIFY
evidence were read but not treated as authority.

## P1-1 - Error and skipped actual receipts can count as economic savings

The economic report validates that the immutable baseline receipt completed,
but it never requires the actual receipt to represent successful completed
work:

- `_verified_baseline_receipt()` at
  `src/agent_runtime/templates/project/scripts/eval_harness.py:1484-1512`
  requires `baseline.status == "completed"`.
- `_routing_evidence_exclusion_reason()` at
  `src/agent_runtime/templates/project/scripts/eval_harness.py:1515-1554`
  checks model/reasoning/provider comparability and applied/effective route
  flags, but not the actual receipt's `status`, `error`, or failure outcome.
- Both token and monetary eligibility inherit that omission at
  `src/agent_runtime/templates/project/scripts/eval_harness.py:1557-1593`.

An independent offline reproduction used the public
`codex_subagent_bridge.record_reply()` path, an observed completed baseline of
100 tokens and USD 0.10, and an explicit matching actual route with 15 tokens
and USD 0.02. The same workload ID and an observed provider/model/reasoning
identity were used on both sides.

| Actual case | Route telemetry | Token eligible | Money eligible |
| --- | --- | ---: | ---: |
| `completed` | explicit matching | 1 | 1 |
| `error`, `error="synthetic provider failure"` | explicit matching | 1 | 1 |
| `skipped` | explicit matching | 1 | 1 |
| `completed` | missing | 0 | 0 |
| `error` | missing | 0 | 0 |
| `skipped` | missing | 0 | 0 |

The error and skipped rows were finalized as `application_status=applied`,
`route_status=effective`, and a verified baseline. Each was reported as 85
saved tokens and USD 0.08 saved billed cost. These are synthetic eligibility
outputs only; this review makes no economic-savings claim.

Failed or unexecuted work cannot establish savings merely because its route
telemetry is comparable. Require the actual immutable receipt to be
successfully completed, with no recorded error or failure outcome, before
either economic path is eligible. Add public-path, finalizer, and report
negatives for `error`, `skipped`, unknown/nonterminal status, and completed
receipts with a recorded error.

## P1-2 - Unknown terminal usage releases the persistent budget commitment

`_usage_from_records()` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:517-581` treats
the presence of any terminal execution receipt as sufficient to remove its
reservation:

- lines 529-537 remove reservations whose dispatch ID appears in any receipt;
- line 562 counts absent token telemetry as zero;
- line 581 therefore commits neither the reservation nor actual usage.

A true two-process restart reproduction used task and claim token budgets of
10:

1. Process one reserved a ceiling of 10 and was allowed.
2. It recorded a terminal `completed` receipt with
   `token_usage_status="unavailable"` and no token values.
3. Ledger accounting then showed zero pending reservations and zero committed
   tokens for both task and claim.
4. A fresh process reserved another ceiling of 10 and was allowed with
   `reason="within_budget"`.

The hard guard consequently forgets the conservative commitment whenever a
provider-called terminal receipt lacks usage telemetry. Repeating the pattern
can authorize unbounded unknown usage across restarts. The remedy must not
invent actual token usage: retain the conservative reservation, or a
documented conservative remainder, until authoritative usage is available.
A pre-provider skipped receipt may release its reservation. Add a fresh
two-process negative for completed/error provider calls with unavailable or
partial telemetry, plus a skipped-before-call release control.

## Focused SDK repair assessment

The focused repair itself passes. `verify_sdk_backend._record()` now records
the configured provider from `route["provider"]` and records observed provider
only from explicit result telemetry.

An independent SDK matrix covered completed results with absent, blank,
unknown, mismatching, and matching provider values; error and skipped paths
without a result; and soft-error paths with missing or matching telemetry:

- configured provider remained `claude-agent`;
- absent/blank observed provider normalized to null;
- unknown and mismatching identities remained explicit and ineligible;
- no-result error/skipped receipts kept observed provider null;
- only explicit `claude-agent` telemetry completed route observation;
- every standalone case had zero token and monetary eligible records.

Independent baseline/actual matrices for missing, blank, unknown, and
mismatching observed providers also remained token- and money-ineligible.
Role-tier defaults, explicit escalation triggers, partial tier/provider
assertion rejection, canonical provider aliases, and the native forged
unsupported-reasoning negative all passed.

The ordinary persistent-budget control also passed: process one committed 5
observed tokens under a budget of 10, and a fresh process correctly rejected a
ceiling of 6 with `task_budget_insufficient`. P1-2 is specifically the
unknown-usage settlement path.

## Verification results

Every Python, test, and gate command removed
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`,
`AZURE_OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`AWS_SESSION_TOKEN` from its environment. Bytecode and pytest cache writes
were disabled.

Required suites:

- root routing/dispatcher/doctor suite: `108 passed in 26.56s`;
- required six-module template suite: `193 passed in 2.03s`;
- SDK fake-provider suite: `3 passed in 0.15s`;
- taskset governance suite: `12 passed in 0.47s`;
- managed-host lock suite: `23 passed in 1.32s`.

The full Runtime suite did not reproduce the W4a all-green count:
`1 failed, 2981 passed, 3 skipped, 4 warnings in 154.59s`.
The failure was
`tests/test_ui_console_e2e.py::test_decision_first_home_fits_two_screens_in_browser[desktop-viewport0]`,
where browser evaluation raised
`TypeError: Cannot read properties of null (reading 'built_at')` in
`stateFreshness()`. An immediate exact-node rerun failed identically in
3.70 seconds.

This UI discrepancy is not counted as a TASK-AR-652 telemetry finding. Neither
the failing test nor its served UI asset changed in the acceptance range:
their base and candidate blob IDs are respectively
`93f6e22dd5873cce6d0017faac775a9c8640242a` and
`6e8682b0e3d345df1c48d38f3a8d02b75c1321f6`. It is documented because the
exact candidate's full suite was not green and appears to expose an unrelated
pre-existing browser-load race.

Repository checks passed:

- Runtime asset usage: 38 assets, 404 uses, 0 blocks, 0 watches.
- Template mirror: 84 expected/common, 81 identical, 3 intentional,
  0 findings.
- Managed-host lock, evidence index, root and packaged taskset gates, T3
  plan-assumption gate, and integrated Owner governance: pass.
- Root/template parity for `model_routing.py`,
  `task_claim_dispatcher.py`, and `taskset_work_gate.py`: byte-identical.
- In-memory compilation of all 22 Python files changed across the complete
  acceptance range: pass.
- `git diff --check` for the complete range, focused candidate/implementation
  boundaries, working tree, and index: pass.

All execution controls used fake, dummy, or in-memory providers. No credential
value or `.env` file was read, no live provider or network endpoint was
called, and no dependency was installed.

## Boundary and claim disposition

Only this W4b report was added. No implementation, task/unit record, claim,
handoff, log, board, review index, plan assumption, registry, managed asset,
host lock, consumer primary, credential, environment setting, dependency,
provider, account, broker, database, notification, deployment, remote branch,
tag, version, publication, or release state was changed.

`CLAIM-20260730-123600-task-ar-652-ar652001` remains `claimed` and unreleased.
This verifier did not run claim release, closeout, merge, commit, push, deploy,
or publication. The claim may advance only after both P1 findings are repaired
and a fresh independent W4b approves a new exact clean candidate.

## Final verdict

REVISE — P0: 0, P1: 2, P2: 0
