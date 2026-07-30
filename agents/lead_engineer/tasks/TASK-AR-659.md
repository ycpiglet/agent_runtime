---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-659
display_id: TASK-AR-659
task_uid: 18fcba00-e775-4623-8e67-dcccb58f0f9e
work_id: TASK-AR-659
work_uid: 18fcba00-e775-4623-8e67-dcccb58f0f9e
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Make footprints, semantic domains, and dependencies mandatory
status: planned
priority: P0
difficulty: L
est_hours: 16
est_tokens: 33000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-659/UNIT-TASK-AR-659-001.md
reservation_id: RES-20260730-112517-91ed5cf4-05
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Prevent duplicate or incompatible parallel work before dispatch, including overlaps that do not share exact file paths.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - Mutating claims without target files and semantic domains cannot start.
  - Actual diff outside the claimed footprint blocks release and integration.
  - Two claims for the same semantic domain cannot coexist even when target paths differ.
  - Dependencies are checked across all active and completed work, not only one taskset view.
  - Generated shared views are modified only by their designated projection owner.
verification:
  - python -m pytest -q tests/test_footprint_conflict_gate.py tests/test_task_claim_dispatcher.py tests/test_task_unit_readiness_gate.py tests/test_wave_dispatcher.py tests/test_state_sync_gate.py
---

# TASK-AR-659 - Make footprints, semantic domains, and dependencies mandatory

## Goal

- Prevent duplicate or incompatible parallel work before dispatch, including overlaps that do not share exact file paths.

## Scope

- Fail closed on empty and escaped actual footprints, acquire semantic-domain ownership atomically, enforce dependencies globally, and keep generated/shared surfaces under a single projection owner.

## Acceptance Criteria

- Mutating claims without target files and semantic domains cannot start.
- Actual diff outside the claimed footprint blocks release and integration.
- Two claims for the same semantic domain cannot coexist even when target paths differ.
- Dependencies are checked across all active and completed work, not only one taskset view.
- Generated shared views are modified only by their designated projection owner.

## Verification

- `python -m pytest -q tests/test_footprint_conflict_gate.py tests/test_task_claim_dispatcher.py tests/test_task_unit_readiness_gate.py tests/test_wave_dispatcher.py tests/test_state_sync_gate.py`
