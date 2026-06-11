---
id: TASK-AR-348
display_id: TASK-AR-348
task_uid: 79254591-b673-4000-affb-9ba5dbcbd0a2
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
started_at: 2026-06-12T01:38:36+09:00
updated_at: 2026-06-12T01:38:36+09:00
completed_at: 2026-06-12T01:38:36+09:00
status: completed
priority: P1
difficulty: M
est_hours: 5
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
horizon: medium
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
escalation_triggers: [ambiguity, cross_cutting, repeated_failure]
tags:
  - project-management
  - backlog-board
  - hierarchy-view
---

# TASK-AR-348 - Board and project hierarchy views

## Goal

- Render project/taskset/task/unit hierarchy without stuffing detailed instructions into backlog files.

## Scope

- Extend `BACKLOG-BOARD.md` output with project/taskset hierarchy metadata and detail-spec links.
- Keep task rows compact; link to unit specs rather than embedding them.
- Add tests that completed tasksets still archive correctly.

## Acceptance Criteria

- Owner can see which project and taskset a task belongs to.
- A worker can jump from board to the detailed task/unit spec.
- Board remains a decision surface, not a giant instruction dump.

## Evidence Targets

- `scripts/backlog_board.py`
- `tests/test_backlog_board_tasksets.py`
- `BACKLOG-BOARD.md`

