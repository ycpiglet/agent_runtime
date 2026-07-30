---
title: W4b Provider Identity - TASK-AR-652 Independent Economic Routing Review
date: 2026-07-30
created_at: 2026-07-30T17:21:05+09:00
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_commit: 2c143d3a269f21e40f62351790baf1d2cd527561
reviewed_tree: 458ec229a99824be23a456bbf206dad563c78a34
repair_base: c7ca39afc53c9c0a63be93a545dab48742f22c8f
implementation_commit: f48ff8a9514a5e1e49e784088ba19ad283328289
implementation_tree: 8d7442f26247df91d9bf2d6dc2b0e764c039862c
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..2c143d3a269f21e40f62351790baf1d2cd527561
focused_repair_range: c7ca39afc53c9c0a63be93a545dab48742f22c8f..f48ff8a9514a5e1e49e784088ba19ad283328289
focused_candidate_range: c7ca39afc53c9c0a63be93a545dab48742f22c8f..2c143d3a269f21e40f62351790baf1d2cd527561
verifier_agent_instance_id: qa-20260730-w4b-ar652-provider-identity
verified_by: qa-20260730-w4b-ar652-provider-identity
verifier_role: qa-reviewer
verifier_task: /root/task_ar_652_w4b_provider_identity
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-candidate.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-candidate-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-provider-identity-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730170435.json
tags: [w4b, provider-identity, independent-verification, execution-receipts, telemetry-integrity, revise]
---

# W4b Provider Identity - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 1, P2: 0`

Immediately before this report was added, the worktree and index were clean.
The exact final candidate was commit
`2c143d3a269f21e40f62351790baf1d2cd527561`, tree
`458ec229a99824be23a456bbf206dad563c78a34`. The focused implementation was
commit `f48ff8a9514a5e1e49e784088ba19ad283328289`, tree
`8d7442f26247df91d9bf2d6dc2b0e764c039862c`.

The complete acceptance range
`da4177f6211b2a1a049ba25b62332b113a54cf97..2c143d3a269f21e40f62351790baf1d2cd527561`,
focused provider-identity implementation
`c7ca39afc53c9c0a63be93a545dab48742f22c8f..f48ff8a9514a5e1e49e784088ba19ad283328289`,
and focused exact-candidate range
`c7ca39afc53c9c0a63be93a545dab48742f22c8f..2c143d3a269f21e40f62351790baf1d2cd527561`
were reviewed independently.

Verifier `qa-20260730-w4b-ar652-provider-identity`, role `qa-reviewer`, is
distinct from worker `le-20260730-123600-kst-ar652001`. The worker W4a and
canonical VERIFY record were read but not treated as authority.

The focused provider-identity repair closes the prior W4b finding in all
requested baseline/actual, reasoning-absent/reasoning-present, token, and
monetary cases. One complete-range execution-receipt P1 remains: the live SDK
verifier fabricates `observed_provider` from its selected backend whenever the
provider completion does not supply provider telemetry.

## P1 - Live SDK verifier promotes backend selection into observed telemetry

`src/agent_runtime/templates/project/scripts/verify_sdk_backend.py:62-96`
writes an immutable execution receipt. At lines 75-77 it sets:

```python
observed_provider=str(getattr(result, "provider", "") or "claude")
if result
else None
```

Thus any truthy completion object is recorded with
`observed_provider="claude"` even when it has no provider field. That value is
the selected backend name from `get_provider("claude")` at line 105, not
provider telemetry returned by the completion.

The declared `ProviderResult` contract at
`src/agent_runtime/templates/project/scripts/providers/base.py:34-48` has no
provider field. The shipped SDK fake at
`src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py:19-37`
also returns no provider field. Its test still passes because it asserts only
source, status, and token count.

### Independent offline reproduction

A temporary-ledger call to `_record()` used a successful `SimpleNamespace`
completion carrying model, reasoning, tokens, billed cost, and currency, but
no provider attribute. No provider call or network access occurred.

```json
{
  "completion_provider_attribute": null,
  "receipt_provider": "claude",
  "receipt_observed_provider": "claude",
  "receipt_source": "verify_sdk_backend",
  "receipt_status": "completed"
}
```

Control calls proved this is isolated from the focused provider repair:

- `eval_harness.record_execution_receipt()` preserved a missing
  `observed_provider` as null.
- `agent_worker._completion_observation()` preserved a missing completion
  provider as null.
- `codex_subagent_bridge._completion_observation()` preserved an omitted
  provider as null.

The economic gate currently fails closed for this receipt because bare
`claude` is not a registered canonical identity. This reproduction therefore
does not establish or claim any token or monetary savings. It nevertheless
falsifies the immutable observation field and directly violates the replan
invariant that completion provider telemetry must never be inferred from
request configuration or backend selection. Other receipt consumers can no
longer distinguish actual completion telemetry from a selected adapter name.

### Required repair

1. Remove the fallback provider value. If the completion does not explicitly
   carry provider telemetry, record `observed_provider=null`.
2. Keep configured/selected backend identity in the configured `provider` or
   execution-surface fields only.
3. If the provider adapter is extended to return completion provider
   telemetry, require an explicit registered canonical identity and preserve
   missing/unknown values as ineligible.
4. Add an SDK negative whose successful completion lacks provider telemetry
   and asserts a null observed provider plus zero token and monetary
   eligibility. Add a positive only for explicit matching completion
   telemetry.

