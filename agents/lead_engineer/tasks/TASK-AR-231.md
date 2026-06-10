---
id: TASK-AR-231
status: completed
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
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - docs/UI_LIVE_OBSERVABILITY.md
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

## State Machine Mapping

- cycle: done
- task: TASK-AR-231 completed
- gate: pass
- document: formatted

## Progress Log

- 2026-06-10: Started after `TASK-AR-230` landed. Implementation path is TDD-first event filtering, panel freshness metadata, error/evidence extraction, and read-only replay visibility.
- 2026-06-10: Completed filterable events, derived `errors`/`evidence`/`replay` resources, Evidence UI tab, and `/api/events` query filtering. Streaming remains deferred; polling remains the active transport.

## Completion Evidence

- `PYTHONPATH=src pytest tests/test_ui_state.py -q` -> 6 passed.
- `PYTHONPATH=src pytest tests/test_ui_console.py -q` -> 10 passed.
- `PYTHONPATH=src pytest tests/test_ui_commands.py -q` -> 11 passed.
- Temporary-root route smoke: filtered `/api/events` returned one `agent.error`; `/api/state` showed one error, one evidence link, and two replay records.
