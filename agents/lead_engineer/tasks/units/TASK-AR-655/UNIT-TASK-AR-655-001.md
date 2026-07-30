---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-655-001
work_uid: 14c6a516-785f-4295-b100-9e1cae07fb5a
kind: unit
parent_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_id: TASK-AR-655
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
summary: Implement immutable GoalRun storage and membership hashing
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-657-001
escalation_triggers:
context: The current loop stores only raw goal text while wave dispatch resolves the live taskset on every invocation. A run needs a durable identity and sealed membership before any writer claim is created.
inputs:
  - reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
  - new:scripts/runtime_state_store.py
  - scripts/agent_loop.py
  - scripts/wave_dispatcher.py
  - agents/project/WORK-SCHEMA.yml
target_files:
  - new:scripts/execution_scope.py
  - new:tests/test_execution_scope.py
  - agents/project/WORK-SCHEMA.yml
  - src/agent_runtime/templates/project/agents/project/WORK-SCHEMA.yml
  - tests/fixtures/host/agent_runtime.lock.json
scope: Define GoalRun, immutable membership snapshots, deterministic digests, base SHA, budgets, completion predicates, and atomic local persistence. Do not wire dispatch or session leases in this unit.
acceptance:
  - The same inputs produce the same membership digest.
  - A live registry addition does not change an existing run record.
  - Corrupt or partially written state fails closed.
  - Run identity is independent from human-readable goal text.
verification:
  - python -m pytest -q tests/test_execution_scope.py
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Provide the GoalRun schema, persistence location, digest fixtures, and before/after proof that a newly added unit is excluded.
stop_condition: Stop before changing dispatch, claim acquisition, or Git behavior.
---

# UNIT-TASK-AR-655-001 - Implement immutable GoalRun storage and membership hashing

## Context

The current loop stores only raw goal text while wave dispatch resolves the live taskset on every invocation. A run needs a durable identity and sealed membership before any writer claim is created.

## Inputs

- reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
- new:scripts/runtime_state_store.py
- scripts/agent_loop.py
- scripts/wave_dispatcher.py
- agents/project/WORK-SCHEMA.yml

## Target Files

- new:scripts/execution_scope.py
- new:tests/test_execution_scope.py
- agents/project/WORK-SCHEMA.yml
- src/agent_runtime/templates/project/agents/project/WORK-SCHEMA.yml
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Define GoalRun, immutable membership snapshots, deterministic digests, base SHA, budgets, completion predicates, and atomic local persistence. Do not wire dispatch or session leases in this unit.

## Steps

1. Write failure-first tests for task and unit additions after scope sealing.
2. Define versioned GoalRun and ScopeChangeRequest schemas.
3. Resolve exact membership and hash normalized work-item identity and unit-spec inputs.
4. Persist start, status, and close transitions through the canonical runtime-state adapter.
5. Document compatibility behavior for a raw goal that has no sealed run.

## Acceptance Criteria

- The same inputs produce the same membership digest.
- A live registry addition does not change an existing run record.
- Corrupt or partially written state fails closed.
- Run identity is independent from human-readable goal text.

## Verification

- `python -m pytest -q tests/test_execution_scope.py`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Provide the GoalRun schema, persistence location, digest fixtures, and before/after proof that a newly added unit is excluded.

## Stop Boundary

Stop before changing dispatch, claim acquisition, or Git behavior.
