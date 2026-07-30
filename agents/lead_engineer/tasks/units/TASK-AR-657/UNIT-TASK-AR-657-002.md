---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-657-002
work_uid: 23756cdf-cdfd-4d75-8e98-c320b3a94a28
kind: unit
parent_id: TASK-AR-657
unit_id: UNIT-TASK-AR-657-002
task_id: TASK-AR-657
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
summary: Move live claims out of source history and project compatibility views
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-657-001
  - UNIT-TASK-AR-655-001
escalation_triggers:
context: Claim autocommit protects against reset/clean by creating the cross-session source commits that later sessions treat as unknown work.
inputs:
  - new:scripts/runtime_state_store.py
  - scripts/task_claim_dispatcher.py
  - scripts/claim_guard.py
  - scripts/agent_instance_registry.py
  - scripts/parallel_worktree_gate.py
target_files:
  - scripts/task_claim_dispatcher.py
  - scripts/claim_guard.py
  - scripts/agent_instance_registry.py
  - scripts/parallel_worktree_gate.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_claim_guard.py
  - new:tests/test_agent_instance_registry.py
  - tests/test_parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
scope: Persist live coordination in the control-plane store, disable source-branch claim autocommits, and generate compatibility summaries only through a serialized projection owner. Preserve immutable released evidence where policy requires it.
acceptance:
  - A worker claim cannot create a source commit.
  - All linked worktrees read the same active ownership state.
  - Legacy evidence remains available without being treated as a live lease.
  - Worker branches contain product/work-item changes only.
verification:
  - python -m pytest -q tests/test_task_claim_dispatcher.py tests/test_claim_guard.py tests/test_agent_instance_registry.py tests/test_parallel_worktree_gate.py
handoff: Show unchanged HEAD/status around a complete claim lifecycle and consistent status from two linked worktrees.
stop_condition: Stop before deleting historical claim records or broad repository cleanup.
---

# UNIT-TASK-AR-657-002 - Move live claims out of source history and project compatibility views

## Context

Claim autocommit protects against reset/clean by creating the cross-session source commits that later sessions treat as unknown work.

## Inputs

- new:scripts/runtime_state_store.py
- scripts/task_claim_dispatcher.py
- scripts/claim_guard.py
- scripts/agent_instance_registry.py
- scripts/parallel_worktree_gate.py

## Target Files

- scripts/task_claim_dispatcher.py
- scripts/claim_guard.py
- scripts/agent_instance_registry.py
- scripts/parallel_worktree_gate.py
- tests/test_task_claim_dispatcher.py
- tests/test_claim_guard.py
- new:tests/test_agent_instance_registry.py
- tests/test_parallel_worktree_gate.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py

## Scope

Persist live coordination in the control-plane store, disable source-branch claim autocommits, and generate compatibility summaries only through a serialized projection owner. Preserve immutable released evidence where policy requires it.

## Steps

1. Assert that create, heartbeat, and release leave HEAD and status unchanged.
2. Persist claim lifecycle with session/run identity and fencing.
3. Replace tracked live claim reads with canonical store reads.
4. Provide explicit migration for legacy tracked claims.
5. Make one projection actor responsible for optional tracked summaries.

## Acceptance Criteria

- A worker claim cannot create a source commit.
- All linked worktrees read the same active ownership state.
- Legacy evidence remains available without being treated as a live lease.
- Worker branches contain product/work-item changes only.

## Verification

- `python -m pytest -q tests/test_task_claim_dispatcher.py tests/test_claim_guard.py tests/test_agent_instance_registry.py tests/test_parallel_worktree_gate.py`

## Handoff

Show unchanged HEAD/status around a complete claim lifecycle and consistent status from two linked worktrees.

## Stop Boundary

Stop before deleting historical claim records or broad repository cleanup.
