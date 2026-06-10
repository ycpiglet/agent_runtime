---
id: TASK-AR-248
status: planned
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 10
est_tokens: 2200
task_set_id: TASKSET-AR-PANE-PROGRESS
depends_on:
  - TASK-AR-247
tags:
  - ui-console
  - runtime-state
  - pane-progress
  - task-set
  - live-observability
audit_log:
  - docs/superpowers/plans/2026-06-10-pane-progress-tasksets.md
  - docs/UI_STATE_API_EXAMPLES.md
  - docs/UI_CONSOLE_MVP.md
created: 2026-06-10
---

## Goal

Show pane and task-set progress in the runtime UI using phase, step counter, rough percent, and human-readable status text.

## Scope

- Extend `agent_runtime.ui_state` so active claims expose `task_set_id`, `step_index`, `step_total`, and `status_text`.
- Add `task_sets` aggregation to the state API.
- Render progress information in the local web console Agents view.
- Document the API and UI contract.

## Completion Criteria

- UI state tests verify per-pane progress fields and task-set aggregation.
- Console tests verify progress fields are present in the browser JavaScript rendering path.
- `python -m agent_runtime.cli ui-state --root . --resource agents --json` exposes pane-level progress.
- `python -m agent_runtime.cli ui-state --root . --resource task_sets --json` exposes task-set progress.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-248 planned
- gate: pending
- review: draft

