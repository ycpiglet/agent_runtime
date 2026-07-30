---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-660
display_id: TASK-AR-660
task_uid: b1ad13b9-6d47-4213-90e9-1e15cc4eed0c
work_id: TASK-AR-660
work_uid: b1ad13b9-6d47-4213-90e9-1e15cc4eed0c
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Make automation loops durable and idempotent
status: planned
priority: P1
difficulty: XL
est_hours: 22
est_tokens: 46000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-660/UNIT-TASK-AR-660-001.md
reservation_id: RES-20260730-112517-91ed5cf4-06
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Prevent process restarts, retries, and duplicate dispatch from repeating steps or externally visible effects.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - A run step has a stable idempotency key across restart.
  - A completed effect with a receipt is reconciled rather than repeated.
  - Retry limits apply across process restarts with backoff, jitter, and circuit breaking.
  - No-progress repetition halts with a classified reason.
  - Cancelling a goal run prevents child dispatch and queued effects from continuing.
verification:
  - python -m pytest -q tests/test_run_step_ledger.py tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_stop_events.py tests/test_auto_dispatch.py
---

# TASK-AR-660 - Make automation loops durable and idempotent

## Goal

- Prevent process restarts, retries, and duplicate dispatch from repeating steps or externally visible effects.

## Scope

- Add a durable run-step-attempt ledger, idempotency keys, effect receipts, global retry budgets, progress checks, cancellation propagation, and compensation pointers. Keep provider-specific effects behind adapters.

## Acceptance Criteria

- A run step has a stable idempotency key across restart.
- A completed effect with a receipt is reconciled rather than repeated.
- Retry limits apply across process restarts with backoff, jitter, and circuit breaking.
- No-progress repetition halts with a classified reason.
- Cancelling a goal run prevents child dispatch and queued effects from continuing.

## Verification

- `python -m pytest -q tests/test_run_step_ledger.py tests/test_agent_loop.py tests/test_goal_supervisor.py tests/test_stop_events.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py`
