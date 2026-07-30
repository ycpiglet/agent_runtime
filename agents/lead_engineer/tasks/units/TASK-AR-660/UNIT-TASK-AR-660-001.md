---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-660-001
work_uid: 93993ae8-cdda-4a00-95ad-8639ff606447
kind: unit
parent_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
task_id: TASK-AR-660
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
summary: Persist run steps, effect receipts, retries, and cancellation
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-656-002
  - UNIT-TASK-AR-657-001
  - UNIT-TASK-AR-658-001
escalation_triggers:
context: Current iteration and failure caps are per process. Supervisor restart can repeat a logical step because there is no durable cursor or effect receipt.
inputs:
  - new:scripts/runtime_state_store.py
  - scripts/agent_loop.py
  - scripts/goal_supervisor.py
  - scripts/stop_events.py
  - src/agent_runtime/templates/project/scripts/auto_dispatch.py
target_files:
  - new:scripts/run_step_ledger.py
  - scripts/agent_loop.py
  - scripts/goal_supervisor.py
  - scripts/stop_events.py
  - src/agent_runtime/templates/project/scripts/auto_dispatch.py
  - new:tests/test_run_step_ledger.py
  - new:tests/test_agent_loop.py
  - tests/test_goal_supervisor.py
  - tests/test_stop_events.py
  - src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
  - new:docs/durable-automation-contract.md
scope: Persist intent, lease, attempt, receipt, result, retry, cancellation, and compensation metadata for logical steps. Do not directly implement provider-specific irreversible actions.
acceptance:
  - Crash-after-effect-before-result does not repeat the effect when a receipt exists.
  - Concurrent duplicate dispatch elects one step lease owner.
  - Retry exhaustion is durable and cannot reset with a new process.
  - Non-reversible effects carry an explicit recovery or compensation pointer.
verification:
  - python -m pytest -q tests/test_run_step_ledger.py tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_stop_events.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
handoff: Attach crash-window, duplicate-dispatch, retry-budget, no-progress, and cancellation traces.
stop_condition: Stop before enabling any new external side effect by default.
---

# UNIT-TASK-AR-660-001 - Persist run steps, effect receipts, retries, and cancellation

## Context

Current iteration and failure caps are per process. Supervisor restart can repeat a logical step because there is no durable cursor or effect receipt.

## Inputs

- new:scripts/runtime_state_store.py
- scripts/agent_loop.py
- scripts/goal_supervisor.py
- scripts/stop_events.py
- src/agent_runtime/templates/project/scripts/auto_dispatch.py

## Target Files

- new:scripts/run_step_ledger.py
- scripts/agent_loop.py
- scripts/goal_supervisor.py
- scripts/stop_events.py
- src/agent_runtime/templates/project/scripts/auto_dispatch.py
- new:tests/test_run_step_ledger.py
- new:tests/test_agent_loop.py
- tests/test_goal_supervisor.py
- tests/test_stop_events.py
- src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
- new:docs/durable-automation-contract.md

## Scope

Persist intent, lease, attempt, receipt, result, retry, cancellation, and compensation metadata for logical steps. Do not directly implement provider-specific irreversible actions.

## Steps

1. Define idempotency as run ID, scope revision, and logical step ID.
2. Write intent before an effect and reconcile a receipt before retry.
3. Track attempt, time, cost, and token budgets across processes.
4. Add exponential backoff with jitter and no-progress detection.
5. Cascade cancellation to children and queued effects.

## Acceptance Criteria

- Crash-after-effect-before-result does not repeat the effect when a receipt exists.
- Concurrent duplicate dispatch elects one step lease owner.
- Retry exhaustion is durable and cannot reset with a new process.
- Non-reversible effects carry an explicit recovery or compensation pointer.

## Verification

- `python -m pytest -q tests/test_run_step_ledger.py tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_stop_events.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py`

## Handoff

Attach crash-window, duplicate-dispatch, retry-budget, no-progress, and cancellation traces.

## Stop Boundary

Stop before enabling any new external side effect by default.
