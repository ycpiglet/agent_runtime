---
id: UI-LIVE-OBSERVABILITY
task: TASK-AR-231
status: completed
owner: lead-engineer
updated_at: 2026-06-10
tags: [ui-console, live-updates, event-filtering, evidence, replay]
---

# UI Live Observability

`TASK-AR-231` makes the local UI console more trustworthy during long runs by
adding filterable event views and read-only derived errors, evidence, and replay
collections.

## Resources

| Resource | Source | Purpose |
|---|---|---|
| `events` | `agents/runtime/events/*.jsonl` | Runtime timeline with source/freshness metadata |
| `errors` | derived from error-severity events | Recent failure panel |
| `evidence` | event/message `evidence` fields | Review and proof links |
| `replay` | event/message records with task or goal context | Long-run task/goal reconstruction |

## Filtering

`GET /api/events` accepts query filters:

| Query | Match |
|---|---|
| `type` or `event` | exact event name |
| `agent`, `role`, or `actor` | exact role/actor |
| `task_id` or `task` | exact task id |
| `goal_id` or `goal` | exact goal id |
| `q`, `query`, or `search` | case-insensitive text search over the event record |

The browser also filters the event list client-side so the user can narrow the
timeline without waiting for another poll cycle.

## Freshness

Tasks, messages, events, agents, goals, commands, and derived views keep
`source_path`, `source_kind`, `last_updated`, and `freshness` where the source
record can provide it. Missing optional runtime directories remain visible as
gaps instead of being silently ignored.

## Replay Boundary

Replay is read-only and derived. It does not re-run commands or mutate runtime
state. It collects recent task/goal-context events and messages into a stable
timeline capped to the latest 200 records.

## Verification

- `PYTHONPATH=src pytest tests/test_ui_state.py -q` -> 6 passed.
- `PYTHONPATH=src pytest tests/test_ui_console.py -q` -> 10 passed.
- `PYTHONPATH=src pytest tests/test_ui_commands.py -q` -> 11 passed.
- Temporary-root route smoke: `/api/events?type=agent.error&agent=qa&task_id=TASK-UI-231&goal_id=goal-231&q=evidence`
  returned one filtered event; `/api/state` showed one error, one evidence link,
  and two replay records.
