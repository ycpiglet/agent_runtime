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
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Add effective-tier detection and dispatch cost ledger
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Codex haiku, sonnet, and opus tiers currently resolve to the same default model, so the policy records different labels without reducing token cost.
inputs:
  - scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/subagent_dispatch.py
target_files:
  - scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/subagent_dispatch.py
  - src/agent_runtime/doctor.py
  - tests/test_model_routing.py
  - tests/test_role_routing.py
  - tests/test_role_routing_wiring.py
scope: Resolve configured provider models, flag ineffective tiers, and append dispatch/usage records. Do not embed provider credentials or implement a separate agent executor.
acceptance:
  - Same-model tiers cannot be reported as savings.
  - Low-cost routing is the default for worker-ready routine units.
  - Critical or failed work records a visible escalation.
  - Missing usage telemetry is marked unverified, not zero.
verification:
  - python -m pytest tests/test_model_routing.py tests/test_role_routing.py tests/test_role_routing_wiring.py -q
handoff: Provide routing matrices for Claude and Codex plus sample dispatch ledger records.
stop_condition: Stop before hardcoding an unverified current model catalog or storing API secrets.
---

# UNIT-TASK-AR-646-001 - Add effective-tier detection and dispatch cost ledger

## Context

Codex haiku, sonnet, and opus tiers currently resolve to the same default model, so the policy records different labels without reducing token cost.

## Inputs

- scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/subagent_dispatch.py

## Target Files

- scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/subagent_dispatch.py
- src/agent_runtime/doctor.py
- tests/test_model_routing.py
- tests/test_role_routing.py
- tests/test_role_routing_wiring.py

## Scope

Resolve configured provider models, flag ineffective tiers, and append dispatch/usage records. Do not embed provider credentials or implement a separate agent executor.

## Steps

1. Detect effective tier-to-model equivalence.
2. Add routing status to doctor.
3. Record dispatch decision and escalation reason.
4. Ingest actual token/cost/latency when the provider exposes it.

## Acceptance Criteria

- Same-model tiers cannot be reported as savings.
- Low-cost routing is the default for worker-ready routine units.
- Critical or failed work records a visible escalation.
- Missing usage telemetry is marked unverified, not zero.

## Verification

- `python -m pytest tests/test_model_routing.py tests/test_role_routing.py tests/test_role_routing_wiring.py -q`

## Handoff

Provide routing matrices for Claude and Codex plus sample dispatch ledger records.

## Stop Boundary

Stop before hardcoding an unverified current model catalog or storing API secrets.
