---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-646-001
work_uid: 7e7603e3-6d8f-4b19-88bc-7f2316b336cb
kind: unit
parent_id: TASK-AR-646
unit_id: UNIT-TASK-AR-646-001
task_id: TASK-AR-646
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T08:14:17+09:00
started_at: 2026-07-29T06:42:09+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Add provider-aware routing, native dispatch proof, and truthful usage telemetry
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-064209-task-ar-646-0823.json
context: Codex API haiku, sonnet, and opus tiers resolve to one model; registration defaults and fabricated ambiguity defeat low-cost routing; provider workers and the native Codex bridge do not prove the observed model or cost.
inputs:
  - scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/subagent_dispatch.py
  - src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py
  - src/agent_runtime/templates/project/scripts/agent_worker.py
  - src/agent_runtime/templates/project/scripts/auto_dispatch.py
  - src/agent_runtime/templates/project/scripts/eval_harness.py
  - reviews/REVIEW-2026-07-29-task-ar-646-w0-t3-replan.md
target_files:
  - scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/model_routing.py
  - scripts/work.py
  - src/agent_runtime/templates/project/scripts/work.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/subagent_dispatch.py
  - src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py
  - src/agent_runtime/templates/project/scripts/agent_worker.py
  - src/agent_runtime/templates/project/scripts/auto_dispatch.py
  - src/agent_runtime/templates/project/scripts/eval_harness.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/templates/project/docs/agent_bootstrap/codex.md
  - src/agent_runtime/templates/project/agents/lead_engineer/TOKEN-BUDGET.md
  - tests/test_model_routing.py
  - tests/test_work_registration.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_doctor.py
  - tests/test_role_routing.py
  - tests/test_role_routing_wiring.py
  - tests/test_provider_import_contract.py
  - tests/test_template_smoke.py
  - src/agent_runtime/templates/project/scripts/test_model_routing.py
  - src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py
  - src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py
  - new:src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py
  - src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
  - src/agent_runtime/templates/project/scripts/test_eval_harness.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Make routine registration low-cost, resolve configured provider/native models, enforce deterministic-first delegation, flag ineffective tiers, and append truthful dispatch/completion telemetry. Do not embed credentials, synthesize prices, create a shared budget authority, or implement a separate agent executor.
acceptance:
  - Same-model tiers cannot be reported as savings.
  - New precise routine task/unit registrations default to worker_low without fabricated risk triggers.
  - Claim creation derives and records requested versus selected tier; data-integrity and other registered high-risk signals visibly escalate.
  - A read-only explorer role and precise implementer default to lower-cost native routing; higher-risk roles retain stronger defaults.
  - Lookup-only dispatch is blocked until deterministic preflight is sufficient or recorded insufficient.
  - Generic, provider-worker, auto-dispatch, and native bridge events share dispatch correlation and routing/usage status fields.
  - Missing model, token, latency, or billed-cost telemetry is marked unverified/unavailable, not zero or inferred.
  - Token delta is not described as monetary cost savings without comparable billed-cost evidence.
verification:
  - python -m pytest tests/test_model_routing.py tests/test_work_registration.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_provider_import_contract.py tests/test_template_smoke.py -q
  - python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q
  - python scripts/runtime_asset_usage.py --check
  - python -m pytest -q
handoff: Provide Claude, Codex API, and native Codex routing matrices; deterministic-preflight failures; sample dispatch/completion records; and token-versus-billed-cost reporting examples.
stop_condition: Stop before live billable calls, unverified economic claims, provider credential storage, global Codex config changes, a shared persistent budget authority, consumer mutation, or release/version operations.
verified_at: 2026-07-29T07:28:48+09:00
verified_by: le-20260729-kst-646001
evidence_refs:
  - reviews/VERIFY-2026-07-29-unit-task-ar-646-001-20260729072848.json
review_refs:
  - reviews/W4B-2026-07-29-unit-task-ar-646-001.md
compound_refs:
  - agents/project/knowledge/compounds/records/COMPOUND-20260729-081348-temp-git-fixture-head-corruption-survives-bounde-2514bdcf5f65.json
defect_signatures:
  - defect:ci-flaky-temp-git:d1ff9421d45168c6
resolution: done
completed_at: 2026-07-29T08:14:17+09:00
closed_by: codex-root-v080-orchestrator
measurement_unavailable_reason: Exact per-unit hours and token telemetry were not captured; no live provider usage occurred and completion telemetry remained unavailable where the provider did not report it.
---

