---
id: UI-WRITE-COMMANDS
task: TASK-AR-229
status: completed
owner: lead-engineer
updated_at: 2026-06-10
tags: [ui-console, command-outbox, task-crud, backlog-order]
---

# UI Write Commands

`TASK-AR-229` adds a safe write-through API for the local UI console. The
browser never writes runtime files directly. It sends JSON requests to the local
console server, which validates the command, applies the allowed mutation, and
stores the accepted or failed command under `.ui_outbox/COMMAND-*.json`.

## Command Types

| Type | Route | Effect |
|---|---|---|
| `task.create` | `POST /api/tasks` | Creates a task markdown file under `agents/lead_engineer/tasks` |
| `task.update` | `PATCH /api/tasks/:id` | Updates title, description, status, priority, owner, or order |
| `task.reorder` | `POST /api/tasks/:id/reorder` | Persists `order` and optional status for stable UI ordering |
| `task.comment` | `POST /api/messages` | Writes a queued message under `agents/messages/inbox` |
| `task.archive` | `POST /api/tasks/:id/archive` | Marks the task `status: completed` and `archived: true` |
| `runtime.*` | `POST /api/commands` | Queues agent prompts, approval-required requests, or unsupported lifecycle requests |

## Validation

- Allowed statuses: `planned`, `ready`, `in_progress`, `review`, `blocked`, `completed`.
- Allowed priorities: `P0`, `P1`, `P2`, `P3`.
- Task IDs must match `TASK-*`.
- Unsafe direct-file keys such as `path`, `source_path`, and `direct_file_path`
  are rejected.
- Failed commands are also stored in `.ui_outbox` with `status: failed` and
  `errors`, so the UI can show the outcome.

## Ordering

Task frontmatter may now include `order`. The read adapter sorts tasks by
`order`, then by task id. Reorder commands update that field, so order stays
stable across refreshes.

## UI States

The console displays write states in the `Writes` tab:

| State | Meaning |
|---|---|
| `pending` | Browser request submitted and awaiting response |
| `accepted` | Server validated and applied the command |
| `queued` | Server translated the command into a runtime-visible message |
| `approval_required` | High-risk command is held for owner approval before execution |
| `pending_runtime_support` | Valid command is stored, but no executor exists yet |
| `failed` | Server rejected the command and stored validation errors |

## Verification

- `PYTHONPATH=src pytest tests/test_ui_commands.py tests/test_ui_console.py tests/test_ui_state.py -q` -> 21 passed.
- Browser smoke on a temporary runtime root created `TASK-UI-901`, changed status, archived it, and observed three accepted command records through `/api/state`.
