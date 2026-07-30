---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-656-001
work_uid: 798b02b4-cbec-4877-bf5e-451861164a8c
kind: unit
parent_id: TASK-AR-656
unit_id: UNIT-TASK-AR-656-001
task_id: TASK-AR-656
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Select and claim only frozen goal-run members
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-655-002
  - UNIT-TASK-AR-657-002
escalation_triggers:
context: wave_dispatcher currently re-enumerates every current unit in a taskset. The taskset boundary gate is repository-global and only activates after completion.
inputs:
  - new:scripts/execution_scope.py
  - scripts/wave_dispatcher.py
  - scripts/task_claim_dispatcher.py
  - scripts/taskset_boundary_gate.py
target_files:
  - scripts/wave_dispatcher.py
  - scripts/task_claim_dispatcher.py
  - scripts/taskset_boundary_gate.py
  - tests/test_wave_dispatcher.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_taskset_boundary_gate.py
  - src/agent_runtime/templates/project/scripts/wave_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_boundary_gate.py
scope: Add run and scope-revision inputs, select manifest IDs instead of live taskset membership, and validate scope digest before claim creation. Do not add session fencing yet.
acceptance:
  - Later work never enters the frozen wave.
  - Unrelated goal runs cannot block each other's boundary checks.
  - A stale or mismatched digest fails closed before a claim file or event exists.
verification:
  - python -m pytest -q tests/test_wave_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_taskset_boundary_gate.py
handoff: Attach the late-unit and cross-goal regressions plus the manifest-based wave plan.
stop_condition: Stop before moving runtime state storage or changing Git operations.
---

# UNIT-TASK-AR-656-001 - Select and claim only frozen goal-run members

## Context

wave_dispatcher currently re-enumerates every current unit in a taskset. The taskset boundary gate is repository-global and only activates after completion.

## Inputs

- new:scripts/execution_scope.py
- scripts/wave_dispatcher.py
- scripts/task_claim_dispatcher.py
- scripts/taskset_boundary_gate.py

## Target Files

- scripts/wave_dispatcher.py
- scripts/task_claim_dispatcher.py
- scripts/taskset_boundary_gate.py
- tests/test_wave_dispatcher.py
- tests/test_task_claim_dispatcher.py
- tests/test_taskset_boundary_gate.py
- src/agent_runtime/templates/project/scripts/wave_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/taskset_boundary_gate.py

## Scope

Add run and scope-revision inputs, select manifest IDs instead of live taskset membership, and validate scope digest before claim creation. Do not add session fencing yet.

## Steps

1. Reproduce a unit added after scope sealing entering the next wave.
2. Plan from the sealed unit list and classify later units as discovered-after-scope.
3. Require run ID, revision, and digest on mutating claims.
4. Key boundary decisions by run and session rather than every repository claim.
5. Add template parity coverage.

## Acceptance Criteria

- Later work never enters the frozen wave.
- Unrelated goal runs cannot block each other's boundary checks.
- A stale or mismatched digest fails closed before a claim file or event exists.

## Verification

- `python -m pytest -q tests/test_wave_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_taskset_boundary_gate.py`

## Handoff

Attach the late-unit and cross-goal regressions plus the manifest-based wave plan.

## Stop Boundary

Stop before moving runtime state storage or changing Git operations.
