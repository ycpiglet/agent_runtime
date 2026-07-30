---
title: W4b Provenance Final - TASK-AR-652 Terminal Success and Budget Settlement Review
date: 2026-07-30
created_at: 2026-07-30T19:25:38+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_commit: 450d39eebaaeecf9b1ac99866ea08986fc91d7c4
reviewed_tree: 15c941b55be0ab754726dbd3f80a49620ab06b67
implementation_commit: 8534f2a13a8d059168c4d9ae8b3718a0862f4eee
implementation_tree: 354e1b74aa2e99634937e55bc282ce7fdf21dfa5
latest_replan_commit: a70dfeefc59418cff987e296a93fb4061aae96b2
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..450d39eebaaeecf9b1ac99866ea08986fc91d7c4
focused_repair_range: a70dfeefc59418cff987e296a93fb4061aae96b2..8534f2a13a8d059168c4d9ae8b3718a0862f4eee
focused_candidate_range: 8534f2a13a8d059168c4d9ae8b3718a0862f4eee..450d39eebaaeecf9b1ac99866ea08986fc91d7c4
verifier_agent_instance_id: qa-20260730-w4b-ar652-provenance-final
verified_by: qa-20260730-w4b-ar652-provenance-final
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_provenance_final
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-terminal-integrity-final.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-terminal-provenance-success-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-terminal-provenance-success-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730190052.json
tags: [w4b, provenance, terminal-success, budget-integrity, independent-verification, revise]
---

# W4b Provenance Final - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 2, P2: 0`

The exact candidate is not ready for approval. The focused repair correctly
replaces the former finish-reason denylist with a positive success allowlist
and introduces a narrow, reservation-bound no-provider settlement. Independent
adversarial verification nevertheless found two fail-open inputs at those same
release boundaries:

1. an explicitly empty finish reason is converted to allowlisted `stop` before
   the positive predicate sees it; and
2. a generic skipped receipt with caller-supplied observed zero-token
   components settles a reservation as ordinary observed usage, bypassing the
   dedicated no-provider provenance path.

Immediately before this report was written, both worktree and index were
clean. `HEAD` was
`450d39eebaaeecf9b1ac99866ea08986fc91d7c4`, tree
`15c941b55be0ab754726dbd3f80a49620ab06b67`. The focused implementation was
`8534f2a13a8d059168c4d9ae8b3718a0862f4eee`, tree
`354e1b74aa2e99634937e55bc282ce7fdf21dfa5`.

The complete acceptance range
`da4177f6211b2a1a049ba25b62332b113a54cf97..450d39eebaaeecf9b1ac99866ea08986fc91d7c4`,
focused repair range
`a70dfeefc59418cff987e296a93fb4061aae96b2..8534f2a13a8d059168c4d9ae8b3718a0862f4eee`,
and implementation-to-candidate metadata range
`8534f2a13a8d059168c4d9ae8b3718a0862f4eee..450d39eebaaeecf9b1ac99866ea08986fc91d7c4`
were reviewed independently.

Verifier `qa-20260730-w4b-ar652-provenance-final`, role `qa-reviewer`, is
distinct from worker `le-20260730-123600-kst-ar652001`. Worker W4a and the
canonical VERIFY record were read as supporting evidence, not treated as
verification authority.

## P1-1 - Explicitly empty finish values are promoted to successful `stop`

