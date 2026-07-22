---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-599
display_id: TASK-AR-599
task_uid: 15e52ef5-f082-4b97-a683-b319ee235386
work_id: TASK-AR-599
work_uid: 15e52ef5-f082-4b97-a683-b319ee235386
kind: task
parent_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
registered_at: 2026-07-19T10:28:06+09:00
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-22T17:31:48+09:00
title: Adopt never-blocking allimbot notifications
status: completed
priority: P1
difficulty: L
est_hours: 7
est_tokens: 15000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-599/UNIT-TASK-AR-599-001.md
reservation_id: RES-20260719-102806-bbbc9438-06
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Add local dashboard/ntfy notification support for task completion, governance blockage, session end, update notices, and CI failure with blank-by-default configuration.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_allimbot.py tests/test_update_notify.py tests/test_orchestrator_atomic_writes.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/verify_wheel_dotfiles.py --check
  - python scripts/owner_governance_gate.py
  - python scripts/regen_host_lock_if_needed.py --check
verification_status: passed
verified_at: 2026-07-22T17:25:33+09:00
verified_by: codex-root-task-ar-599-rework
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-599-20260722171444.json
  - reviews/VERIFY-2026-07-22-task-ar-599-20260722172533.json
resolution: done
completed_at: 2026-07-22T17:31:48+09:00
closed_by: codex-root-task-ar-599-closeout
actual_hours: 1.0
actual_tokens: 35000
---

# TASK-AR-599 - Adopt never-blocking allimbot notifications

## Goal

- Resolve GitHub #279 by shipping an optional, zero-dependency notification client and wiring the four proposed intervention points without making notification availability a runtime dependency.

## Scope

- Vendor the official allimbot client contract, provide package/template surfaces, optional hooks and CI wiring, documentation, and tests; never embed tokens or require a configured provider.

## Acceptance Criteria

- Unset notification configuration is a silent no-op everywhere.
- Every network error is bounded by a three-second timeout and cannot fail task completion, governance, SessionStart/Stop, update-notify, or CI.
- Task completion, governance blockage, session end, update notice, and CI failure have tested optional notification paths.
- No real secret or endpoint token is committed.

## Verification

- `python -m pytest tests/test_allimbot.py tests/test_update_notify.py tests/test_orchestrator_atomic_writes.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/verify_wheel_dotfiles.py --check`
- `python scripts/owner_governance_gate.py`
- `python scripts/regen_host_lock_if_needed.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-22T17:31:48+09:00`
- Resolution: `done`
- Actual hours: `1.0`
- Actual tokens: `35000`
- Closed by: `codex-root-task-ar-599-closeout`
- Evidence:
  - `reviews/VERIFY-2026-07-22-task-ar-599-20260722171444.json`
  - `reviews/VERIFY-2026-07-22-task-ar-599-20260722172533.json`
<!-- work-close:end -->
