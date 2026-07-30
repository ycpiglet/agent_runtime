---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-655-001
work_uid: 250178c6-8aed-4bc0-855b-ab140bf44268
kind: unit
parent_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_id: TASK-AR-655
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T12:00:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Unify task-claim renewal and expiry consumers
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: TASK-AR-650 continued well beyond its 30-minute lease, but the task claim dispatcher has only create, projection, and release commands. The separate low-level claim lease heartbeat is not connected to task claim JSON.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/claim_lease.py
  - src/agent_runtime/templates/project/scripts/state_sync_gate.py
target_files:
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/agent_orchestrator.py
  - src/agent_runtime/templates/project/scripts/state_sync_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/worktree_lifecycle_gate.py
  - src/agent_runtime/ui_state.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_state_sync_gate.py
  - tests/test_parallel_worktree_gate.py
  - tests/test_worktree_lifecycle_gate.py
  - tests/test_ui_state.py
scope: Unify local lifecycle timestamps without creating a remote lease service.
acceptance:
  - Long tasks can remain legitimately active.
  - Stale workers cannot revive another owner's claim.
  - Replan renewal records old and new task, unit, target-file, and stop-boundary digests and cannot silently broaden scope.
  - Every surface agrees on active versus expired.
  - Renewal never commits or pushes host Git state.
verification:
  - python -m pytest tests/test_task_claim_dispatcher.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py -q
handoff: Attach the atomicity tests, owner mismatch, crash/restart, replan old/new scope digest proof, cross-consumer expiry matrix, and independent W4b.
stop_condition: Stop before introducing a network lease dependency, auto-committing host state, or recovering a claim without owner identity.
---

# UNIT-TASK-AR-655-001 - Unify task-claim renewal and expiry consumers

## Context

TASK-AR-650 continued well beyond its 30-minute lease, but the task claim dispatcher has only create, projection, and release commands. The separate low-level claim lease heartbeat is not connected to task claim JSON.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/claim_lease.py
- src/agent_runtime/templates/project/scripts/state_sync_gate.py

## Target Files

- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/agent_orchestrator.py
- src/agent_runtime/templates/project/scripts/state_sync_gate.py
- src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
- src/agent_runtime/templates/project/scripts/worktree_lifecycle_gate.py
- src/agent_runtime/ui_state.py
- tests/test_task_claim_dispatcher.py
- tests/test_state_sync_gate.py
- tests/test_parallel_worktree_gate.py
- tests/test_worktree_lifecycle_gate.py
- tests/test_ui_state.py

## Scope

Unify local lifecycle timestamps without creating a remote lease service.

## Steps

1. Add expiry and concurrent-renewal negative fixtures.
2. Implement atomic owner-checked heartbeat and renewal.
3. Wire orchestrator progress to the same mutation.
4. Adopt one expiry classifier in all read consumers.
5. Verify crash and restart behavior.

## Acceptance Criteria

- Long tasks can remain legitimately active.
- Stale workers cannot revive another owner's claim.
- Every surface agrees on active versus expired.
- Renewal never commits or pushes host Git state.

## Verification

- `python -m pytest tests/test_task_claim_dispatcher.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py -q`

## Handoff

Attach the atomicity tests, owner mismatch, crash/restart, cross-consumer expiry matrix, and independent W4b.

## Stop Boundary

Stop before introducing a network lease dependency, auto-committing host state, or recovering a claim without owner identity.
