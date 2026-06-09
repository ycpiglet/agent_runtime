---
id: TASK-AR-232
status: planned
owner: lead-engineer
priority: P2
difficulty: L
est_hours: 16
est_tokens: 2600
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
