---
id: UI-RUNTIME-COMMANDS
task: TASK-AR-230
status: completed
owner: lead-engineer
updated_at: 2026-06-10
tags: [ui-console, runtime-commands, command-outbox, safety-boundary]
---

# UI Runtime Commands

`TASK-AR-230` extends the UI console write path from task edits to runtime-safe
command requests. The browser submits commands to `/api/commands`; the local
server validates them and stores the outcome in `.ui_outbox/COMMAND-*.json`.

## Command Types

| Type | Runtime effect |
|---|---|
| `runtime.call_agent` | Writes a queued runtime-command message to the selected agent |
| `runtime.assign_task` | Queues a task instruction for the selected agent/runtime target |
| `runtime.request_review` | Queues a review request without opening a terminal |
| `runtime.request_meeting` | Queues a meeting/sync request without opening a terminal |
| `runtime.goal.start` | Records an explicit lifecycle request for a future executor |
| `runtime.goal.pause` | Records an explicit lifecycle request for a future executor |
| `runtime.goal.resume` | Records an explicit lifecycle request for a future executor |
| `runtime.goal.stop` | Records an explicit lifecycle request for a future executor |

## Safety Metadata

Every command record includes:

| Field | Meaning |
|---|---|
| `actor` | User or UI actor that requested the command |
| `target` | Selected agent, runtime target, or goal id |
| `reason` | Operator rationale shown in the write log |
| `task_id` | Optional task context |
| `goal_id` | Optional goal context |
| `approval_required` | Whether execution must wait for owner approval |
| `risk_level` | `low` or `high` based on approval triggers |

High-risk commands are not executed. Requests mentioning deletion, commit,
push, pull request creation, dependency install, long-running goals, or
irreversible external effects are stored with `status: approval_required`.

## Runtime Boundary

The UI does not type into Claude, Codex, PowerShell, or any PTY. Supported
agent prompts are translated into queued markdown messages under
`agents/messages/inbox`. Lifecycle controls are stored as
`pending_runtime_support` until a runtime executor consumes those command
records.

## UI States

| State | Meaning |
|---|---|
| `queued` | Message-backed runtime command is visible to the runtime |
| `approval_required` | High-risk command is waiting for owner approval |
| `pending_runtime_support` | Command is valid but no executor exists yet |
| `failed` | Command schema or payload validation failed |

## Verification

- `PYTHONPATH=src pytest tests/test_ui_commands.py -q` -> 11 passed.
- `PYTHONPATH=src pytest tests/test_ui_console.py -q` -> 9 passed.
- Temporary-root route smoke: `POST /api/commands` with `runtime.call_agent`
  returned `queued`; `/api/state` then showed one command and one queued
  `runtime.call_agent` message to `qa`.
