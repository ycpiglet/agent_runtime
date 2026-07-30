---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-655
display_id: TASK-AR-655
task_uid: de3c2768-cf2b-4fc5-aad6-160071e91f3e
work_id: TASK-AR-655
work_uid: de3c2768-cf2b-4fc5-aad6-160071e91f3e
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T12:00:00+09:00
title: Add atomic heartbeat and renewal to task claims
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-655/UNIT-TASK-AR-655-001.md
reservation_id: RES-20260730-112500-842c7890-04
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Keep long-running task claims truthful and make expiry consistent across claim, pointer, Doctor, state sync, and UI.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
acceptance:
  - task_claim_dispatcher exposes atomic owner-checked heartbeat and renew commands.
  - Heartbeat updates claim top-level and nested lease timestamps together.
  - Wrong owner, expired claim, timestamp regression, and concurrent renewal fail closed.
  - A replan-aware renewal binds the current task, unit, target-file, and stop-boundary digests without silently broadening the prior claim.
  - Doctor, state sync, worktree lifecycle, and UI use one expiry interpretation.
  - Progress updates cannot leave an active pointer paired with an expired claim.
verification:
  - python -m pytest tests/test_task_claim_dispatcher.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py -q
---

# TASK-AR-655 - Add atomic heartbeat and renewal to task claims

## Goal

- Keep long-running task claims truthful and make expiry consistent across claim, pointer, Doctor, state sync, and UI.

## Scope

- Add owner-checked task claim heartbeat/renew, wire progress updates to it, and reconcile expired active claims across every consumer.

## Acceptance Criteria

- task_claim_dispatcher exposes atomic owner-checked heartbeat and renew commands.
- Heartbeat updates claim top-level and nested lease timestamps together.
- Wrong owner, expired claim, timestamp regression, and concurrent renewal fail closed.
- A replan-aware renewal binds the current task, unit, target-file, and stop-boundary digests without silently broadening the prior claim.
- Doctor, state sync, worktree lifecycle, and UI use one expiry interpretation.
- Progress updates cannot leave an active pointer paired with an expired claim.

## Verification

- `python -m pytest tests/test_task_claim_dispatcher.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py -q`