The repaired success predicate is correct in isolation.
`SUCCESSFUL_EXECUTION_FINISH` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:43-49` contains
only `completed`, `end_turn`, `stop`, `stop_sequence`, and `success`.
`_execution_succeeded()` at lines 399-410 additionally requires completed
status, no error, and outcome `ok`.

The public record constructors erase the distinction between omission and an
explicit empty value before that predicate runs:

- `record_execution_receipt()` writes
  `str(finish_reason or "stop")` at
  `src/agent_runtime/templates/project/scripts/eval_harness.py:1425`;
- `codex_subagent_bridge.record_reply()` converts a falsy finish value to
  `stop` for completed status at
  `src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py:706-715`;
- the worker and SDK recording paths use the same truthiness fallback at
  `src/agent_runtime/templates/project/scripts/agent_worker.py:666`,
  `src/agent_runtime/templates/project/scripts/agent_worker.py:1135`, and
  `src/agent_runtime/templates/project/scripts/verify_sdk_backend.py:199`.

Consequently, the allowlist cannot fail closed on the explicitly empty value
required by the accepted replan. It receives `stop`, not the original invalid
input.

### Independent public-path reproduction

An offline `codex_subagent_bridge.create_dispatch_packet()` /
`record_reply()` matrix used matching registered provider, model, and
reasoning observations; authoritative token components and billed costs; a
successful observed 100-token/USD 0.10 baseline; and a 15-token/USD 0.02
actual. No finalized route or eligibility field was forged.

| Actual finish input | Stored finish | Final application/route | Token eligible | Money eligible |
| --- | --- | --- | ---: | ---: |
| `""` | `stop` | `applied` / `effective` | 1 | 1 |
| `"   "` | whitespace | `unverified` / `unverified` | 0 | 0 |
| unknown/nonterminal/tool/truncation values | unchanged | `unverified` / `unverified` | 0 | 0 |
| `stop` control | `stop` | `applied` / `effective` | 1 | 1 |
| `" END_TURN "` control | normalized by predicate | `applied` / `effective` | 1 | 1 |

The negative matrix included unknown, `incomplete`, `in_progress`, `queued`,
`requires_action`, `tool_use`, `tool_call`, `action_required`, `length`,
`max_tokens`, `truncated`, failure, cancellation, timeout, and skipped values.
All nonempty negatives fail closed as intended.

A symmetric baseline reproduction recorded a completed, otherwise fully
observed baseline with explicit `finish_reason=""`. The constructor stored
`stop`; finalization marked the baseline verified, and both token and money
eligibility became 1 for the successful actual. Thus this is present at both
the actual and baseline economic boundaries.

These are synthetic eligibility outputs only. They are not token or monetary
savings claims.

### Required repair

- Preserve the distinction between an omitted finish value and an explicitly
  supplied empty value. Do not use truthiness fallback for completion
  provenance.
- Normalize first, then admit only the five positive terminal-success
  spellings. Explicit empty, whitespace, unknown, nonterminal, tool/action,
  truncation, failure, cancellation, timeout, and skipped values must remain
  non-success.
- If a specific adapter may synthesize a canonical success value when the
  provider truly omits a field, make that an explicit adapter contract backed
  by provider-return provenance; do not make explicit empty equivalent to
  omission.
- Add public bridge, provider/worker/SDK adapter, finalizer, and report tests
  for explicit empty values on both actual and baseline receipts, alongside
  the five supported success controls.

## P1-2 - Skipped observed-zero receipts bypass no-provider settlement provenance

The dedicated no-provider settlement is narrow and well bound. The accepted
transitions at
`src/agent_runtime/templates/project/scripts/eval_harness.py:50-53` are only
`auto_dispatch -> session_budget_preflight` and
`auto_dispatch -> claim_preflight`. `_verified_pre_provider_skip()` at lines
449-509 validates the reservation, immutable settlement, transition, task,
claim, reservation fingerprint, authority fingerprint, receipt linkage, and
absence of provider and usage observations.

However, `_budget_settlement_basis()` checks generic authoritative token usage
first at lines 512-523. `_has_authoritative_token_usage()` at lines 413-430
validates the observed flag, nonnegative components, and component sum, but
does not require execution status, provider-return provenance, or a status
consistent with an actual provider result. Zero input plus zero output
therefore qualifies.

`_usage_from_records()` treats `observed_usage` as fully settled at lines
842-868. It neither retains the reservation ceiling nor requires the dedicated
settlement. The public native bridge exposes the contradiction because
`record_reply()` accepts `status="skipped"` and token components, then writes
a generic `native_codex_reply` receipt at
`src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py:752-802`.

### Independent public-path and true-restart reproduction

The synthetic fixture created canonical task and active-claim token budgets of
10, then:

1. called `codex_subagent_bridge.create_dispatch_packet()` and reserved the
   full ceiling of 10;
2. called `record_reply(status="skipped", finish_reason="skipped",
   error="synthetic spawn did not occur", tokens_in=0, tokens_out=0)`;
3. inspected the durable ledger; and
4. launched a genuinely fresh Python process to request a second ceiling-10
   reservation for the same task and claim.

| First receipt | Settlement ID | Computed basis | Task committed | Claim committed | Fresh ceiling 10 |
| --- | --- | --- | ---: | ---: | --- |
| skipped, explicit observed `0 + 0` | null | `observed_usage` | 0 | 0 | allowed |
| skipped, token usage unavailable control | null | `conservative_ceiling` | 10 | 10 | blocked |

The first receipt's source was the bridge's real `native_codex_reply`, not a
forged stored settlement basis. No dedicated no-provider settlement existed.
The fresh process independently re-read the append-only ledger, so the result
is a durable task-and-claim accounting bypass rather than an in-memory cache
artifact.

A direct public-ledger control produced the same outcome for skipped generic
receipts with explicit observed zero: they were classified as
`observed_usage` before the dedicated provenance check. When the same
receipts had unavailable components, the complete ceiling remained committed.

No provider was called in either fixture. Explicit zeros on a declared
skipped/no-call path are caller assertions, not authoritative provider-return
usage. Treating them as ordinary observed usage makes the dedicated
no-provider settlement optional and allows repeated ceiling reuse across
restarts.

### Required repair

- Make authoritative usage classification consistent with execution
  provenance. A skipped/no-call terminal receipt must not settle through
  generic observed usage merely because its caller supplied `0 + 0`.
- Reject contradictory token telemetry on skipped/no-call receipts, or
  downgrade it to unavailable and retain the conservative ceiling unless the
  validated dedicated no-provider settlement authorizes release.
- Preserve valid observed usage from real provider-return paths, including
  error paths that can legitimately carry usage, by binding the observation
  to the relevant execution surface/result provenance rather than status
  text alone.
- Add public native-bridge and direct-ledger task-and-claim tests for skipped
  `0 + 0`, impossible source/status pairs, and missing settlement provenance.
  Each negative must be re-read in a fresh process and block a second full
  reservation. Keep the two legitimate auto-dispatch no-call transitions and
  a real observed-provider usage control.

## Repaired controls that remain effective

The two findings do not invalidate the rest of the focused repair:

- the positive success predicate rejects every tested nonempty unknown,
  nonterminal, tool/action, truncation, failure, cancellation, timeout, and
  skipped finish value for both actual and baseline evidence;
- caller-forged stored application, route, and settlement-basis fields do not
  override report-time recomputation;
- the valid dedicated settlement copies canonical task and claim identity
  from its reservation and releases exactly one reservation;
- caller-supplied task or claim mismatches, invalid transitions, provider
  observations, non-null token components, and billed-cost observations fail
  closed;
- single-field tampering of settlement schema, identity, dispatch, task,
  claim, reservation identity/source/fingerprint, receipt source,
  authority fingerprint, status, or observations is rejected;
- missing settlement provenance retains the conservative ceiling;
- duplicate, orphaned, mismatched, partially written, and malformed settlement
  ledger records raise integrity errors;
- the actual auto-dispatch session-budget and claim-lost branches emit the
  dedicated settlement and perform zero provider calls.

Whole-range provider identity, SDK telemetry, routing, role-tier, and economic
controls also remain effective:

- configured and observed provider identities must be registered and match;
- missing or incomplete SDK provider telemetry remains unverified;
- low/standard roles cannot silently obtain a high tier without a registered
  trigger, while registered audit/planning/security triggers are explicit;
- token components, billed cost, currency, baseline comparison, and provider
  route identity must be authoritative before economic eligibility.

## Verification commands and results

Every Python, test, gate, and adversarial command ran with
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`,
`AZURE_OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`AWS_SESSION_TOKEN` removed. Bytecode and pytest cache writes were disabled.
No repository or template `.env` file existed.

Required and regression suites:

- root routing/claim/doctor suite: `108 passed in 27.62s`;
- required six-module template suite: `256 passed in 4.26s`;
- SDK fake-provider suite: `3 passed in 0.11s`;
- taskset governance plus managed-host lock suites:
  `35 passed in 1.63s` (`12 + 23`);
- focused terminal-success, settlement, and auto-dispatch matrix:
  `55 passed, 123 deselected in 1.82s`;
- direct auto-dispatch no-provider branch controls:
  `3 passed in 0.29s`;
- full Runtime suite:
  `2982 passed, 3 skipped, 4 warnings in 156.33s`.

The four warnings were the existing UI beta invalid-escape warnings.

Independent adversarial checks:

- direct success-predicate matrix: all five supported spellings, including
  case and outer whitespace variants, accepted; empty, whitespace, unknown,
  nonterminal, action/tool, truncation, error, cancellation, timeout, and
  skipped variants rejected;
- public actual and baseline bridge matrix: explicit empty alone was stored as
  `stop` and became economically eligible;
- settlement tamper matrix: every single-field provenance mutation rejected;
- valid, missing, duplicate, orphan, and partial-ledger settlement matrix:
  valid release succeeded, missing remained conservative, and malformed or
  conflicting records failed closed;
- true fresh-process public bridge matrix: skipped observed zero released both
  task and claim ceilings without a settlement, while unavailable usage
  retained both ceilings.

Repository gates and static checks:

- Runtime assets: 38 assets, 404 uses, 0 blocks, 0 watches;
- template mirror: 84 common, 81 identical, 3 intentional, 0 findings;
- managed-host lock: current;
- evidence index: 0 findings;
- root and packaged taskset gates: 0 findings;
- T3 plan-assumption gate for
  `TASKSET-AR-V080-OPERABILITY-HARDENING`: 0 findings;
- integrated Owner governance: exit 0, with only nonblocking watches and
  advisories;
- root/template SHA-256 and byte parity for `model_routing.py`,
  `task_claim_dispatcher.py`, and `taskset_work_gate.py`: exact;
- in-memory compilation of all 22 Python files changed in the full acceptance
  range: pass;
- `git diff --check` for the full range, focused repair range, worktree, and
  index: pass.

All execution controls used fake, synthetic, dummy, or in-memory data. No live
provider or network endpoint was called, no credential value was read, and no
dependency was installed.

## Boundary and claim disposition

No production code, task/unit metadata, evidence index, taskset assumption,
managed-host lock, consumer primary, credential, environment setting,
dependency, provider account, database, broker, order, notification,
deployment, remote branch, tag, version, publication, or release state was
changed by this review.

The claim
`agents/runtime/task_claims/CLAIM-20260730-123600-task-ar-652-ar652001.json`
remains `claimed`, phase `wave-claimed`, under worker
`le-20260730-123600-kst-ar652001`. It has no release or verifier transition.
Because this verdict contains task-scope P1 findings, it must remain claimed.

## Final verdict

`REVISE — P0: 0, P1: 2, P2: 0`

