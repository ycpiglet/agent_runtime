---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-595
display_id: TASK-AR-595
task_uid: 833d0b22-5c7f-4437-9e5e-f279653d625b
work_id: TASK-AR-595
work_uid: 833d0b22-5c7f-4437-9e5e-f279653d625b
kind: task
parent_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
registered_at: 2026-07-19T10:28:06+09:00
created_at: 2026-07-19T10:28:06+09:00
started_at: 2026-07-19T11:45:07+09:00
updated_at: 2026-07-19T11:54:41+09:00
title: Enforce isolated build prerequisites in host updater
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 6500
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-595/UNIT-TASK-AR-595-001.md
reservation_id: RES-20260719-102806-bbbc9438-02
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Remove the updater path that bypasses declared isolated build requirements and prove the generated/executed commands are safe.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_inventory_sync_sanitize.py -q
verification_status: passed
verified_at: 2026-07-19T11:51:27+09:00
verified_by: codex-root-task-ar-595
evidence_refs:
  - reviews/VERIFY-2026-07-19-task-ar-595-20260719115127.json
  - reviews/W4B-2026-07-19-TASK-AR-595.md
  - reviews/ROLE-REVIEW-2026-07-19-TASK-AR-595-INDEPENDENT-AUDITOR.md
resolution: done
completed_at: 2026-07-19T11:54:41+09:00
closed_by: codex-root-task-ar-595
actual_hours: 0.5
actual_tokens: 5000
---

# TASK-AR-595 - Enforce isolated build prerequisites in host updater

## Goal

- Resolve GitHub #287 so host updates honor pyproject build-system requirements instead of building with an incompatible ambient setuptools.

## Scope

- Change host update planning/execution and its tests; do not broaden the change to unrelated publish smoke paths without evidence.

## Acceptance Criteria

- Host updater no longer forces --no-build-isolation for an sdist/VCS install that declares setuptools>=68.
- Plan rendering and executable steps use the same build-isolation policy.
- Existing update trust, install-directory, sentinel, and sync checks still pass.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py -q`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-19T11:54:41+09:00`
- Resolution: `done`
- Actual hours: `0.5`
- Actual tokens: `5000`
- Closed by: `codex-root-task-ar-595`
- Evidence:
  - `reviews/VERIFY-2026-07-19-task-ar-595-20260719115127.json`
<!-- work-close:end -->
