---
title: W4b Final Candidate - TASK-AR-652 Independent Economic Routing Review
date: 2026-07-30
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
claim_id: CLAIM-20260730-123600-task-ar-652-ar652001
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: da4177f6211b2a1a049ba25b62332b113a54cf97
reviewed_commit: c7ca39afc53c9c0a63be93a545dab48742f22c8f
reviewed_tree: 30dddc3041d99c0e0cffdf86dc2689e7e7c14bbc
repair_base: fd06f7be04a678a5c306a1582a8086b5b9666bbd
implementation_commit: 4f721559d45a02f20e9035d7443cbfeceb9c48b0
implementation_tree: 3d4bde7200c2855af0b11fa9d36320fe68ca7cfe
full_review_range: da4177f6211b2a1a049ba25b62332b113a54cf97..c7ca39afc53c9c0a63be93a545dab48742f22c8f
focused_repair_range: fd06f7be04a678a5c306a1582a8086b5b9666bbd..4f721559d45a02f20e9035d7443cbfeceb9c48b0
focused_candidate_range: fd06f7be04a678a5c306a1582a8086b5b9666bbd..c7ca39afc53c9c0a63be93a545dab48742f22c8f
verified_by: codex-independent-task-ar-652-w4b-final-candidate
verifier_task: /root/task_ar_652_w4b_final_candidate
verifier_role: independent-auditor
worker_identity: le-20260730-123600-kst-ar652001
independence_status: independent
pre_report_worktree_status: clean
claim_disposition: remain_claimed
prior_w4b: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-approval.md
replan: reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-approval-replan.md
w4a_evidence: reviews/W4A-2026-07-30-unit-task-ar-652-001-final-approval-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730163357.json
tags: [w4b, final-candidate, independent-verification, model-routing, execution-receipts, savings-integrity, revise]
---

# W4b Final Candidate - UNIT-TASK-AR-652-001

## Independent verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

Before this report was added, the worktree was clean and the exact candidate
was commit `c7ca39afc53c9c0a63be93a545dab48742f22c8f`, tree
`30dddc3041d99c0e0cffdf86dc2689e7e7c14bbc`. The final implementation is
commit `4f721559d45a02f20e9035d7443cbfeceb9c48b0`, tree
`3d4bde7200c2855af0b11fa9d36320fe68ca7cfe`.

The complete acceptance range
`da4177f6211b2a1a049ba25b62332b113a54cf97..c7ca39afc53c9c0a63be93a545dab48742f22c8f`,
focused implementation repair
`fd06f7be04a678a5c306a1582a8086b5b9666bbd..4f721559d45a02f20e9035d7443cbfeceb9c48b0`,
and focused exact-candidate range
`fd06f7be04a678a5c306a1582a8086b5b9666bbd..c7ca39afc53c9c0a63be93a545dab48742f22c8f`
were inspected independently.

This verifier is
`codex-independent-task-ar-652-w4b-final-candidate`, role
`independent-auditor`, and is distinct from worker
`le-20260730-123600-kst-ar652001`. The worker's conclusions and canonical
W4a evidence were read but not assumed; all required suites, governance gates,
and adversarial controls were rerun.

The repair closes both latest reported P1s in their stated cases. Partial
tier/provider assertion dictionaries no longer select execution authority,
and native receipts cannot self-declare reasoning unsupported. One adjacent
P1 remains: the unsupported-reasoning exception does not bind the configured
provider to a known, matching observed provider. Missing, unknown, and
different unsupported observed providers can therefore create verified token
and billed-cost savings.

## P1 - Unsupported reasoning is not bound to observed provider identity

`provider_reasoning_capability()` at
`scripts/model_routing.py:637-648` and its packaged mirror correctly classify
registered providers as `required`, `unsupported`, or `unknown`.
`_route_observation_complete()` at
`src/agent_runtime/templates/project/scripts/eval_harness.py:1149-1173`
does not enforce provider identity:

1. It returns true immediately when an observed reasoning value exists,
   before validating either provider.
2. When reasoning is absent, it rejects only an observed provider whose
   capability is `required`.
3. It then accepts the receipt when the configured provider is
   `unsupported` and the receipt string says `unsupported`.

Consequently, an empty or unknown observed provider is treated like an
unsupported provider. A different registered unsupported provider, such as
configured `codex-agent` with observed `claude-agent`, is also treated as
equivalent. Capability equality is not provider identity.

### Independent finalizer and report reproduction

Each offline case used one immutable baseline and one actual receipt with the
same workload. The baseline observed 100 tokens and USD 0.10 on
`model-expensive`; the actual observed 15 tokens and USD 0.02 on
`model-cheap`. Both configured `codex-agent`, whose canonical route has
`resolved_reasoning_effort=None` and
`resolved_reasoning_source=unsupported`. Only the indicated
`observed_provider` field changed.

