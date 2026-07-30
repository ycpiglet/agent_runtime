---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-659-001
work_uid: f7244ef2-9748-40eb-bb4f-b51e5593897d
kind: unit
parent_id: TASK-AR-659
unit_id: UNIT-TASK-AR-659-001
task_id: TASK-AR-659
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
summary: Enforce planned and actual ownership across files and domains
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-656-001
  - UNIT-TASK-AR-657-002
escalation_triggers:
context: Empty target_files currently warn, file footprints miss semantic conflicts, and isolated taskset views can overlook global dependency state.
inputs:
  - scripts/footprint_conflict_gate.py
  - scripts/task_claim_dispatcher.py
  - scripts/task_unit_readiness_gate.py
  - scripts/wave_dispatcher.py
  - scripts/state_sync_gate.py
target_files:
  - scripts/footprint_conflict_gate.py
  - scripts/task_claim_dispatcher.py
  - scripts/task_unit_readiness_gate.py
  - scripts/wave_dispatcher.py
  - scripts/state_sync_gate.py
  - tests/test_footprint_conflict_gate.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_task_unit_readiness_gate.py
  - tests/test_wave_dispatcher.py
  - tests/test_state_sync_gate.py
scope: Require explicit file and semantic footprints, validate actual diffs at release/integration, and resolve dependencies against canonical global state. Preserve read-only/research exemptions with explicit claim mode.
acceptance:
  - Read-only work can run without a write footprint only when explicitly classified read-only.
  - A semantic collision is detected before either worker writes.
  - Release cannot pass when actual files exceed the lease.
  - A dependency completed in another taskset is recognized without importing its branch.
verification:
  - python -m pytest -q tests/test_footprint_conflict_gate.py tests/test_task_claim_dispatcher.py tests/test_task_unit_readiness_gate.py tests/test_wave_dispatcher.py tests/test_state_sync_gate.py
handoff: Provide path, domain, generated-surface, and global-dependency conflict fixtures.
stop_condition: Stop before changing protected remote branch policy.
---

# UNIT-TASK-AR-659-001 - Enforce planned and actual ownership across files and domains

## Context

Empty target_files currently warn, file footprints miss semantic conflicts, and isolated taskset views can overlook global dependency state.

## Inputs

- scripts/footprint_conflict_gate.py
- scripts/task_claim_dispatcher.py
- scripts/task_unit_readiness_gate.py
- scripts/wave_dispatcher.py
- scripts/state_sync_gate.py

## Target Files

- scripts/footprint_conflict_gate.py
- scripts/task_claim_dispatcher.py
- scripts/task_unit_readiness_gate.py
- scripts/wave_dispatcher.py
- scripts/state_sync_gate.py
- tests/test_footprint_conflict_gate.py
- tests/test_task_claim_dispatcher.py
- tests/test_task_unit_readiness_gate.py
- tests/test_wave_dispatcher.py
- tests/test_state_sync_gate.py

## Scope

Require explicit file and semantic footprints, validate actual diffs at release/integration, and resolve dependencies against canonical global state. Preserve read-only/research exemptions with explicit claim mode.

## Steps

1. Turn footprint-less mutating claims from warning to blocking.
2. Add normalized semantic-domain declarations and atomic acquisition.
3. Compute actual base-to-HEAD and dirty footprints and reject escape.
4. Resolve dependency completion from canonical work and claim state.
5. Reserve generated shared surfaces for the projection owner.

## Acceptance Criteria

- Read-only work can run without a write footprint only when explicitly classified read-only.
- A semantic collision is detected before either worker writes.
- Release cannot pass when actual files exceed the lease.
- A dependency completed in another taskset is recognized without importing its branch.

## Verification

- `python -m pytest -q tests/test_footprint_conflict_gate.py tests/test_task_claim_dispatcher.py tests/test_task_unit_readiness_gate.py tests/test_wave_dispatcher.py tests/test_state_sync_gate.py`

## Handoff

Provide path, domain, generated-surface, and global-dependency conflict fixtures.

## Stop Boundary

Stop before changing protected remote branch policy.
