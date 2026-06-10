---
id: TASK-AR-229
display_id: TASK-AR-229
task_uid: 9d3ec2a8-4728-4fd8-a785-10ac57059306
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
status: completed
owner: lead-engineer
priority: P1
difficulty: M
est_hours: 12
est_tokens: 2200
task_set_id: TASKSET-AR-UI-CONSOLE
tags:
  - ui-console
  - task-crud
  - command-outbox
  - backlog-order
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-226.md
  - agents/lead_engineer/tasks/TASK-AR-227.md
  - agents/lead_engineer/tasks/TASK-AR-228.md
  - docs/UI_WRITE_COMMANDS.md
  - src/agent_runtime/ui_commands.py
  - src/agent_runtime/ui_console.py
  - tests/test_ui_commands.py
  - BACKLOG.md
  - BACKLOG-BOARD.md
created: 2026-06-10
---

## Goal

Let the UI manage tasks safely by sending changes through runtime APIs or a command outbox, while preserving task order as a scheduling signal.

## Scope

- Add create task, edit title, edit description, change status, edit priority, assign agent, add comment/message, archive task, and reorder backlog actions.
- Route writes through API endpoints or `.ui_outbox/COMMAND-*.json` style command files.
- Store write acknowledgements and validation errors so the UI can show whether runtime accepted a change.
- Preserve order fields whenever drag/drop changes status or rank.

## Deliverables

- Safe write interface for task CRUD and ordering.
- UI controls in backlog/kanban/detail drawer for the supported operations.
- Tests for command serialization and invalid update rejection.

## Completion Criteria

- Creating or editing a task from the UI results in a runtime-visible task update.
- Reordering tasks preserves stable order across refreshes.
- Invalid status, missing task ID, or unsafe direct-file mutation attempts are rejected.
- The UI shows pending, accepted, and failed write states.

## Implementation Notes

- The runtime remains authoritative; frontend state must reconcile after each accepted write.
- Use command outbox if a full runtime API is not ready.
- Keep destructive actions such as delete/archive behind explicit confirmation or out of MVP if runtime support is unclear.

## Verification

- Add unit tests for write command payloads.
- Add an integration or smoke test that creates a task and observes it through the read API.

## State Machine Mapping

| Machine | Current State | Trigger | Evidence |
|---|---|---|---|
| `cycle` | `done` | `gates_pass` | UI create/update/archive smoke passed on an isolated runtime root. |
| `task` | `completed` | `done_criteria_met` | `ui_commands` and `ui_console` write routes cover task create/update/reorder/comment/archive. |
| `gate` | `pass` | `verification_passed` | Targeted tests and browser smoke passed. |
| `document` | `formatted` | `document_regenerated` | `docs/UI_WRITE_COMMANDS.md` records routes, validation, ordering, and states. |

## Completion Evidence

- 2026-06-10: Added `src/agent_runtime/ui_commands.py` with validated write-through/outbox commands.
- 2026-06-10: Added POST/PATCH routes for task create, task update, reorder, comment/message, and archive.
- 2026-06-10: Added UI controls for create, save, move earlier/later, comment, archive, and write-state display.
- 2026-06-10: Added command state loading through `/api/commands` and `/api/state`.
- 2026-06-10: Added canonical `order` frontmatter support in `ui_state`.
- 2026-06-10: Targeted tests passed: `PYTHONPATH=src pytest tests/test_ui_commands.py tests/test_ui_console.py tests/test_ui_state.py -q` -> 21 passed.
- 2026-06-10: Browser smoke created `TASK-UI-901`, updated it, archived it, and observed three accepted commands.
- 2026-06-10: Full suite passed: `PYTHONPATH=.;src pytest tests -q` -> 239 passed.
- 2026-06-10: Next implementation pointer is `TASK-AR-230` Runtime Command Controls.
