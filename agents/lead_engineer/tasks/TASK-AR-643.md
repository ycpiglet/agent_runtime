---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-643
display_id: TASK-AR-643
task_uid: 34e50cc4-74b2-4fed-b538-6127b71a1efe
work_id: TASK-AR-643
work_uid: 34e50cc4-74b2-4fed-b538-6127b71a1efe
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T23:37:20+09:00
title: Enforce consumer template and skill dependency closure
status: planned
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-643/UNIT-TASK-AR-643-001.md
reservation_id: RES-20260728-163601-b8c2a87a-05
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Guarantee that every capability advertised to a clean host has all executable dependencies in the selected profile.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-643 - Enforce consumer template and skill dependency closure

## Goal

- Guarantee that every capability advertised to a clean host has all executable dependencies in the selected profile.

## Scope

- Add a dependency-closure gate, ship or rewire missing work/release/session helpers, and expand clean-host smoke to exercise declared skills.

## Acceptance Criteria

- Every shipped SKILL dependency exists in its effective profile.
- work.py and required helpers execute in a clean installed host.
- Template smoke exercises work status/new/verify and session closeout dependencies.
- Profile reduction never leaves dangling docs or hook commands.

## Verification

- `python -m pytest tests/test_template_smoke.py tests/test_runtime_asset_usage.py tests/test_wheel_dotfiles_packaging.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`
