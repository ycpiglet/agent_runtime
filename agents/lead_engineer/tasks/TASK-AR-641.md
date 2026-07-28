---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-641
display_id: TASK-AR-641
task_uid: eb3e329f-b0e1-4bfc-9a8f-de3bf752a38d
work_id: TASK-AR-641
work_uid: eb3e329f-b0e1-4bfc-9a8f-de3bf752a38d
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Build brownfield adopt planning and generated-tree filtering
status: planned
priority: P0
difficulty: L
est_hours: 12
est_tokens: 26000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-641/UNIT-TASK-AR-641-001.md
reservation_id: RES-20260728-163601-b8c2a87a-03
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Let an existing repository understand exactly what Agent Runtime would add, own, preserve, or conflict with before any mutation.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-641 - Build brownfield adopt planning and generated-tree filtering

## Goal

- Let an existing repository understand exactly what Agent Runtime would add, own, preserve, or conflict with before any mutation.

## Scope

- Add adopt --plan, pre-adoption doctor mode, generated-directory filtering, host asset detection, and a machine-readable ownership/conflict report.

## Acceptance Criteria

- Bean Wiki and Allimbot inventory excludes generated and ignored trees.
- Existing AGENTS, Claude agents, skills, and product docs are detected as host assets.
- adopt --plan is read-only and reports planned writes and conflicts.
- doctor distinguishes pre-adoption readiness from broken installation.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py tests/test_doctor.py tests/test_adoption.py -q`
