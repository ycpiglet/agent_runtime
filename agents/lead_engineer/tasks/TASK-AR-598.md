---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-598
display_id: TASK-AR-598
task_uid: f8e1d34f-0149-42d8-b9a0-1a52d299c756
work_id: TASK-AR-598
work_uid: f8e1d34f-0149-42d8-b9a0-1a52d299c756
kind: task
parent_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
registered_at: 2026-07-19T10:28:06+09:00
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-22T16:39:03+09:00
title: Integrate crash-safe session resume audit
status: planned
priority: P1
difficulty: M
est_hours: 3
est_tokens: 7000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-598/UNIT-TASK-AR-598-001.md
reservation_id: RES-20260719-102806-bbbc9438-05
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Rebase the stale PR's report-only crash recovery auditor onto current main, preserve SessionStart order, and verify malformed state never blocks startup.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_session_resume_check.py tests/test_orchestrator_atomic_writes.py -q
  - python scripts/regen_host_lock_if_needed.py --check
verification_status: passed
verified_at: 2026-07-22T16:39:03+09:00
verified_by: codex-root-task-ar-598
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-598-20260722163903.json
---

# TASK-AR-598 - Integrate crash-safe session resume audit

## Goal

- Resolve GitHub #274 and supersede or merge PR #277 by shipping the host-proven session_resume_check in the current template.

## Scope

- Integrate PR #277 content, resolve current-main conflicts, and refresh tests/fixture lock; atomic session writes already landed in PR #276 and must remain intact.

## Acceptance Criteria

- The template ships session_resume_check.py and invokes it after interrupted_run_detector during SessionStart.
- Empty roots and malformed pointer/claim JSON remain non-blocking by default.
- PR #277 is merged or explicitly superseded by the integrated change and #274 is closed.

## Verification

- `python -m pytest tests/test_session_resume_check.py tests/test_orchestrator_atomic_writes.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`