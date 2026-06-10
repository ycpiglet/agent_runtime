---
id: TASK-AR-266
display_id: TASK-AR-266
task_uid: c008f8b2-b12d-4523-a63c-4e2d0c87756d
registered_at: 2026-06-11
created_at: 2026-06-11
started_at: 2026-06-11
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
title: Apply Linear-like console shell styling
status: completed
priority: high
owner: lead_engineer
task_set_id: TASKSET-AR-UI-DESIGN-SYSTEM
created: 2026-06-11
completed: 2026-06-11
---

# TASK-AR-266 - Apply Linear-like console shell styling

## Outcome

Applied the selected dark operator-console token system to the Agent Runtime UI shell while preserving existing DOM ids and route contracts.

## Evidence

- `src/agent_runtime/ui_console.py`
- `tests/test_ui_console.py`

## Notes

The implementation keeps `runtime-console-app`, existing tabs, command form, filters, and JavaScript API calls intact.
