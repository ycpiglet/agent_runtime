---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-663
display_id: TASK-AR-663
task_uid: f59acf14-8044-40da-94f4-e825a525a5e1
work_id: TASK-AR-663
work_uid: f59acf14-8044-40da-94f4-e825a525a5e1
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Prove concurrent-session safety and roll out enforcement
status: planned
priority: P1
difficulty: XL
est_hours: 24
est_tokens: 50000
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-663/UNIT-TASK-AR-663-001.md
reservation_id: RES-20260730-112517-91ed5cf4-09
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Demonstrate that the current reciprocal-blocking and duplicate-work chain cannot recur across crashes, races, retries, and incompatible parallel changes.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - The pre-fix unknown-change chain is reproduced deterministically and fails after remediation.
  - Race, crash, stale token, retry, cancellation, late task, foreign state, and semantic conflict scenarios pass.
  - Legacy tracked live state migrates without losing audit evidence or creating active ownership.
  - Shadow-mode metrics quantify false positives and bypasses before blocking rollout.
  - Rollback preserves source history, run state, and ownership integrity.
verification:
  - python -m pytest -q tests/test_parallel_session_isolation.py tests/test_bounded_goal_scope.py tests/test_runtime_chaos.py tests/test_control_plane_migration.py tests/test_enforcement_rollout.py
  - python scripts/regen_host_lock_if_needed.py --check
  - python -m pytest -q tests/test_template_smoke.py
  - python scripts/owner_governance_gate.py
---

# TASK-AR-663 - Prove concurrent-session safety and roll out enforcement

## Goal

- Demonstrate that the current reciprocal-blocking and duplicate-work chain cannot recur across crashes, races, retries, and incompatible parallel changes.

## Scope

- Build end-to-end concurrency and failure-injection scenarios, migrate existing state, run shadow mode, define observability and rollback, then enable hard enforcement by measured stages.

## Acceptance Criteria

- The pre-fix unknown-change chain is reproduced deterministically and fails after remediation.
- Race, crash, stale token, retry, cancellation, late task, foreign state, and semantic conflict scenarios pass.
- Legacy tracked live state migrates without losing audit evidence or creating active ownership.
- Shadow-mode metrics quantify false positives and bypasses before blocking rollout.
- Rollback preserves source history, run state, and ownership integrity.

## Verification

- `python -m pytest -q tests/test_parallel_session_isolation.py tests/test_bounded_goal_scope.py tests/test_runtime_chaos.py tests/test_control_plane_migration.py tests/test_enforcement_rollout.py`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python -m pytest -q tests/test_template_smoke.py`
- `python scripts/owner_governance_gate.py`
