---
id: TASK-AR-347
display_id: TASK-AR-347
task_uid: 815686ed-3b26-41ff-87e2-6995ab47758b
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
updated_at: 2026-06-11T19:50:16+09:00
status: planned
priority: P1
difficulty: M
est_hours: 4
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
horizon: medium
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - project-management
  - wip
  - flow
---

# TASK-AR-347 - WIP and flow policy

## Goal

- Add Kanban-style WIP controls and flow signals for tasksets, teams, and worker units.

## Scope

- Define WIP limits for active units per taskset/team.
- Track work item age, blocked age, and throughput where local data exists.
- Add watch/block outputs when WIP or stale work crosses policy limits.

## Acceptance Criteria

- Board or gate output shows active WIP and stale unit signals.
- WIP exceptions require explicit policy text.
- Flow metrics are derived from claims/task metadata, not chat claims.

## Evidence Targets

- `scripts/backlog_board.py`
- `scripts/taskset_work_gate.py` or a dedicated flow gate
- focused tests

