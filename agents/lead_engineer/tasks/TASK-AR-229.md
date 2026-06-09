---
id: TASK-AR-229
status: planned
owner: lead-engineer
priority: P1
difficulty: M
est_hours: 12
est_tokens: 2200
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
