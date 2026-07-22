---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-610
display_id: TASK-AR-610
task_uid: 956cd4ea-4194-401f-aa1f-14a195623301
work_id: TASK-AR-610
work_uid: 956cd4ea-4194-401f-aa1f-14a195623301
kind: task
parent_id: TASKSET-AR-PR303-CI-SCHEMA-RECOVERY
registered_at: 2026-07-22T18:26:18+09:00
created_at: 2026-07-22T18:26:18+09:00
updated_at: 2026-07-22T20:03:03+09:00
title: Normalize legacy closeout evidence metadata
status: completed
started_at: 2026-07-22T18:27:20+09:00
priority: P0
difficulty: S
est_hours: 0.5
est_tokens: 3000
owner: lead-engineer
initiative_id: INIT-AR-PR303-CI-SCHEMA-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-PR303-CI-SCHEMA-RECOVERY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-610/UNIT-TASK-AR-610-001.md
reservation_id: RES-20260722-182618-821b1891-01
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
created_by: codex-root-planner
summary: Fold legacy closeout evidence keys into canonical evidence_refs or Markdown closeout records and restore PR
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python scripts/taskset_work_gate.py --check
  - python scripts/rbac_write_gate.py --check
  - python scripts/owner_governance_gate.py --allow-empty-owner-docs
verification_status: passed
tags:
  - pr-303
  - ci
  - work-schema
verified_at: 2026-07-22T18:36:40+09:00
verified_by: codex-root-task-ar-610
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-610-20260722183640.json
resolution: done
completed_at: 2026-07-22T20:03:03+09:00
closed_by: codex-root
actual_hours: 0.25
actual_tokens: 5000
---

# TASK-AR-610 - Normalize legacy failed verification evidence references

## Goal

- Make the existing TASK-AR-594 record satisfy the canonical work-item schema while preserving its failed verification evidence path.

## Scope

- Make the existing TASK-AR-594 record satisfy the canonical work-item schema while preserving its failed verification evidence path.

## Acceptance Criteria

- TASK-AR-594 contains no schema-unknown failed_evidence_refs key.
- All referenced W4a/W4b evidence paths remain linked from canonical evidence_refs.
- Implementation commit and remote closeout values remain recorded in Markdown.
- Taskset work, RBAC write, and Owner governance gates pass.

## Verification

- `python scripts/taskset_work_gate.py --check`
- `python scripts/rbac_write_gate.py --check`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-22T20:03:03+09:00`
- Resolution: `done`
- Actual hours: `0.25`
- Actual tokens: `5000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-22-task-ar-610-20260722183640.json`
<!-- work-close:end -->
