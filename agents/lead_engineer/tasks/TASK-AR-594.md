---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-594
display_id: TASK-AR-594
task_uid: 49059d8b-28c1-41b1-a2ab-0abe48d05bd4
work_id: TASK-AR-594
work_uid: 49059d8b-28c1-41b1-a2ab-0abe48d05bd4
kind: task
parent_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
registered_at: 2026-07-19T10:28:06+09:00
created_at: 2026-07-19T10:28:06+09:00
started_at: 2026-07-19T10:32:13+09:00
updated_at: 2026-07-19T11:08:22+09:00
title: Honor canonical taskset task order
status: completed
priority: P0
difficulty: M
est_hours: 4
est_tokens: 9000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-594/UNIT-TASK-AR-594-001.md
reservation_id: RES-20260719-102806-bbbc9438-01
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Preserve task order declared by canonical taskset records throughout plan and dispatch.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_role_routing_wiring.py -q
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT --check
verification_status: passed
verified_at: 2026-07-19T11:07:41+09:00
verified_by: codex-root-task-ar-594-rework
evidence_refs:
  - reviews/VERIFY-2026-07-19-task-ar-594-20260719105444.json
  - reviews/VERIFY-2026-07-19-task-ar-594-20260719110741.json
failed_evidence_refs:
  - reviews/VERIFY-2026-07-19-task-ar-594-20260719110720.json
review_evidence_refs:
  - reviews/W4B-2026-07-19-TASK-AR-594-REWORK.md
  - reviews/ROLE-REVIEW-2026-07-19-TASK-AR-594-SKEPTIC.md
resolution: done
completed_at: 2026-07-19T11:08:22+09:00
closed_by: codex-root-task-ar-594-rework
actual_hours: 1.5
actual_tokens: 18000
---

# TASK-AR-594 - Honor canonical taskset task order

## Goal

- Resolve GitHub #289 so taskset dispatch selects explicit canonical task order before score-based fallback ordering.

## Scope

- Update taskset parsing/selection and focused tests in both the live script and host template mirror; do not change unrelated wave scheduling policy.

## Acceptance Criteria

- An explicit ordered task list TASK-219 -> TASK-220 -> TASK-217 is returned in that order even when score ordering differs.
- Tasksets without an explicit order retain deterministic existing fallback behavior.
- Live and template taskset_dispatcher implementations remain byte-equivalent where required.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py tests/test_role_routing_wiring.py -q`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-19T11:08:22+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `18000`
- Closed by: `codex-root-task-ar-594-rework`
- Evidence:
  - `reviews/VERIFY-2026-07-19-task-ar-594-20260719105444.json`
  - `reviews/VERIFY-2026-07-19-task-ar-594-20260719110741.json`
<!-- work-close:end -->
