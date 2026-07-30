---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-663-001
work_uid: b3dcba7f-ddce-48e8-97c3-1056749930be
kind: unit
parent_id: TASK-AR-663
unit_id: UNIT-TASK-AR-663-001
task_id: TASK-AR-663
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
summary: Run chaos scenarios, migrate state, and stage enforcement
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-658-002
  - UNIT-TASK-AR-660-001
  - UNIT-TASK-AR-661-001
  - UNIT-TASK-AR-662-001
escalation_triggers:
context: The safety model spans scope, leases, Git, loops, integration, and verification. Unit tests alone cannot prove the absence of reciprocal blocking or duplicated effects.
inputs:
  - reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
  - new:scripts/runtime_state_store.py
  - new:scripts/execution_scope.py
  - new:scripts/session_scm_guard.py
  - new:scripts/run_step_ledger.py
target_files:
  - new:tests/test_parallel_session_isolation.py
  - new:tests/test_bounded_goal_scope.py
  - new:tests/test_runtime_chaos.py
  - new:tests/test_control_plane_migration.py
  - new:tests/test_enforcement_rollout.py
  - new:scripts/control_plane_migration.py
  - new:scripts/enforcement_rollout.py
  - scripts/owner_governance_gate.py
  - new:docs/autonomous-execution-rollout.md
  - new:docs/runbooks/session-isolation-recovery.md
scope: Exercise real concurrent processes and temporary linked worktrees, migrate legacy coordination state, and define shadow-to-block rollout with telemetry and rollback. Do not enable blocking in consumer repositories until exit criteria pass.
acceptance:
  - A clean session closes while an unrelated sibling worktree is dirty.
  - Only one simultaneous same-scope claimant or step executor succeeds.
  - A late task never enters a sealed run.
  - Crash recovery neither duplicates effects nor accepts stale writes.
  - Rollout metrics and recovery runbook are sufficient for an operator to reverse enforcement safely.
verification:
  - python -m pytest -q tests/test_parallel_session_isolation.py tests/test_bounded_goal_scope.py tests/test_runtime_chaos.py tests/test_control_plane_migration.py tests/test_enforcement_rollout.py
  - python scripts/regen_host_lock_if_needed.py --check
  - python -m pytest -q tests/test_template_smoke.py
  - python scripts/owner_governance_gate.py
handoff: Attach the chaos matrix, pre/post failure traces, migration report, shadow metrics, and staged rollout decision.
stop_condition: Stop before broad hard enforcement if any P0 race, false-positive ownership block, or rollback data-loss case remains.
---

# UNIT-TASK-AR-663-001 - Run chaos scenarios, migrate state, and stage enforcement

## Context

The safety model spans scope, leases, Git, loops, integration, and verification. Unit tests alone cannot prove the absence of reciprocal blocking or duplicated effects.

## Inputs

- reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
- new:scripts/runtime_state_store.py
- new:scripts/execution_scope.py
- new:scripts/session_scm_guard.py
- new:scripts/run_step_ledger.py

## Target Files

- new:tests/test_parallel_session_isolation.py
- new:tests/test_bounded_goal_scope.py
- new:tests/test_runtime_chaos.py
- new:tests/test_control_plane_migration.py
- new:tests/test_enforcement_rollout.py
- new:scripts/control_plane_migration.py
- new:scripts/enforcement_rollout.py
- scripts/owner_governance_gate.py
- new:docs/autonomous-execution-rollout.md
- new:docs/runbooks/session-isolation-recovery.md

## Scope

Exercise real concurrent processes and temporary linked worktrees, migrate legacy coordination state, and define shadow-to-block rollout with telemetry and rollback. Do not enable blocking in consumer repositories until exit criteria pass.

## Steps

1. Reproduce reciprocal unknown-change blocking and duplicate claim/effect races.
2. Inject process death at lease, effect, verification, and protected-update boundaries.
3. Test late registration, sibling dirt, base advancement, stale fencing, and incompatible design domains.
4. Migrate legacy tracked state as historical evidence rather than active ownership.
5. Run observe, warn, block-new, and block-all stages with explicit exit and rollback criteria.

## Acceptance Criteria

- A clean session closes while an unrelated sibling worktree is dirty.
- Only one simultaneous same-scope claimant or step executor succeeds.
- A late task never enters a sealed run.
- Crash recovery neither duplicates effects nor accepts stale writes.
- Rollout metrics and recovery runbook are sufficient for an operator to reverse enforcement safely.

## Verification

- `python -m pytest -q tests/test_parallel_session_isolation.py tests/test_bounded_goal_scope.py tests/test_runtime_chaos.py tests/test_control_plane_migration.py tests/test_enforcement_rollout.py`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python -m pytest -q tests/test_template_smoke.py`
- `python scripts/owner_governance_gate.py`

## Handoff

Attach the chaos matrix, pre/post failure traces, migration report, shadow metrics, and staged rollout decision.

## Stop Boundary

Stop before broad hard enforcement if any P0 race, false-positive ownership block, or rollback data-loss case remains.
