---
id: TASK-AR-342
display_id: TASK-AR-342
task_uid: a9df4c1b-0cdc-4164-b298-13f7dd15f545
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
updated_at: 2026-06-11T19:50:16+09:00
status: planned
priority: P0
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
horizon: short
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - project-management
  - hierarchy
  - schema
---

# TASK-AR-342 - Project hierarchy SSoT and horizon metadata

## Goal

- Make `project -> taskset -> task -> unit` and short/mid/long horizon metadata a canonical runtime contract.

## Scope

- Harden `agents/project/PROJECT-MANAGEMENT-CONTRACT.md` into schema-ready conventions.
- Define where project, taskset, task, and unit specs live.
- Add metadata conventions for `project_id`, `horizon`, `unit_spec`, and model-tier fields.

## Acceptance Criteria

- A future task can link to a project and unit spec without relying on chat history.
- Existing task files remain valid during migration.
- The contract documents backlog as metadata/index, not full execution spec.

## Evidence Targets

- `agents/project/PROJECT-MANAGEMENT-CONTRACT.md`
- `docs/superpowers/plans/2026-06-11-project-management-operating-system.md`
- schema or validator follow-up notes