## Provider-identity repair assessment

The focused repair itself passes.

An independent temporary-ledger matrix covered 20 negative cases:

- both baseline and actual receipts;
- missing observed provider, unknown observed provider, and cross-provider
  mismatch;
- missing and unknown configured provider controls;
- reasoning absent on `codex-agent` routes and reasoning present on native
  Codex routes;
- finalizer-level and report-level checks with forged success flags retained;
- both token and billed-cost eligibility.

Every negative produced zero token-eligible and zero monetary-eligible
records. Baseline defects made the baseline reference invalid; actual defects
made application status unverified. The report independently rechecked both
sides and rejected stale or forged `applied` / `effective` flags.

Five positive alias pairs remained valid:

- `native-codex`, `codex-session`, and `codex-native` normalized to the same
  native identity with reasoning telemetry present;
- `codex` and `codex-agent` normalized to the same provider-worker identity
  with the authoritative unsupported-reasoning contract.

These were synthetic eligibility controls only. No economic savings conclusion
is drawn from them.

The native forgery control also passed: a native baseline and actual receipt
with populated resolved reasoning, absent observed reasoning, and a forged
`resolved_reasoning_source=unsupported` left the baseline invalid and both
economic paths ineligible.

## Earlier W4b regression assessment

- Partial tier/provider assertion dictionaries: pass. Prompt rendering and
  message emission reject partial tier, partial alternate-provider, and mixed
  assertions before executable authority or message persistence. Explicit
  tier, trigger, and provider arguments remain valid controls.
- Native `unsupported` reasoning forgery: pass at finalization and report
  boundaries.
- Persistent budgets and restart behavior: pass. Canonical claim authority,
  zero/invalid budgets, atomic reservations, ambiguous-claim failure, and
  cumulative restart enforcement all remain fail-closed before a provider
  call.
- Replay and equivalence: pass. Duplicate dispatch and open-inbox replay make
  one provider call/one receipt; observed-equivalent routes override forged
  savings flags.
- Execution-receipt and governance boundaries: terminal receipt, claim loss,
  policy rejection, council atomicity, taskset projection, and Owner governance
  controls pass. The SDK provider-observation falsification above remains the
  sole release-blocking receipt-integrity defect.

## Verification commands and results

Every Python/test/gate command ran with
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`,
`AZURE_OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`AWS_SESSION_TOKEN` removed from the process environment. Bytecode and pytest
cache writes were disabled.

Required suites:

- `python -m pytest tests/test_model_routing.py tests/test_task_claim_dispatcher.py tests/test_doctor.py -q`
  -> `108 passed in 26.67s`.
- The required six-module template routing/dispatch/bridge/worker/auto/eval
  suite -> `193 passed in 2.15s`.
- `python -m pytest src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q`
  -> `2 passed in 0.13s`.
- `python -m pytest tests/test_taskset_work_gate.py -q`
  -> `12 passed in 0.47s`.
- `python -m pytest tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q`
  -> `23 passed in 1.32s`.
- `python -m pytest -q`
  -> `2982 passed, 3 skipped, 4 pre-existing UI beta invalid-escape warnings
  in 156.66s`.

Focused/adversarial evidence:

- Focused earlier-boundary pytest selection -> `38 passed, 128 deselected in
  0.68s`.
- Independent provider matrix -> 20 negative cases rejected on token and
  monetary paths; five registered-alias positive controls accepted.
- Independent native unsupported-reasoning forgery -> baseline invalid,
  token eligibility 0, monetary eligibility 0.
- Independent SDK telemetry reproduction -> completion provider absent,
  receipt `observed_provider="claude"`.

Governance and static evidence:

- `python scripts/runtime_asset_usage.py --check` -> 38 assets, 404 uses,
  0 blocks, 0 watches.
- `python scripts/template_mirror_gate.py --check` -> 84 expected/common,
  81 identical, 3 intentional, 0 findings.
- Managed-host lock check -> current.
- Evidence index -> 0 findings.
- Root and packaged taskset gates -> 0 findings.
- T3 plan-assumption gate -> 0 findings.
- Integrated Owner governance -> exit 0 with only non-blocking watches and
  advisories.
- SHA-256 parity is exact for root/template `model_routing.py`,
  `task_claim_dispatcher.py`, and `taskset_work_gate.py`.
- In-memory compilation of all 22 Python files changed across the acceptance
  range passed.
- `git diff --check` passed for the full acceptance range, focused
  implementation repair, focused exact candidate, worktree, and index.

No credential value was read. No live provider or network endpoint was called.
No package was installed. No consumer primary, account, database, broker,
notification, deployment, remote branch, push, tag, version, publication, or
release state was changed.

## Claim and boundary disposition

Only this report was added. No implementation, test, task/unit record, claim,
handoff, log, board, review index, plan assumption, registry, managed asset,
host lock, consumer project, credential, environment setting, dependency,
provider, account, broker, database, notification, deployment, remote branch,
tag, version, publication, or release state was changed.

`CLAIM-20260730-123600-task-ar-652-ar652001` remains `claimed` and unreleased.
This verifier did not invoke claim release, closeout, merge, commit, push,
deployment, or publication. A repaired exact candidate needs a fresh
independent W4b before release.

REVISE — P0: 0, P1: 1, P2: 0
