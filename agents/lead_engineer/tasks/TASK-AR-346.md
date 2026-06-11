---
id: TASK-AR-346
display_id: TASK-AR-346
task_uid: 72489271-63b2-4dde-8759-4384fbb7b9db
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
updated_at: 2026-06-11T19:50:16+09:00
status: planned
priority: P0
difficulty: L
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
horizon: short
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - project-management
  - taskset-dispatch
  - scope-boundary
---

# TASK-AR-346 - Dispatcher unit claims and scope stop

## Goal

- Extend taskset dispatch so a worker can claim one unit and must stop at the taskset/unit boundary.

## Scope

- Extend claim JSON with `project_id`, `unit_id`, model tier, WIP slot, and stop condition.
- Require readiness gate pass before low-tier unit dispatch.
- Emit or record completion-stop evidence when a taskset or assigned unit is complete.

## Acceptance Criteria

- Dispatcher output tells the worker exactly which unit to execute.
- Scope-outside continuation is blocked or reported after completion.
- Existing taskset alias behavior remains compatible.

## Evidence Targets

- `scripts/taskset_dispatcher.py`
- `scripts/taskset_work_gate.py`
- `tests/test_taskset_dispatcher.py`
- `tests/test_taskset_work_gate.py`

