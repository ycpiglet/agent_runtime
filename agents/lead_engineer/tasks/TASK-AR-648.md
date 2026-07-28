---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-648
display_id: TASK-AR-648
task_uid: a6d807f7-f61e-402c-b5e9-d50b3de23bf6
work_id: TASK-AR-648
work_uid: a6d807f7-f61e-402c-b5e9-d50b3de23bf6
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Run the Bean Wiki web-content pilot
status: planned
priority: P0
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-001.md
reservation_id: RES-20260728-163601-b8c2a87a-10
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Prove lightweight adoption preserves the existing editorial harness while adding task trace, compound, scribe, and model economy.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-648 - Run the Bean Wiki web-content pilot

## Goal

- Prove lightweight adoption preserves the existing editorial harness while adding task trace, compound, scribe, and model economy.

## Scope

- Use a clean Bean Wiki worktree, apply core plus web-content profile, run three non-publishing tasks, and capture adoption and runtime evidence.

## Acceptance Criteria

- Existing AGENTS, editorial agents, skills, and content rules are unchanged except an explicit runtime include/adapter.
- Three real tasks complete with trace and no claimless diff.
- One compound retrieval and one restart/compaction recovery are demonstrated.
- No live content publish occurs.

## Verification

- `python -m pytest tests/test_adoption.py tests/test_template_smoke.py -q`
- `python scripts/pilot_acceptance.py --host bean-wiki --check`
