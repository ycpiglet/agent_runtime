---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-594-001
work_uid: 28998ec6-2ff6-44a1-9b27-74c6c5360598
kind: unit
parent_id: TASK-AR-594
unit_id: UNIT-TASK-AR-594-001
task_id: TASK-AR-594
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T10:28:06+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:#274,#279,#280,#285,#287,#289,#290; pr:#277
created_by: codex-root-planner
summary: Implement canonical task order selection
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - high_risk
  - cross_cutting
  - data_integrity
context: Autofolio reproduced GitHub #289 on agent_runtime v0.6.0: canonical taskset prose orders TASK-219, TASK-220, TASK-217, but _tasks_for discards that order and picks TASK-217 by score.
inputs:
  - https://github.com/ycpiglet/agent_runtime/issues/289
  - scripts/taskset_dispatcher.py
  - tests/test_taskset_dispatcher.py
target_files:
  - scripts/taskset_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
  - tests/test_taskset_dispatcher.py
  - tests/test_role_routing_wiring.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Parse an authoritative ordered task list from the canonical taskset record, use it before fallback score ordering, mirror the implementation, and add regression coverage.
acceptance:
  - The reported three-task reproduction selects TASK-219 first and preserves the full declared order.
  - Missing, duplicated, or unrelated task IDs cannot silently reorder valid tasks.
  - Focused dispatcher tests pass.
verification:
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_role_routing_wiring.py -q
handoff: Provide changed-file summary, before/after selection evidence, focused test output, and any fallback compatibility note.
stop_condition: Stop if canonical order cannot be derived without changing the taskset record contract; escalate with the conflicting record examples.
---

# UNIT-TASK-AR-594-001 - Implement canonical task order selection

## Context

Autofolio reproduced GitHub #289 on agent_runtime v0.6.0: canonical taskset prose orders TASK-219, TASK-220, TASK-217, but _tasks_for discards that order and picks TASK-217 by score.

## Inputs

- https://github.com/ycpiglet/agent_runtime/issues/289
- scripts/taskset_dispatcher.py
- tests/test_taskset_dispatcher.py

## Target Files

- scripts/taskset_dispatcher.py
- src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
- tests/test_taskset_dispatcher.py
- tests/test_role_routing_wiring.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Parse an authoritative ordered task list from the canonical taskset record, use it before fallback score ordering, mirror the implementation, and add regression coverage.

## Steps

1. Add a deterministic canonical-order parser with unambiguous task ID matching.
2. Thread canonical order into task selection without changing fallback semantics.
3. Add reproduction and fallback regression tests, then refresh the host fixture lock if needed.

## Acceptance Criteria

- The reported three-task reproduction selects TASK-219 first and preserves the full declared order.
- Missing, duplicated, or unrelated task IDs cannot silently reorder valid tasks.
- Focused dispatcher tests pass.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py tests/test_role_routing_wiring.py -q`

## Handoff

Provide changed-file summary, before/after selection evidence, focused test output, and any fallback compatibility note.

## Stop Boundary

Stop if canonical order cannot be derived without changing the taskset record contract; escalate with the conflicting record examples.
