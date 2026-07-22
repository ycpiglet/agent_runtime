---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-611
display_id: TASK-AR-611
task_uid: 7dd220e9-1b3d-41d5-a2b3-bf877ba7a8d2
work_id: TASK-AR-611
work_uid: 7dd220e9-1b3d-41d5-a2b3-bf877ba7a8d2
kind: task
parent_id: TASKSET-AR-BACKLOG-TASKSET-TEST-RECOVERY
registered_at: 2026-07-22T18:48:38+09:00
created_at: 2026-07-22T18:48:38+09:00
updated_at: 2026-07-22T19:33:55+09:00
title: Synchronize the real-backlog taskset expectation
status: planned
priority: P0
difficulty: XS
est_hours: 0.5
est_tokens: 2500
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-BACKLOG-TASKSET-TEST-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-BACKLOG-TASKSET-TEST-RECOVERY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-611/UNIT-TASK-AR-611-001.md
reservation_id: RES-20260722-184838-3dcdb3b7-01
origin_type: downstream_bug
origin_ref: github-actions:run-29909181630
created_by: codex-root-planner
summary: Make the real-backlog classification test recognize every taskset registered by the July remediation and PR
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python -m pytest tests -q
  - python scripts/taskset_work_gate.py --check
  - python scripts/rbac_write_gate.py --check
verification_status: passed
verified_at: 2026-07-22T19:33:55+09:00
verified_by: codex-root-task-ar-611
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-611-20260722193355.json
---

# TASK-AR-611 - Synchronize the real-backlog taskset expectation

## Goal

- Make the real-backlog classification test recognize every taskset registered by the July remediation and PR #303 CI-recovery work.

## Scope

- Update only the expected taskset IDs in tests/test_backlog_board_tasksets.py. Do not change backlog parsing, task classification behavior, or production code.

## Acceptance Criteria

- The expected set includes TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION, TASKSET-AR-PR303-CI-SCHEMA-RECOVERY, and TASKSET-AR-BACKLOG-TASKSET-TEST-RECOVERY.
- The focused backlog taskset test passes.
- The full tests suite passes under the same PYTHONPATH=src invocation used by CI.

## Verification

- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python -m pytest tests -q`
- `python scripts/taskset_work_gate.py --check`
- `python scripts/rbac_write_gate.py --check`