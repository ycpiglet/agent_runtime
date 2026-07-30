---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-656
display_id: TASK-AR-656
task_uid: 4aab81f0-39a0-4aad-ae9d-530d3f231379
work_id: TASK-AR-656
work_uid: 4aab81f0-39a0-4aad-ae9d-530d3f231379
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Bind dispatch, loops, and supervision to a frozen run
status: planned
priority: P0
difficulty: L
est_hours: 16
est_tokens: 34000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-656/UNIT-TASK-AR-656-001.md
reservation_id: RES-20260730-112517-91ed5cf4-02
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Ensure every selection, claim, restart, and completion decision uses one exact goal run and scope revision rather than live backlog or raw goal text.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - Wave planning for a goal selects only IDs sealed in its active scope revision.
  - A claim outside the sealed scope fails before persistence.
  - Agent loops consume only run-bound work and never drain an unrelated role inbox.
  - Supervisor restarts identify an exact run and reject a mismatched scope digest.
  - Frozen completion stops even when new backlog exists.
verification:
  - python -m pytest -q tests/test_wave_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_taskset_boundary_gate.py
---

# TASK-AR-656 - Bind dispatch, loops, and supervision to a frozen run

## Goal

- Ensure every selection, claim, restart, and completion decision uses one exact goal run and scope revision rather than live backlog or raw goal text.

## Scope

- Make wave dispatch consume sealed membership, make claims validate the same digest, and make agent_loop and goal_supervisor resume only an exact run. Do not implement the session lease store in this task.

## Acceptance Criteria

- Wave planning for a goal selects only IDs sealed in its active scope revision.
- A claim outside the sealed scope fails before persistence.
- Agent loops consume only run-bound work and never drain an unrelated role inbox.
- Supervisor restarts identify an exact run and reject a mismatched scope digest.
- Frozen completion stops even when new backlog exists.

## Verification

- `python -m pytest -q tests/test_wave_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_taskset_boundary_gate.py`
