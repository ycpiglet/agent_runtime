---
id: UI-CONSOLE-MVP
task: TASK-AR-228
status: completed
owner: lead-engineer
updated_at: 2026-06-10
tags: [ui-console, web-ui, mvp]
---

# UI Console MVP

`TASK-AR-228` adds a local, read-only web console on top of the
`TASK-AR-227` state adapter.

## Run

```powershell
$env:PYTHONPATH='src'
python -m agent_runtime.cli ui-console --root . --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

## Served Routes

| Route | Purpose |
|---|---|
| `/` | UI shell |
| `/app.css` | UI styling |
| `/app.js` | UI polling and rendering |
| `/api/state` | aggregate runtime state |
| `/api/tasks` | task resource |
| `/api/agents` | agent resource |
| `/api/messages` | message resource |
| `/api/events` | event resource |
| `/api/goals` | goal resource |
| `/api/sources` | source/gap/warning resource |
| `/api/errors` | derived recent error resource |
| `/api/evidence` | derived evidence link resource |
| `/api/replay` | derived task/goal replay resource |
| `/api/graph` | derived communication/assignment graph |
| `/api/state-machines` | state-machine process resource |
| `/api/roadmap` | roadmap/milestone resource |
| `/api/commands` | write command log and runtime command submission |

## MVP Coverage

| View | Coverage |
|---|---|
| Dashboard | total tasks, active tasks, blocked tasks, warnings/gaps |
| Backlog | read-only Kanban columns: Backlog, Ready, In Progress, Review, Blocked, Done |
| Agents | runtime session cards and empty state |
| Messages | inbox/archive message list and empty state |
| Events | runtime JSONL timeline, empty state, and type/agent/task/goal/search filters |
| Evidence | recent errors, evidence links, and replay records |
| Map | graph edges, state-machine cards, roadmap milestones |
| Sources | source freshness, gaps, warnings |
| Writes | pending, accepted, queued, approval-required, unsupported, and failed commands |
| Task detail | source path, freshness, status, owner, priority, blocked reason |

## Verification

- Unit/smoke: `PYTHONPATH=src pytest tests/test_ui_console.py -q` -> 5 passed.
- Browser desktop smoke: Chromium loaded `http://127.0.0.1:8765/`, rendered 29 task cards and 6 Kanban lanes, and task detail included source/freshness metadata.
- Browser mobile smoke: Chromium at 390px width rendered 29 task cards, 6 lanes, 5 tabs, and kept body width equal to viewport width.

## Mutation Boundary

The original MVP console was read-only. `TASK-AR-229` closes the first write
follow-up by adding validated task create/update/reorder/comment/archive
commands through the local server and `.ui_outbox`. `TASK-AR-230` adds
runtime-safe command submission for agent prompts and lifecycle requests through
`POST /api/commands`. Lifecycle execution remains explicit
`pending_runtime_support` until a runtime executor exists.
