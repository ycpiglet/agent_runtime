---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-596
display_id: TASK-AR-596
task_uid: 46edc6d6-3cff-48b9-9f5d-b70bb48c04e1
work_id: TASK-AR-596
work_uid: 46edc6d6-3cff-48b9-9f5d-b70bb48c04e1
kind: task
parent_id: TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
registered_at: 2026-06-21T19:00:00+09:00
created_at: 2026-06-21T19:00:00+09:00
started_at: 2026-06-21T19:20:00+09:00
updated_at: 2026-06-21T18:50:15+09:00
title: Create marketing campaign-readiness evidence packet for owner review
status: completed
priority: P1
difficulty: M
est_hours: 4
est_tokens: 6500
owner: lead_engineer
team: planning-office
initiative_id: INIT-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md
reservation_id: RES-20260621-190000-151c6745-01
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Prepare a reusable marketing campaign-readiness packet (constraints, claims, channels, and evidence expectations) that can be promoted to implementation only after owner approval.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION --check
  - python scripts/task_identity.py check --check
verification_status: passed
verified_at: 2026-06-21T18:49:21+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-06-21-task-ar-596-20260621184921.json
resolution: done
completed_at: 2026-06-21T18:50:15+09:00
closed_by: work.py close
actual_hours: 4
actual_tokens: 6500
---

# TASK-AR-596 - Create marketing campaign-readiness evidence packet for owner review

## Goal

- Prepare a reusable marketing campaign-readiness packet (constraints, claims, channels, and evidence expectations) that can be promoted to implementation only after owner approval.

## Scope

- Draft marketing execution packets only; no channel actions, message dispatch, or ad platform mutations.

## Acceptance Criteria

- Marketing lane draft packet exists with required outputs and in-scope/out-of-scope boundaries.
- Channel actions are explicitly marked as draft/owner-gated and do not require direct agent-side execution.
- Decision trigger and external-effect safeguards are explicit.
- Task and unit evidence commands are reproducible.

## Verification

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION --check`
- `python scripts/task_identity.py check --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-21T18:50:15+09:00`
- Resolution: `done`
- Actual hours: `4`
- Actual tokens: `6500`
- Closed by: `work.py close`
- Evidence:
  - `reviews/VERIFY-2026-06-21-task-ar-596-20260621184921.json`
<!-- work-close:end -->
