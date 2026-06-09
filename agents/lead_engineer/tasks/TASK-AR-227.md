---
id: TASK-AR-227
status: planned
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
tags:
  - ui-console
  - runtime-api
  - file-adapter
  - state-api
  - mvp
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-226.md
  - BACKLOG.md
  - BACKLOG-BOARD.md
created: 2026-06-10
---

## Goal

Expose a safe, read-first backend interface for the UI console, using runtime files as the source of truth and avoiding direct frontend mutation of runtime internals.

## Scope

- Implement the minimum state endpoints or equivalent local adapter:
  - `GET /api/state`
  - `GET /api/tasks`
  - `GET /api/agents`
  - `GET /api/messages`
  - `GET /api/events`
  - `GET /api/goals`
- Normalize runtime records into UI-facing objects without losing source references.
- Include `last_updated`, `source`, and `freshness` metadata in responses.
- Keep the first implementation polling-compatible; do not require WebSocket infrastructure.

## Deliverables

- A small UI backend service or file adapter module.
- Tests for parsing representative runtime task/message/event/goal records.
- API response examples for the frontend task.

## Completion Criteria

- Read-only state can be loaded without starting a long-running goal loop.
- Missing optional runtime files return empty collections plus warnings, not crashes.
- The adapter preserves task IDs, statuses, ordering fields, assignees, and blocked reasons.
- The adapter returns source pointers so the UI can show where data came from.

## Implementation Notes

- If FastAPI is used, keep it local-first and dependency-minimal.
- If a file adapter is used before an API server, keep the interface shaped like the future API.
- Do not embed Claude Code, Codex CLI, or terminal sessions in this task.

## Verification

- Add unit tests for adapter parsing and empty-state behavior.
- Run targeted tests plus any existing publish/release preflight checks affected by new files.
