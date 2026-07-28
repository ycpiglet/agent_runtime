---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-649
display_id: TASK-AR-649
task_uid: 57d95039-80bf-4e22-b7f8-b8356dccf637
work_id: TASK-AR-649
work_uid: 57d95039-80bf-4e22-b7f8-b8356dccf637
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Run the Allimbot security-service pilot
status: planned
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: risk-and-safety
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-649/UNIT-TASK-AR-649-001.md
reservation_id: RES-20260728-163601-b8c2a87a-11
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Prove runtime adoption works in a mixed Python/Next/Supabase security-sensitive service and uses native Allimbot events.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-649 - Run the Allimbot security-service pilot

## Goal

- Prove runtime adoption works in a mixed Python/Next/Supabase security-sensitive service and uses native Allimbot events.

## Scope

- Use a clean Allimbot worktree, apply core plus security-service, complete ordinary and critical tasks plus offline event recovery, and keep production external effects blocked.

## Acceptance Criteria

- Existing product security and release policies remain host-owned.
- An ordinary task and a Critical task both complete with correct review routing.
- Offline native events spool and recover without secret leakage.
- No production deployment or credential change occurs.

## Verification

- `python scripts/pilot_acceptance.py --host allimbot --check`
- `python -m pytest tests/test_pilot_acceptance.py tests/test_allimbot.py -q`
