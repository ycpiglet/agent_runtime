---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-600
display_id: TASK-AR-600
task_uid: 99ec8f63-17da-485c-b398-c78a154d07ce
work_id: TASK-AR-600
work_uid: 99ec8f63-17da-485c-b398-c78a154d07ce
kind: task
parent_id: TASKSET-AR-AUTO-MERGE-INTEGRITY
registered_at: 2026-07-19T10:34:25+09:00
created_at: 2026-07-19T10:34:25+09:00
updated_at: 2026-07-22T18:05:29+09:00
title: Confirm remote merge state before success
status: planned
priority: P1
difficulty: M
est_hours: 1
est_tokens: 1000
owner: lead_engineer
initiative_id: INIT-AR-AUTO-MERGE-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTO-MERGE-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-600/UNIT-TASK-AR-600-001.md
reservation_id: RES-20260719-103425-89ccc7c0-01
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-19-auto-merge-execution-readback.md
created_by: codex-root
summary: Make auto_merge execute fail closed when GitHub rejects a merge and preserve success only after a remote MERGED read-back.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/owner_governance_gate.py --allow-empty-owner-docs
verification_status: passed
tags:
  - work-cli-created
verified_at: 2026-07-22T18:05:29+09:00
verified_by: codex-root-task-ar-600-rework
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-600-20260722175324.json
  - reviews/VERIFY-2026-07-22-task-ar-600-20260722175452.json
  - reviews/VERIFY-2026-07-22-task-ar-600-20260722175618.json
  - reviews/VERIFY-2026-07-22-task-ar-600-20260722180529.json
---

# TASK-AR-600 - Confirm remote merge state before success

## Goal

- Make auto_merge execute fail closed when GitHub rejects a merge and preserve success only after a remote MERGED read-back.

## Scope

- Make auto_merge execute fail closed when GitHub rejects a merge and preserve success only after a remote MERGED read-back.

## Acceptance Criteria

- Draft merge rejection returns nonzero and does not report success.
- Remote MERGED read-back preserves success when only local cleanup fails.
- Existing auto-merge surface behavior remains unchanged.

## Verification

- `python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`