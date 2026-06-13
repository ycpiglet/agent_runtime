---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-373
work_uid: d30bf31f-641a-4e5a-8968-51d14a267fed
kind: task
parent_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-373/UNIT-TASK-AR-373-001.md
origin_type: planning_proposal
origin_ref: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
created_by: planner
id: TASK-AR-373
display_id: TASK-AR-373
task_uid: d30bf31f-641a-4e5a-8968-51d14a267fed
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
updated_at: 2026-06-13T16:30:00+09:00
title: Unit-readiness migration report for legacy planned tasks
status: worker_ready
priority: P3
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
escalation_triggers:
  - ambiguity
  - migration
tags:
  - unit-readiness
  - migration
  - planning
---

# TASK-AR-373 - Unit-readiness migration report for legacy planned tasks

## Goal

- Make it visible which planned tasks are worker-ready and which still require planner refinement into units.

## Scope

- Run or extend the unit readiness gate to classify planned/in-progress tasks.
- Produce a report grouping tasks by `worker_ready`, `task_detail_sufficient`, `unit_missing`, and `planner_refine_required`.
- Do not fail the whole repository for historical tasks; fail only when a dispatcher attempts low-tier worker assignment without a ready unit or equivalent detail.
- Add next-action links for the highest-risk planned tasks.

## Out Of Scope

- Writing units for every legacy task in this task.
- Closing or reprioritizing existing tasksets.
- Changing task statuses without owner/planner decision.

## Acceptance Criteria

- Report lists every planned task missing a worker-ready unit or equivalent task detail.
- Dispatcher/gate behavior remains compatible with completed and historical tasks.
- Future planners have a clear migration queue instead of discovering missing context during execution.

## Verification

- `python scripts/task_unit_readiness_gate.py --check`
- Focused report/gate tests if new classification output is added.

## Handoff

- Report counts by class, top migration candidates, and any tasks blocked from low-tier dispatch.
