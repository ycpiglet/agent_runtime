---
id: TASK-AR-230
status: completed
owner: lead-engineer
priority: P1
difficulty: M
est_hours: 10
est_tokens: 2000
tags:
  - ui-console
  - runtime-commands
  - agent-prompts
  - safety-boundary
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-226.md
  - agents/lead_engineer/tasks/TASK-AR-227.md
  - agents/lead_engineer/tasks/TASK-AR-229.md
  - src/agent_runtime/ui_commands.py
  - src/agent_runtime/ui_console.py
  - tests/test_ui_commands.py
  - tests/test_ui_console.py
  - docs/UI_RUNTIME_COMMANDS.md
  - BACKLOG.md
  - BACKLOG-BOARD.md
created: 2026-06-10
---

## Goal

Allow the user to control runtime work from the UI by sending prompts and lifecycle commands through the runtime command interface instead of embedding CLI terminals.

## Scope

- Add command actions for send prompt to agent, send task to runtime, request review, request meeting, start goal, pause goal, resume goal, and stop goal where supported.
- Add safety metadata to commands: actor, target, reason, task_id, goal_id, created_at, and approval requirement.
- Show command status in the UI after submission.
- Keep high-risk actions routed to human approval when they involve deletion, commit, push, PR creation, dependency install, long-running goals, or irreversible external effects.

## Deliverables

- `POST /api/commands` or command-outbox equivalent.
- UI command input and agent/task action buttons.
- Command status display linked to messages/events.

## Completion Criteria

- User can send an instruction to a selected agent through runtime-visible state.
- Pause/resume/start/stop controls are present only when runtime capability exists or the unsupported state is explicit.
- The UI never attempts to type into Claude/Codex terminal sessions directly.
- High-risk commands are blocked or marked approval-required before execution.

## Implementation Notes

- Model the correct flow as UI -> command -> runtime -> worker/provider -> stored output -> UI refresh.
- Do not add PTY/WebSocket terminal embedding in this task.
- Reuse existing message/task routing primitives if present.

## Verification

- Add command schema tests and a smoke test for at least one `call_agent` command.
- Verify submitted commands appear in the message/event timeline after runtime processing or are visible as pending outbox records.

## State Machine Mapping

- cycle: done
- task: TASK-AR-230 completed
- gate: pass
- document: formatted

## Progress Log

- 2026-06-10: Started after `TASK-AR-229` landed. Implementation path is test-first extension of `.ui_outbox` command records for runtime-safe prompt/lifecycle requests, with unsupported or high-risk execution made explicit instead of terminal embedding.
- 2026-06-10: Completed runtime command controls. Added `runtime.call_agent`, `runtime.assign_task`, `runtime.request_review`, `runtime.request_meeting`, and `runtime.goal.*` command records. High-risk commands become `approval_required`; lifecycle commands without an executor become `pending_runtime_support`; safe agent prompts write queued runtime messages.

## Completion Evidence

- `PYTHONPATH=src pytest tests/test_ui_commands.py -q` -> 11 passed.
- `PYTHONPATH=src pytest tests/test_ui_console.py -q` -> 9 passed.
- `PYTHONPATH=src pytest tests/test_ui_commands.py tests/test_ui_state.py -q` -> 16 passed.
- Temporary-root route smoke: `POST /api/commands` with `runtime.call_agent` returned `queued`; `/api/state` showed one queued command and one `runtime.call_agent` message to `qa`.