| Changed receipt | `observed_provider` | Finalizer result | Token result | Monetary result |
| --- | --- | --- | --- | --- |
| actual | missing | `verified`, `applied`, `effective` | 1 eligible, 85 saved | 1 eligible, USD 0.08 saved |
| actual | `unknown-provider` | `verified`, `applied`, `effective` | 1 eligible, 85 saved | 1 eligible, USD 0.08 saved |
| actual | `claude-agent` | `verified`, `applied`, `effective` | 1 eligible, 85 saved | 1 eligible, USD 0.08 saved |
| baseline | missing | baseline accepted as complete | 1 eligible, 85 saved | 1 eligible, USD 0.08 saved |
| baseline | `unknown-provider` | baseline accepted as complete | 1 eligible, 85 saved | 1 eligible, USD 0.08 saved |
| baseline | `claude-agent` | baseline accepted as complete | 1 eligible, 85 saved | 1 eligible, USD 0.08 saved |

The actual-row cases isolate the defect from the baseline: their baseline was
the canonical `codex-agent` positive. The baseline-row cases isolate the
inverse defect: their actual was canonical. Thus neither finalization nor
reporting requires a known matching observed provider for the unsupported
exception.

This violates the acceptance rule that savings require an observed comparable
baseline. It also permits a report to treat completion telemetry from one
provider, no provider, or an unknown provider as evidence that the configured
provider route was applied.

### Controls that pass

- A native baseline with resolved reasoning `high`, a forged
  `resolved_reasoning_source=unsupported`, and no observed reasoning is
  `invalid` with `baseline_route_observation_incomplete`; token and monetary
  eligible counts are zero.
- A report-level native actual with resolved reasoning `low`, forged
  `unsupported`, no observed reasoning, and forged
  `verified`/`applied`/`effective` flags is excluded as
  `observed_reasoning_unavailable`; token and monetary eligible counts are
  zero.
- Any non-null resolved reasoning still needs an observed reasoning value.
- Observed native identities `native-codex`, `codex-session`, and
  `codex-native` are all classified reasoning-required and fail closed without
  reasoning; token and monetary eligible counts are zero.
- A canonical configured/observed `codex-agent` pair remains eligible. The
  registered `codex` alias paired with observed `codex-agent` also remains
  eligible.

These controls show that the intended native repair works and that a valid
unsupported-provider path can be preserved. They do not close missing,
unknown, or cross-provider observations.

### Required repair

Provider identity validation must precede every success return from
`_route_observation_complete()`:

1. Canonicalize both configured and observed provider names through a trusted
   registry that returns a canonical provider identity and reasoning
   capability.
2. Reject a missing or unknown configured or observed provider.
3. Reject canonical provider mismatch. Registered aliases may compare equal
   only when they normalize to the same identity, for example
   `codex`/`codex-agent` and the native Codex aliases.
4. If `resolved_reasoning_effort` is non-null, always require observed
   reasoning.
5. Permit absent observed reasoning only when both provider identities match,
   the canonical capability is `unsupported`, the resolved reasoning is null,
   and the canonical route source is `unsupported`.
6. Apply this check to baseline finalization and report-level actual
   validation. Add baseline and actual negatives for missing, unknown, and
   mismatched providers across token and billed-cost paths, plus native-alias
   negatives and canonical `codex-agent`/`codex` positives.

## Closure of the two latest reported P1s

### Partial route assertions

At both `render_prompt()` and `emit_call_message()`:

- partial `{"requested_tier": "reviewer_standard"}` was rejected against the
  Scribe's authoritative `worker_low`;
- partial `{"provider": "codex-agent"}` was rejected against the default
  `native-codex`;
- the mixed partial tier/provider case was rejected before emission, with no
  message file created.

Separate trusted controls work:

- explicit `requested_tier=reviewer_standard` rendered and emitted that tier;
- explicit `requested_tier=planner_high` plus registered
  `data_integrity` rendered and emitted an authorized high route with reason
  `trigger:data_integrity`;
- explicit `provider=codex-agent` rendered and emitted the registered alternate
  provider;
- an asserted `codex-agent` route with explicit
  `provider=native-codex` was rejected at both boundaries.

This latest P1 is closed.

### Native unsupported-reasoning forgery

The native baseline and report-level actual attacks now yield zero token and
monetary eligibility. Non-null resolved reasoning requires observation,
native aliases are reasoning-required, and the canonical `codex-agent`
unsupported route remains usable. The original native self-declaration P1 is
closed; the provider-identity P1 above is a distinct remaining boundary.

## Regression samples of the four earlier repaired boundaries

The 22-case focused selection passed.

- Ordinary CLI/legacy role policy: Scribe remains role-bound, raw model input
  is rejected, legacy routing is re-resolved, and a normal Codex Scribe packet
  uses `worker_low`.
- Claim/budget authority and restart: the claim record remains authoritative,
  cumulative task/claim usage survives restart, and a canonical zero claim
  budget blocks before a fake provider call.
- Replay/policy terminals: duplicate dispatch and repeated inbox replay make
  one provider call and retain one receipt; auto-dispatch and worker raw routes
  produce terminal policy receipts without provider calls.
