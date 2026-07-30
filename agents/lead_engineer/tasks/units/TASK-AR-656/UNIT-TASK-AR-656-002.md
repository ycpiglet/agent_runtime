---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-656-002
work_uid: d7152983-3777-415e-a220-d504d41e2e2f
kind: unit
parent_id: TASK-AR-656
unit_id: UNIT-TASK-AR-656-002
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
summary: Resume the exact run and stop on frozen completion
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-656-001
escalation_triggers:
context: agent_loop carries a raw string and goal_supervisor finds the latest goal in a shared daily log. Concurrent sessions can therefore resume the wrong work or continue into generic inbox messages.
inputs:
  - new:scripts/execution_scope.py
  - scripts/agent_loop.py
  - scripts/goal_supervisor.py
  - scripts/stop_events.py
target_files:
  - scripts/agent_loop.py
  - scripts/goal_supervisor.py
  - scripts/stop_events.py
  - new:tests/test_agent_loop.py
  - tests/test_goal_supervisor.py
  - tests/test_stop_events.py
  - src/agent_runtime/templates/project/scripts/agent_loop.py
scope: Bind loop start, dispatch, stop events, restart counts, and completion to run ID and scope revision. Preserve a read-only compatibility report for legacy raw-goal events.
acceptance:
  - Identical goal text cannot cross-resume another run.
  - Restart counters are per run rather than per text.
  - New backlog after completion does not re-arm the completed run.
verification:
  - python -m pytest -q tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_stop_events.py
handoff: Show two same-text runs remaining isolated across stop and restart.
stop_condition: Stop before implementing durable effect idempotency or session SCM enforcement.
---

# UNIT-TASK-AR-656-002 - Resume the exact run and stop on frozen completion

## Context

agent_loop carries a raw string and goal_supervisor finds the latest goal in a shared daily log. Concurrent sessions can therefore resume the wrong work or continue into generic inbox messages.

## Inputs

- new:scripts/execution_scope.py
- scripts/agent_loop.py
- scripts/goal_supervisor.py
- scripts/stop_events.py

## Target Files

- scripts/agent_loop.py
- scripts/goal_supervisor.py
- scripts/stop_events.py
- new:tests/test_agent_loop.py
- tests/test_goal_supervisor.py
- tests/test_stop_events.py
- src/agent_runtime/templates/project/scripts/agent_loop.py

## Scope

Bind loop start, dispatch, stop events, restart counts, and completion to run ID and scope revision. Preserve a read-only compatibility report for legacy raw-goal events.

## Steps

1. Write two-session fixtures with identical goal text and different run IDs.
2. Pass exact run identity through loop events and dispatch.
3. Remove generic inbox consumption from run-bound execution.
4. Resume only if run identity, revision, digest, and lease status still match.
5. Stop at frozen completion and report later discoveries separately.

## Acceptance Criteria

- Identical goal text cannot cross-resume another run.
- Restart counters are per run rather than per text.
- New backlog after completion does not re-arm the completed run.

## Verification

- `python -m pytest -q tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_stop_events.py`

## Handoff

Show two same-text runs remaining isolated across stop and restart.

## Stop Boundary

Stop before implementing durable effect idempotency or session SCM enforcement.
