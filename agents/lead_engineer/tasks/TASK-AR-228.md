---
id: TASK-AR-228
display_id: TASK-AR-228
task_uid: 1b4f4177-8cba-4a49-b4a3-c3f65efaf0e8
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
status: completed
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 14
est_tokens: 2600
task_set_id: TASKSET-AR-UI-CONSOLE
tags:
  - ui-console
  - web-ui
  - dashboard
  - kanban
  - mvp
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-226.md
  - agents/lead_engineer/tasks/TASK-AR-227.md
  - docs/UI_CONSOLE_MVP.md
  - docs/UI_STATE_API_EXAMPLES.md
  - src/agent_runtime/ui_console.py
  - tests/test_ui_console.py
  - BACKLOG.md
  - BACKLOG-BOARD.md
created: 2026-06-10
---

## Goal

Build the first read-only web console so the user can see backlog, current work, agents, messages, events, and goal status without repeatedly asking the CLI.

## Scope

- Build a local web UI shell using the selected frontend stack.
- Add dashboard panels for current goal, runtime status, active agents, active tasks, blocked tasks, recent errors, recent events, and next recommended task.
- Add backlog and kanban views with columns: Backlog, Ready, In Progress, Review, Blocked, Done.
- Add agent cards, message log, event timeline, and task detail drawer.
- Add manual refresh and simple polling every 2-5 seconds.

## Deliverables

- A runnable local UI.
- Read-only dashboard, backlog/kanban, agent team, messages, events, and task detail views.
- Basic responsive layout that works on desktop and a narrow viewport.

## Completion Criteria

- User can open the UI and see current backlog/status without asking the CLI.
- Clicking a task opens a detail drawer with source and freshness metadata.
- The UI displays empty-state and error-state panels when runtime data is missing.
- No task mutation controls are active until `TASK-AR-229` write path exists.

## Implementation Notes

- Use real runtime data from `TASK-AR-227`; avoid hardcoded demo-only state except in tests/stories.
- Keep game-like agent visuals simple: icons, status badges, and cards are enough for MVP.
- Avoid terminal emulation and direct CLI control.

## Verification

- Run frontend unit/smoke checks for the UI if a frontend test stack is added.
- Verify with a local browser screenshot or equivalent UI smoke pass after implementation.

## State Machine Mapping

| Machine | Current State | Trigger | Evidence |
|---|---|---|---|
| `cycle` | `done` | `gates_pass` | Browser desktop/mobile smoke loaded the local UI and runtime data. |
| `task` | `completed` | `done_criteria_met` | `src/agent_runtime/ui_console.py` and CLI `ui-console` are present. |
| `gate` | `pass` | `verification_passed` | `pytest tests/test_ui_console.py -q` and Playwright smoke passed. |
| `document` | `formatted` | `document_regenerated` | `docs/UI_CONSOLE_MVP.md` records run command, routes, and verification. |

## Completion Evidence

- 2026-06-10: Added read-only stdlib web server `src/agent_runtime/ui_console.py`.
- 2026-06-10: Added CLI `agent_runtime ui-console --root . --host 127.0.0.1 --port 8765`.
- 2026-06-10: Added dashboard, backlog Kanban, agent, message, event, source, and task-detail views.
- 2026-06-10: Added tests for HTML/assets, `/api/state`, resource routes, 404 behavior, and CLI dispatch.
- 2026-06-10: Verified desktop and mobile Chromium smoke with real runtime state.
- 2026-06-10: Full suite passed: `PYTHONPATH=.;src pytest tests -q` -> 228 passed.
- 2026-06-10: Next implementation pointer is `TASK-AR-229` Task CRUD and Backlog Ordering.
