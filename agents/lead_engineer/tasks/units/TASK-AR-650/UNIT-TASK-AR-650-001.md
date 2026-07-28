---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-650-001
work_uid: 181ee6f3-421b-4508-80ef-f80c7befa641
kind: unit
parent_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_id: TASK-AR-650
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Execute and document the Autofolio migration rehearsal
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Autofolio is pinned to v0.6.0 and uses the right framework/overlay/seam design, but carries 21 unmanaged entries caused by host data, product context, and upstream defects.
inputs:
  - ../autofolio/agent_runtime.yml
  - ../autofolio/docs/AGENT_RUNTIME_INTEGRATION.md
  - ../autofolio/docs/agent_runtime_feedback.md
target_files:
  - tests/fixtures/pilots/autofolio
  - reviews/PILOT-AUTOFOLIO-MIGRATION-v080.md
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
scope: Rehearse configuration migration and safe sync in a clean Autofolio worktree. Do not implement or alter investment-product behavior.
acceptance:
  - Migration is idempotent.
  - Live host data is not managed.
  - Every remaining seam has an explicit host-specific reason.
  - Product tests remain green.
verification:
  - python scripts/pilot_acceptance.py --host autofolio --check
  - python -m pytest tests/test_pilot_acceptance.py -q
handoff: Attach the seam ledger, migration diff, host verification, and rollback instructions.
stop_condition: Stop before product feature changes, live trading effects, origin push, or main-branch mutation.
---

# UNIT-TASK-AR-650-001 - Execute and document the Autofolio migration rehearsal

## Context

Autofolio is pinned to v0.6.0 and uses the right framework/overlay/seam design, but carries 21 unmanaged entries caused by host data, product context, and upstream defects.

## Inputs

- ../autofolio/agent_runtime.yml
- ../autofolio/docs/AGENT_RUNTIME_INTEGRATION.md
- ../autofolio/docs/agent_runtime_feedback.md

## Target Files

- tests/fixtures/pilots/autofolio
- reviews/PILOT-AUTOFOLIO-MIGRATION-v080.md
- scripts/pilot_acceptance.py
- tests/test_pilot_acceptance.py

## Scope

Rehearse configuration migration and safe sync in a clean Autofolio worktree. Do not implement or alter investment-product behavior.

## Steps

1. Snapshot v0.6 ownership and seams.
2. Generate v0.8 migration and reconcile plans.
3. Apply only safe managed updates.
4. Run host verification and quantify remaining seams.

## Acceptance Criteria

- Migration is idempotent.
- Live host data is not managed.
- Every remaining seam has an explicit host-specific reason.
- Product tests remain green.

## Verification

- `python scripts/pilot_acceptance.py --host autofolio --check`
- `python -m pytest tests/test_pilot_acceptance.py -q`

## Handoff

Attach the seam ledger, migration diff, host verification, and rollback instructions.

## Stop Boundary

Stop before product feature changes, live trading effects, origin push, or main-branch mutation.
