---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-597
display_id: TASK-AR-597
task_uid: 5bb7344a-d7a0-4d4e-a8d4-853b4a3a03de
work_id: TASK-AR-597
work_uid: 5bb7344a-d7a0-4d4e-a8d4-853b4a3a03de
kind: task
parent_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
registered_at: 2026-07-19T10:28:06+09:00
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T12:21:24+09:00
title: Preserve Git stderr in release-auto test failures
status: planned
priority: P2
difficulty: S
est_hours: 1
est_tokens: 2500
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-597/UNIT-TASK-AR-597-001.md
reservation_id: RES-20260719-102806-bbbc9438-04
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Make the release-auto test helper raise a diagnostic error that retains the failing command and Git output.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_release_auto_noncritical.py -q
verification_status: passed
verified_at: 2026-07-19T12:21:24+09:00
verified_by: codex-root-task-ar-597
evidence_refs:
  - reviews/VERIFY-2026-07-19-task-ar-597-20260719122124.json
---

# TASK-AR-597 - Preserve Git stderr in release-auto test failures

## Goal

- Resolve GitHub #285 so transient Git setup failures include actionable stdout/stderr in pytest output.

## Scope

- Change the test helper and add regression coverage; do not alter production release behavior.

## Acceptance Criteria

- A failing helper reports the Git command, return code, stdout, and stderr.
- Successful helper calls retain existing behavior.
- Release-auto noncritical tests pass.

## Verification

- `python -m pytest tests/test_release_auto_noncritical.py -q`