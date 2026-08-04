---
title: W4b Call Provenance Final - TASK-AR-652 Economic Evidence Review
date: 2026-07-30
created_at: 2026-07-30T20:21:05+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 1}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_commit: 88caa8b7ed65aac53a03550169e824e273a6624d
reviewed_tree: 38ad449604461672aa3e319306a88080b3eb85f5
implementation_commit: 873252354028adb175f1d175173425692fdbb080
implementation_tree: 8997c5b00214c0c27ce1fc4a24fb19ef87261244
replan_commit: 376cf7f1b8d4730c6849d598d20ddbd525940f78
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..88caa8b7ed65aac53a03550169e824e273a6624d
focused_repair_range: 376cf7f1b8d4730c6849d598d20ddbd525940f78..873252354028adb175f1d175173425692fdbb080
focused_candidate_range: 873252354028adb175f1d175173425692fdbb080..88caa8b7ed65aac53a03550169e824e273a6624d
verifier_agent_instance_id: qa-20260730-w4b-ar652-call-provenance-final
verified_by: qa-20260730-w4b-ar652-call-provenance-final
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_call_provenance_final
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-provenance-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-provider-call-provenance-empty-finish-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-provider-call-provenance-empty-finish-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730200353.json
tags: [w4b, call-provenance, economic-evidence, budget-integrity, independent-verification, revise]
---

# W4b Call Provenance Final - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 1, P2: 1`

The exact candidate is not ready for claim release. The focused repair closes
the two findings from the prior W4b at their direct recording and persistent
budget-settlement boundaries:

- explicit empty and omitted finish values are no longer promoted to a
  successful `stop`;
- missing, generic, or skipped observed usage cannot release a reserved
  ceiling without a matching provider-call-start marker;
- valid matching completion and provider-error markers settle authoritative
  usage;
- marker-only crashes stay reserved; and
- marker/no-provider conflicts, replay mismatches, orphan markers, tampering,
  provider/surface/source mismatches, and council authorization denials fail
  closed.

Independent adversarial review nevertheless found that the new provider-call
provenance is not applied to the token and monetary savings report. A reserved
baseline and reserved actual receipt can both lack a call-start marker, be
classified as `conservative_ceiling` for budget purposes, and still become
eligible economic evidence. The same caller-supplied observations are
therefore correctly distrusted by persistent accounting but trusted by the
economic report.

The complete acceptance range also contains one whitespace defect, so the
worker W4a statement that `git diff --check` passed is not true for the
complete range.

Immediately before this report was created, both worktree and index were
clean. `HEAD` was
`88caa8b7ed65aac53a03550169e824e273a6624d`, tree
`38ad449604461672aa3e319306a88080b3eb85f5`. The focused implementation was
`873252354028adb175f1d175173425692fdbb080`, tree
`8997c5b00214c0c27ce1fc4a24fb19ef87261244`.

The full acceptance range
`da4177f6211b2a1a049ba25b62332b113a54cf97..88caa8b7ed65aac53a03550169e824e273a6624d`,
focused repair range
`376cf7f1b8d4730c6849d598d20ddbd525940f78..873252354028adb175f1d175173425692fdbb080`,
and implementation-to-candidate metadata range
`873252354028adb175f1d175173425692fdbb080..88caa8b7ed65aac53a03550169e824e273a6624d`
were reviewed independently.

Verifier `qa-20260730-w4b-ar652-call-provenance-final`, role `qa-reviewer`, is
distinct from implementation worker `le-20260730-123600-kst-ar652001`.
Worker W4a and the canonical VERIFY record were read as supporting evidence,
not treated as independent verification authority.

## P1 - Reserved receipts without call provenance remain eligible savings evidence

The new durable marker is enforced inside persistent budget settlement:

- `_verified_provider_observed_usage()` in
  `src/agent_runtime/templates/project/scripts/eval_harness.py:613-671`
  validates the reservation, marker, authority fingerprint, provider,
  execution surface, status, and source transition;
- `_budget_settlement_basis()` at lines 749-766 admits `observed_usage` only
  through that helper; and
- `_usage_from_records()` at lines 1007-1183 re-reads markers and retains the
  reservation ceiling when the helper fails.

The economic-report path does not use the same provenance:

- `_verified_baseline_receipt()` at lines 2402-2431 checks
  `_has_authoritative_token_usage()` but does not require a matching marker or
  an `observed_usage` settlement;
- `_routing_evidence_exclusion_reason()` at lines 2434-2475 accepts a
  successful actual receipt without call provenance;
- `_token_delta_exclusion_reason()` at lines 2478-2492 checks token fields
  only;
- `_monetary_delta_exclusion_reason()` at lines 2495-2513 checks billed-cost
  fields only; and