- Same-observed-route forged flags: the finalizer recomputes identical observed
  model/reasoning identities as `ineffective_equivalent`, overriding forged
  savings flags and producing zero eligibility.

The full six-module template suite independently reran the wider persistent
budget, ambiguity, reservation identity, atomicity, replay, worker closure,
and receipt-integrity matrix.

## Exact-candidate taskset and governance behavior

- Root and packaged `taskset_work_gate.py --check` both pass with zero
  findings on the exact candidate.
- The 12-test taskset suite passes. It verifies that wall-clock-only changes,
  including rolling `Throughput (7d)`, are ignored while task status, task
  addition, active-claim addition, and other record-derived drift still fail.
- Runtime asset, template mirror, managed-host lock, evidence index, T3 plan
  assumptions, and integrated Owner governance all pass.
- Integrated Owner governance emits only non-blocking watch/advisory output
  and exits 0.

## Complete acceptance assessment

- Explicit Scribe, exploration, implementation, review, and audit role policy:
  **passes** at the executable prompt/message boundaries.
- Registered high-tier authorization and separate tier/trigger/provider
  controls: **passes**.
- Immutable execution receipts with requested/resolved/observed routing,
  usage, cost, and source: the mechanical persistence and replay properties
  **pass**.
- Native model-plus-reasoning observation and the original forged
  `unsupported` negatives: **pass**.
- Provider-bound route observation: **fails** because missing, unknown, and
  mismatched unsupported observed providers are accepted.
- Persistent task/claim budgets and pre-provider blocking across restart:
  **passes**.
- Savings unavailable without an observed comparable baseline: **fails** on
  the remaining provider-identity gap.
- Exact-candidate taskset and Owner governance: **passes**.

## Verification commands and outcomes

Every Python/test/gate command was run with:

```text
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u GOOGLE_API_KEY \
    -u GEMINI_API_KEY -u AZURE_OPENAI_API_KEY \
    -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_SESSION_TOKEN
```

Required suites:

- `python -m pytest tests/test_model_routing.py tests/test_task_claim_dispatcher.py tests/test_doctor.py -q`
  -> `107 passed in 27.44s`.
- `python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`
  -> `176 passed in 2.52s`.
- `python -m pytest src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q`
  -> `2 passed in 0.15s`.
- `python -m pytest tests/test_taskset_work_gate.py -q`
  -> `12 passed in 0.48s`.
- `python -m pytest -q`
  -> `2981 passed, 3 skipped, 4 pre-existing UI beta invalid-escape warnings
  in 159.66s`.
- `python -m pytest tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q`
  -> `23 passed in 1.39s`.

Focused and adversarial checks:

- One focused pytest command selected the latest repaired P1 tests plus the
  four earlier boundary samples listed above -> `22 passed in 0.38s`.
- Two credential-sanitized inline Python fixtures directly called
  `subagent_dispatch.render_prompt()`, `emit_call_message()`,
  `eval_harness.record_execution_receipt()`, and `eval_harness.report()`.
  Temporary ledgers and message directories used automatically cleaned
  temporary directories. The exact provider inputs and numeric results are
  recorded in the tables above.

Governance:

- `python scripts/runtime_asset_usage.py --check` -> pass; 38 assets, 404
  uses, 0 blocks, 0 watches.
- `python scripts/template_mirror_gate.py --check` -> 84 expected/common, 81
  identical, 3 intentional, 0 findings.
- `python scripts/regen_host_lock_if_needed.py --check` -> current.
- `python scripts/evidence_index_generator.py --check` -> 0 findings.
- `python scripts/taskset_work_gate.py --check` -> 0 findings.
- `python src/agent_runtime/templates/project/scripts/taskset_work_gate.py --check`
  -> 0 findings.
- `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-V080-OPERABILITY-HARDENING`
  -> 0 findings.
- `python scripts/owner_governance_gate.py` -> exit 0.

Static checks:

- SHA-256 parity is exact for root/template `model_routing.py`,
  `task_claim_dispatcher.py`, and `taskset_work_gate.py`.
- In-memory compilation of all 22 Python files changed across the acceptance
  range passes.
- `git diff --check` passes for the complete acceptance range, focused
  implementation repair, focused candidate range, working tree, and index.
- The post-implementation candidate delta contains only the unit record, T3
  assumptions, review index, canonical VERIFY JSON, and W4a report.

No credential value was read. No live provider, network endpoint, consumer,
dependency installation, account, database, broker, notification, deployment,
remote branch, push, tag, version, publication, or release operation was used.

## Boundary and claim disposition

Only this W4b report was added. No implementation, task/unit record, claim,
handoff, log, board, review index, plan assumption, registry, managed asset,
host lock, consumer project, credential, environment setting, dependency,
provider, account, broker, database, notification, deployment, remote branch,
tag, version, publication, or release state was changed.

`CLAIM-20260730-123600-task-ar-652-ar652001` remains `claimed` and unreleased.
This verifier did not run claim release, closeout, merge, commit, push,
deploy, or publication. A new exact clean candidate needs the provider-identity
repair and a fresh independent W4b before release.
