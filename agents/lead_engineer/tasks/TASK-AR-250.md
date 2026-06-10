---
id: TASK-AR-250
display_id: TASK-AR-250
task_uid: 35989583-b684-4d4b-8b3b-69a28d36c54e
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
status: completed
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 6
est_tokens: 1800
task_set_id: TASKSET-AR-PANE-PROGRESS
depends_on:
  - TASK-AR-247
tags:
  - task-set
  - dispatcher
  - hook
  - skill
  - pane-progress
  - governance-gate
audit_log:
  - scripts/taskset_dispatcher.py
  - scripts/taskset_work_gate.py
  - scripts/taskset_prompt_hook.py
  - reviews/REVIEW-2026-06-10-agent-runtime-taskset-dispatcher.md
created: 2026-06-10
---

## Goal

Make task-set work user-friendly enough that a prompt like `taskset-quality-loop 진행해줘` resolves the lane, claims the work, injects guardrails, and prevents avoidable pane conflicts.

## Scope

- Add a task-set dispatcher with alias resolution, next-task planning, and claim creation.
- Extend task claims and parallel gates with task-set and progress metadata.
- Add prompt hook support for `taskset-*` requests.
- Add task-set routing gates to Owner governance.
- Add short skill and template guidance so future agents use the tool instead of re-reading long docs.

## Completion Criteria

- Focused task-set dispatcher, prompt hook, claim dispatcher, and parallel gate tests pass.
- Owner governance includes the task-set work gate.
- Root and project templates include matching scripts, hook config, and skill/rule docs.
- `BACKLOG-BOARD.md` is regenerated with the new task.

## State Machine Mapping

- cycle: completed
- task: TASK-AR-250 completed
- gate: pass
- review: REVIEW-2026-06-10-agent-runtime-taskset-dispatcher
