---
id: TASK-AR-232
display_id: TASK-AR-232
task_uid: bd41c885-08dc-4ff9-bed7-d727b9210333
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
status: completed
owner: lead-engineer
priority: P2
difficulty: L
est_hours: 16
est_tokens: 2600
task_set_id: TASKSET-AR-UI-CONSOLE
tags:
  - ui-console
  - graph-view
  - state-machine
  - roadmap
  - future
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-226.md
  - agents/lead_engineer/tasks/TASK-AR-231.md
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - docs/UI_MAP_VIEWS.md
  - BACKLOG.md
  - BACKLOG-BOARD.md
created: 2026-06-10
---

## Goal

Add the post-MVP visualizations that make the runtime understandable as an agent organization: state-machine view, communication graph, roadmap hierarchy, and workload insight.

## Scope

- Add process/state-machine view for global runtime, goal loop, task lifecycle, and agent lifecycle.
- Add agent communication graph from message/task/review/dependency edges.
- Add roadmap/goals/milestones hierarchy view.
- Add workload heatmap and command palette only after MVP data and commands are stable.
- Keep game-like presentation as optional styling, not a blocker for operational clarity.

## Deliverables

- State-machine stepper or card-based process view.
- Static communication graph generated from latest state.
- Roadmap/goals/milestones list or timeline.
- Follow-up notes for richer graph/live/game-like UI.

## Completion Criteria

- User can see which process state the runtime, goal, task, and agent are currently in.
- Agent graph shows user/orchestrator/worker/reviewer relationships from actual messages or assignments.
- Roadmap hierarchy connects vision/objective/goal/milestone/task where data exists.
- Missing graph/roadmap data is reported as a data gap, not fabricated.

## Implementation Notes

- Start with cards or a vertical stepper before introducing a graph library.
- Use React Flow or similar only after static graph data is proven.
- Keep this task behind MVP read/write/control work.

## Verification

- Add tests for transforming messages/tasks into graph edges.
- Verify state names remain aligned with `agents/project/STATE-MACHINES.yml`.

## State Machine Mapping

- cycle: done
- task: TASK-AR-232 completed
- gate: pass
- document: formatted

## Progress Log

- 2026-06-10: Started after `TASK-AR-231` landed. Implementation path is TDD-first static graph/state-machine/roadmap transforms before introducing a graph library.
- 2026-06-10: Completed static graph, state-machine, and roadmap map views. Added `/api/graph`, `/api/state-machines`, `/api/roadmap`, plus Map UI tab. Rich graph libraries remain deferred.

## Completion Evidence

- `PYTHONPATH=src pytest tests/test_ui_state.py -q` -> 7 passed.
- `PYTHONPATH=src pytest tests/test_ui_console.py -q` -> 11 passed.
- Temporary-root route smoke: `/api/graph` returned two edges, `/api/state-machines` returned one machine, and `/api/roadmap` returned one milestone.
