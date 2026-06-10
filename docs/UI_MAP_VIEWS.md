---
id: UI-MAP-VIEWS
task: TASK-AR-232
status: completed
owner: lead-engineer
updated_at: 2026-06-10
tags: [ui-console, graph-view, state-machine, roadmap]
---

# UI Map Views

`TASK-AR-232` adds read-only map resources for understanding the runtime as an
agent organization before introducing a graph library.

## Resources

| Resource | Route | Source |
|---|---|---|
| `graph` | `GET /api/graph` | tasks, agents, messages, events |
| `state_machines` | `GET /api/state-machines` | `agents/project/STATE-MACHINES.yml` |
| `roadmap` | `GET /api/roadmap` | `agents/project/ROADMAP.md` |

## Graph

The graph contains:

- role/agent/task nodes from sessions, task owners, events, and messages.
- message edges from `from -> to`.
- task ownership edges from `owner_agent -> task`.

## State Machines

The parser reads the current repository state-machine YAML shape and exposes
machine ids, states, initial state, and a conservative observed current state.
For task and agent job machines, observed task/session statuses can override the
initial state.

## Roadmap

The roadmap view extracts current phase, next milestone, and dated markdown
milestones. Missing roadmap or state-machine files are reported as source gaps,
not fabricated hierarchy.

## Verification

- `PYTHONPATH=src pytest tests/test_ui_state.py -q` -> 7 passed.
- `PYTHONPATH=src pytest tests/test_ui_console.py -q` -> 11 passed.
- Temporary-root route smoke: `/api/graph` returned two edges,
  `/api/state-machines` returned one machine, and `/api/roadmap` returned one
  milestone.