- `read_outcomes()` at lines 2364-2377 deliberately filters the call-start
  marker before `report()` receives the rows.

Consequently, the report cannot distinguish a provider-return observation
from an otherwise well-formed caller assertion for a reserved dispatch.

### Independent true-restart reproduction

An offline synthetic ledger used explicit task budget 1,000 and two
reservation ceilings of 200:

1. reserve a native Codex baseline dispatch;
2. record a completed, successful baseline with 100 tokens and USD 0.10, but
   do not authorize or record a provider-call-start marker;
3. reserve a native Codex actual dispatch;
4. record a completed, successful actual with 15 tokens and USD 0.02, a
   different applied model/reasoning route, and the baseline receipt ID, but
   again omit the marker; and
5. launch a fresh Python process that re-reads the durable ledger, runs
   `report()`, and inspects cumulative usage.

All observations, providers, models, reasoning efforts, token components,
billed costs, currency, success status, and finish values were synthetic.
No provider was called.

| Field | Baseline | Actual |
| --- | --- | --- |
| call-start marker ID | null | null |
| budget settlement basis | `conservative_ceiling` | `conservative_ceiling` |
| successful finish | `stop` | `stop` |
| observed tokens | 100 | 15 |
| observed billed cost | USD 0.10 | USD 0.02 |
| baseline reference | n/a | `verified` |
| application / route | n/a | `applied` / `effective` |

Fresh-process output:

```json
{
  "bases": ["conservative_ceiling", "conservative_ceiling"],
  "committed": 400,
  "markers": [null, null],
  "money_eligible": 1,
  "token_eligible": 1
}
```

Persistent accounting is conservative: it commits both 200-token ceilings,
for a total of 400. The economic report is fail-open: it emits one eligible
token comparison and one eligible monetary comparison from the exact two
unproven receipts.

This contradicts the accepted replan invariants that caller-supplied token
components alone do not prove a provider call and that missing call
provenance must not become claimed actual usage. It also permits a false
savings claim even though no provider call occurred.

### Required repair

- Apply validated provider-call provenance to economic eligibility for both
  actual and baseline reserved receipts, not only to cumulative budget
  settlement.
- Require the same reservation, authority, provider, execution-surface,
  provider-result status, and source-transition agreement before token or
  billed-cost observations from a reserved dispatch may enter a savings
  comparison.
- Do not trust the stored `budget_settlement_basis` or
  `budget_provider_call_start_id` fields alone. The report must receive or
  recompute against the validated ledger marker, or ledger validation must
  bind those derived fields strongly enough that report-time use cannot be
  forged.
- Define and test the compatibility rule for truly unreserved legacy
  receipts explicitly. New shipped execution surfaces already reserve before
  a call and should fail closed when their provenance is absent.
- Add public-ledger and native-bridge actual/baseline tests for missing,
  orphaned, mismatched, skipped, wrong-provider, wrong-surface, and
  wrong-transition markers. Re-read each negative in a fresh process and
  assert zero token and monetary eligible records.
- Retain positive controls where both actual and baseline have valid matching
  markers and authoritative provider observations.

## P2 - Complete-range whitespace check contradicts W4a evidence

The focused implementation and candidate metadata ranges pass
`git diff --check`, as do the clean worktree and index. The complete
acceptance range does not:

```text
$ git diff --check da4177f6211b2a1a049ba25b62332b113a54cf97..88caa8b7ed65aac53a03550169e824e273a6624d
reviews/W4B-2026-07-30-unit-task-ar-652-001-provenance-final.md:339: new blank line at EOF.
```

The whitespace was introduced when replan commit
`376cf7f1b8d4730c6849d598d20ddbd525940f78` added the prior W4b report.
This is not a runtime correctness failure, but it makes the current W4a claim
that `git diff --check` passed incomplete for the declared acceptance range.
Remove the extra blank line and record the exact ranges checked in the next
W4a.

## Verified closure of the prior two findings

### Exact finish preservation

- `record_execution_receipt()` stores an omitted finish as null and preserves
  explicit empty as `""`.
- Worker, auto-dispatch, SDK verification, native bridge, and council
  wrappers preserve an explicit empty value.
- Claude CLI/SDK, Claude Agent, Codex, and Codex Agent adapters distinguish an
  absent upstream field from explicit empty.
- `_execution_succeeded()` continues to admit only `completed`, `end_turn`,
  `stop`, `stop_sequence`, and `success`.
- Public actual and baseline tests prove that empty, missing, whitespace,
  unknown, nonterminal, tool/action, truncation, error, cancellation,
  timeout, and skipped finishes remain economically ineligible.

### Persistent provider-call accounting

- `agent-runtime-provider-call-start/v1` is reservation-bound and immutable
  through the public API.
