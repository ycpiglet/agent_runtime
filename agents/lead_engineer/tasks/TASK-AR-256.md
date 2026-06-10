---
id: TASK-AR-256
display_id: TASK-AR-256
task_uid: 8188dea3-31d9-452c-864a-792e257bcee6
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
title: Expose collaboration concurrency state in UI API
status: completed
priority: P1
importance: High
difficulty: M
est_hours: 4
est_tokens: 1100
task_set_id: TASKSET-AR-COLLAB-CONCURRENCY
team: ui-runtime-operator
owner: lead-engineer
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:20:00+09:00
completed_at: 2026-06-10T23:20:00+09:00
tags: [ui-state, collaboration, pane-events]
audit_log: [src/agent_runtime/ui_state.py, tests/test_ui_state.py]
---

## Goal

Expose pane collaboration events and task-set summaries through the UI state adapter.

## Completion Criteria

- UI state includes a `collaboration` resource.
- Sources include `pane_events`.
- Tests cover event summary exposure.

## Result

- Added pane event loading and collaboration summary to `agent_runtime.ui_state`.
