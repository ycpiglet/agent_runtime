---
id: TASK-AR-231
status: planned
owner: lead-engineer
priority: P1
difficulty: M
est_hours: 12
est_tokens: 2200
tags:
  - ui-console
  - live-updates
  - event-log
  - replay
  - evidence
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-227.md
  - agents/lead_engineer/tasks/TASK-AR-228.md
  - agents/lead_engineer/tasks/TASK-AR-230.md
  - BACKLOG.md
  - BACKLOG-BOARD.md
created: 2026-06-10
---

## Goal

Make the UI trustworthy during long `/goal` runs by surfacing freshness, live event changes, logs, errors, and evidence without relying on manual CLI polling.

## Scope

- Add consistent freshness indicators to every panel.
- Keep polling reliable and add Server-Sent Events only if the backend shape is ready.
- Expand event timeline filtering by type, agent, task, goal, and search text.
- Add logs/errors/issues/evidence sections linked back to tasks and events.
- Add the first replay-mode design or minimal implementation for goal iterations.
- Add a daily brief output if the underlying event/task data is sufficient.

## Deliverables

- Live/freshness behavior for state panels.
- Filterable event timeline and linked evidence/error panels.
- Replay-mode or daily-brief follow-up spec if not fully implemented.

## Completion Criteria

- User can tell when each panel was last updated and what source it came from.
- Recent errors and evidence links are visible from dashboard and task detail.
- Long-running goal history can be reviewed without asking the CLI for logs.
- Polling degradation is explicit if backend state cannot be read.

## Implementation Notes

- Start with polling; promote to SSE only after the state API is stable.
- Keep evidence display read-only unless a dedicated evidence mutation path exists.
- Avoid unbounded log rendering; use pagination or truncation with source links.

## Verification

- Add tests for event filtering and freshness metadata.
- Run a local long-ish sample state replay or fixture-based UI smoke check.