- Actual worker, auto-dispatch, SDK fixture, native bridge authorize, and
  council authorize paths write a marker before their provider/spawn
  boundary.
- Generic completed, error, and skipped observed usage without a marker
  retains the complete task and claim ceiling after restart.
- Matching completed and provider-error markers settle to observed usage.
- A marker without a receipt remains a pending reservation.
- A marker plus skipped receipt remains conservative.
- Marker/no-provider settlement conflict is rejected.
- Exact marker replay is idempotent; conflicting replay is rejected.
- Orphan, duplicate, malformed, provider, surface, source-transition,
  reservation, task, claim, authority, fingerprint, status, and identity
  mutations fail closed.
- Council bulk authorization writes no marker when any requested member is
  denied, and accepted members receive member-specific markers.

## Whole-range regression assessment

No regression was found in the earlier TASK-AR-652 controls:

- explicit role policy covers Scribe, exploration, implementation, review,
  audit, and the generic parent-session path;
- high-tier routing requires registered escalation authority;
- caller-supplied or partially pre-resolved route dictionaries cannot bypass
  canonical role policy;
- task and claim budget authority is canonical, atomic, append-only, and
  persistent across process restart;
- duplicate dispatch, receipt replay, ledger corruption, and claim authority
  drift fail closed;
- configured and observed provider identities must be registered and match;
- unsupported reasoning is bound to the observed provider capability;
- SDK selection is not promoted into observed provider/model/reasoning
  telemetry;
- missing or partial usage remains unverified;
- only positive terminal-success spellings can make actual or baseline
  execution successful;
- dedicated no-provider settlement remains restricted to the two legitimate
  auto-dispatch pre-call transitions; and
- route equivalence compares both model and reasoning effort.

The P1 finding is narrower but release-blocking: persistent budget safety is
correct, while the same unproven observations still reach the economic
scoreboard.

## Verification commands and results

Every Python, test, gate, and adversarial command ran with
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`,
`AZURE_OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`AWS_SESSION_TOKEN` removed. Bytecode and pytest cache writes were disabled.
No credential value was read, and all provider controls were fake, dummy,
synthetic, or in-memory.

Test suites:

- focused eval/bridge/worker/auto/SDK repair matrix:
  `223 passed in 5.79s`;
- required root routing/claim/doctor suite:
  `108 passed in 27.86s`;
- required six-module consumer-template suite:
  `290 passed in 6.10s`;
- SDK fake-provider and concrete-adapter suite:
  `5 passed in 0.31s`;
- taskset governance suite:
  `12 passed in 0.47s`;
- managed-host lock suites:
  `23 passed in 1.34s`;
- full canonical Runtime suite:
  `2982 passed, 3 skipped, 4 warnings in 156.96s`.

The four warnings are the existing UI beta invalid-escape warnings.

An exploratory invocation that combined `tests` and the entire packaged
template script directory in one pytest process produced collection-name and
host-import collisions. That is not the repository's canonical suite; the
configured `python -m pytest -q` command and every required separately
isolated template module passed as listed above.

Repository gates and static checks:

- Runtime assets: 38 assets, 404 uses, 0 blocks, 0 watches;
- template mirror: 84 common, 81 identical, 3 intentional, 0 findings;
- evidence index: 0 findings;
- root and packaged taskset work gates: 0 findings;
- T3 plan assumptions for
  `TASKSET-AR-V080-OPERABILITY-HARDENING`: 0 findings;
- managed-host lock: current;
- integrated Owner governance: exit 0, with only nonblocking watches and
  advisories;
- root/template SHA-256 and byte parity for `model_routing.py`,
  `task_claim_dispatcher.py`, and `taskset_work_gate.py`: exact;
- in-memory compilation of all 25 Python files changed in the complete
  acceptance range: pass;
- focused repair, focused candidate, worktree, and index
  `git diff --check`: pass;
- complete acceptance range `git diff --check`: fail with the P2 finding
  above.

## Boundary and claim disposition

The claim file's pre-report SHA-256 was
`997dbf33dbb7cc8e660614dcb037476106ecf473ee6a568bbcd69ff7a0aa37ce`.
It remained `claimed`, phase `wave-claimed`, under worker
`le-20260730-123600-kst-ar652001`, with no verifier or release transition.

No production code, task/unit metadata, evidence index, plan assumption,
managed-host lock, consumer primary, credential, environment setting,
dependency, provider account, database, broker, order, notification,
deployment, remote branch, tag, version, publication, or release state was
changed by this review.

The sole permitted repository mutation is this report:
`reviews/W4B-2026-07-30-unit-task-ar-652-001-call-provenance-final.md`.

Because this verdict contains a task-scope P1 finding, the claim must remain
claimed and unreleased.

## Final verdict

`REVISE — P0: 0, P1: 1, P2: 1`
