---
id: TASK-AR-230
status: planned
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
