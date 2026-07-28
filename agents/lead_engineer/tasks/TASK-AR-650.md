---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-650
display_id: TASK-AR-650
task_uid: a80a7fe2-ae55-4529-a8aa-c38319a0d6d8
work_id: TASK-AR-650
work_uid: a80a7fe2-ae55-4529-a8aa-c38319a0d6d8
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Rehearse Autofolio v0.6 to v0.8 migration
status: planned
priority: P0
difficulty: L
est_hours: 10
est_tokens: 20000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-650/UNIT-TASK-AR-650-001.md
reservation_id: RES-20260728-163601-b8c2a87a-12
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Prove the new ownership/profile model materially reduces Autofolio's unmanaged seams without changing product behavior.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-650 - Rehearse Autofolio v0.6 to v0.8 migration

## Goal

- Prove the new ownership/profile model materially reduces Autofolio's unmanaged seams without changing product behavior.

## Scope

- Run a clean migration plan and safe apply rehearsal, classify all current seams, and verify product tests without product feature changes.

## Acceptance Criteria

- Every current unmanaged path has a managed, seed_once, host_owned, generated, or temporary-conflict disposition.
- Temporary seams decrease materially.
- No Autofolio product file is silently overwritten.
- The v0.6 to RC migration is repeatable from a clean worktree.

## Verification

- `python scripts/pilot_acceptance.py --host autofolio --check`
- `python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q`