# UNIT-TASK-AR-646-001 - Add provider-aware routing and dispatch telemetry

## Context

Codex API haiku, sonnet, and opus tiers currently resolve to one model.
Registration defaults and fabricated ambiguity also defeat routine low-cost
routing. Provider workers and the native Codex bridge do not prove the observed
model, latency, usage, or billed cost.

## Inputs

- scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/subagent_dispatch.py
- src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py
- src/agent_runtime/templates/project/scripts/agent_worker.py
- src/agent_runtime/templates/project/scripts/auto_dispatch.py
- src/agent_runtime/templates/project/scripts/eval_harness.py
- reviews/REVIEW-2026-07-29-task-ar-646-w0-t3-replan.md

## Target Files

- scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/model_routing.py
- scripts/work.py
- src/agent_runtime/templates/project/scripts/work.py
- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/subagent_dispatch.py
- src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py
- src/agent_runtime/templates/project/scripts/agent_worker.py
- src/agent_runtime/templates/project/scripts/auto_dispatch.py
- src/agent_runtime/templates/project/scripts/eval_harness.py
- src/agent_runtime/doctor.py
- src/agent_runtime/templates/project/docs/agent_bootstrap/codex.md
- src/agent_runtime/templates/project/agents/lead_engineer/TOKEN-BUDGET.md
- tests/test_model_routing.py
- tests/test_work_registration.py
- tests/test_task_claim_dispatcher.py
- tests/test_doctor.py
- tests/test_role_routing.py
- tests/test_role_routing_wiring.py
- tests/test_provider_import_contract.py
- tests/test_template_smoke.py
- src/agent_runtime/templates/project/scripts/test_model_routing.py
- src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py
- src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py
- new:src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py
- src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
- src/agent_runtime/templates/project/scripts/test_eval_harness.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Make routine registration low-cost, resolve configured provider/native models,
enforce deterministic-first delegation, flag ineffective tiers, and append
truthful dispatch/completion telemetry. Do not embed credentials, synthesize
prices, create a shared budget authority, or implement a separate agent
executor.

## Steps

1. Correct routine registration defaults and claim-time escalation resolution.
2. Detect provider/native tier-to-model equivalence with model-source
   provenance.
3. Add deterministic preflight and a low-cost read-only explorer route.
4. Carry exact native spawn arguments and completion observations through the
   Codex bridge.
5. Record provider-worker and native dispatch/completion telemetry.
6. Separate token deltas, unavailable billed cost, and verified monetary
   evidence.
7. Add routing status and equivalence warnings to doctor.

## Acceptance Criteria

- Same-model tiers cannot be reported as savings.
- New precise routine task/unit registrations default to `worker_low` without
  fabricated risk triggers.
- Claim creation derives and records requested versus selected tier;
  data-integrity and other registered high-risk signals visibly escalate.
- A read-only explorer role and precise implementer default to lower-cost
  native routing; higher-risk roles retain stronger defaults.
- Lookup-only dispatch is blocked until deterministic preflight is sufficient
  or recorded insufficient.
- Generic, provider-worker, auto-dispatch, and native bridge events share
  dispatch correlation and routing/usage status fields.
- Missing model, token, latency, or billed-cost telemetry is marked
  unverified/unavailable, not zero or inferred.
- Token delta is not described as monetary cost savings without comparable
  billed-cost evidence.

## Verification

- `python -m pytest tests/test_model_routing.py tests/test_work_registration.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_provider_import_contract.py tests/test_template_smoke.py -q`
- `python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python -m pytest -q`

## Handoff

Provide Claude, Codex API, and native Codex routing matrices; deterministic
preflight failures; sample dispatch/completion records; and
token-versus-billed-cost reporting examples.

## Stop Boundary

Stop before live billable calls, unverified economic claims, provider credential
storage, global Codex config changes, a shared persistent budget authority,
consumer mutation, or release/version operations.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-29T08:14:17+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Exact per-unit hours and token telemetry were not captured; no live provider usage occurred and completion telemetry remained unavailable where the provider did not report it.
- Closed by: `codex-root-v080-orchestrator`
- Verification evidence:
  - `reviews/VERIFY-2026-07-29-unit-task-ar-646-001-20260729072848.json`
- Reviews:
  - `reviews/W4B-2026-07-29-unit-task-ar-646-001.md`
- Compounds:
  - `agents/project/knowledge/compounds/records/COMPOUND-20260729-081348-temp-git-fixture-head-corruption-survives-bounde-2514bdcf5f65.json`
<!-- work-close:end -->
