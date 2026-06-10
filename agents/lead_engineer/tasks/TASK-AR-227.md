---
id: TASK-AR-227
display_id: TASK-AR-227
task_uid: 808cdda2-38cf-4fe7-a054-edc1245e3157
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
status: completed
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
task_set_id: TASKSET-AR-UI-CONSOLE
tags:
  - ui-console
  - runtime-api
  - file-adapter
  - state-api
  - mvp
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-226.md
  - docs/UI_RUNTIME_DATA_MAP.md
  - docs/UI_STATE_API_EXAMPLES.md
  - src/agent_runtime/ui_state.py
  - tests/test_ui_state.py
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

## State Machine Mapping

| Machine | Current State | Trigger | Evidence |
|---|---|---|---|
| `cycle` | `done` | `gates_pass` | `ui-state` adapter loads current repo state without starting a runtime loop. |
| `task` | `completed` | `done_criteria_met` | `src/agent_runtime/ui_state.py`, CLI subcommand, and tests are present. |
| `gate` | `pass` | `verification_passed` | `pytest tests/test_ui_state.py -q` passed under `PYTHONPATH=src`. |
| `document` | `formatted` | `document_regenerated` | `docs/UI_STATE_API_EXAMPLES.md` documents response shapes for `TASK-AR-228`. |

## Completion Evidence

- 2026-06-10: Added read-only adapter module `src/agent_runtime/ui_state.py`.
- 2026-06-10: Added CLI surface `agent_runtime ui-state --resource state|tasks|agents|messages|events|goals|sources --json`.
- 2026-06-10: Added tests for runtime task/message/event/session parsing, missing optional source gaps, malformed JSON warnings, Korean `## 목표` task descriptions, and CLI JSON output.
- 2026-06-10: Added API response examples in `docs/UI_STATE_API_EXAMPLES.md`.
- 2026-06-10: Next implementation pointer is `TASK-AR-228` Read-Only Web Console MVP.
