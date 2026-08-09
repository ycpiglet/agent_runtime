---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-661
display_id: TASK-AR-661
task_uid: 0f135daf-4aa5-4d14-bd15-e2e1ca2b0d4d
work_id: TASK-AR-661
work_uid: 0f135daf-4aa5-4d14-bd15-e2e1ca2b0d4d
kind: task
parent_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
registered_at: 2026-08-09T12:00:00+09:00
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:20:00+09:00
title: Restore collision-safe work ledger and taskset authority
status: planned
priority: P1
difficulty: L
est_hours: 16
est_tokens: 32000
owner: lead-engineer
team: planning-office
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-661/UNIT-TASK-AR-661-001.md
reservation_id: RES-20260809-120000-5c48af85-02
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Repair the first-parent merge loss without overwriting canonical 653/654, and make the same ledger, taskset, or claim-identity corruption fail closed in owner governance.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-identity
  - ledger
  - merge-loss
  - data-integrity
  - red-first
review_refs:
  - reviews/REVIEW-2026-08-09-task-ar-661-existing-taskset-recovery-t3-replan.md
acceptance:
  - Every canonical task has one exact fulfilled reservation row and every fulfilled row resolves to the same task path and task_uid.
  - The ledger restores exactly 652 and 655-659 while the colliding old 653/654 reservations are never reintroduced as canonical rows.
  - Every taskset with explicit membership is exact in both directions and V080 no longer aliases the unrelated canonical 653/654 tasks.
  - An immutable recovery map binds lost task/unit UUIDs and historical claim digests to successor Tasks 662/663 without rewriting terminal artifacts.
  - New claims carry canonical work UUID binding and a reused display ID cannot appropriate historical claim authority.
  - The current Host Required Merge Gates task metadata is reconciled only from its own released claim and approved W4b evidence.
  - An audited receipt-first transaction moves staged successor Tasks 662/663 into the existing V080 taskset and initiative with exact task/unit UUID and reservation CAS.
  - Final V080 membership is 652, 662, 663, 655, 656, 657, 658, 659, while the correction taskset retains only 660/661.
verification:
  - PYTHONPATH=src python -m pytest tests/test_task_identity.py tests/test_task_identity_uuid7.py tests/test_taskset_work_gate.py tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_registration.py tests/test_backlog_board_tasksets.py -q
  - PYTHONPATH=src python -m pytest tests/test_owner_governance_chain_parity.py tests/test_owner_governance_consumer_host.py tests/test_state_sync_gate.py tests/test_template_mirror_gate.py tests/test_plan_assumption_gate.py -q
  - PYTHONPATH=src python scripts/task_identity.py check --check
  - PYTHONPATH=src python scripts/taskset_work_gate.py --check
  - PYTHONPATH=src python scripts/owner_governance_gate.py --check
depends_on:
  - TASK-AR-660
---

# TASK-AR-661 - Restore collision-safe work ledger and taskset authority

## Goal

- Repair the first-parent merge loss without overwriting canonical 653/654, and make the same ledger, taskset, or claim-identity corruption fail closed in owner governance.

## Scope

- Add inverse exact reservation validation, explicit taskset membership validation, an audited existing-taskset recovery transaction, immutable collision mapping, exact six-row ledger restoration, V080 membership correction, and stale Host Required Merge Gates closeout reconciliation.

## Acceptance Criteria

- Every canonical task has one exact fulfilled reservation row and every fulfilled row resolves to the same task path and task_uid.
- The ledger restores exactly 652 and 655-659 while the colliding old 653/654 reservations are never reintroduced as canonical rows.
- Every taskset with explicit membership is exact in both directions and V080 no longer aliases the unrelated canonical 653/654 tasks.
- An immutable recovery map binds lost task/unit UUIDs and historical claim digests to successor Tasks 662/663 without rewriting terminal artifacts.
- New claims carry canonical work UUID binding and a reused display ID cannot appropriate historical claim authority.
- The current Host Required Merge Gates task metadata is reconciled only from its own released claim and approved W4b evidence.
- An audited receipt-first transaction moves staged successor Tasks 662/663 into the existing V080 taskset and initiative with exact task/unit UUID and reservation CAS.
- Final V080 membership is 652, 662, 663, 655, 656, 657, 658, 659, while the correction taskset retains only 660/661.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_task_identity.py tests/test_task_identity_uuid7.py tests/test_taskset_work_gate.py tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_registration.py tests/test_backlog_board_tasksets.py -q`
- `PYTHONPATH=src python -m pytest tests/test_owner_governance_chain_parity.py tests/test_owner_governance_consumer_host.py tests/test_state_sync_gate.py tests/test_template_mirror_gate.py tests/test_plan_assumption_gate.py -q`
- `PYTHONPATH=src python scripts/task_identity.py check --check`
- `PYTHONPATH=src python scripts/taskset_work_gate.py --check`
- `PYTHONPATH=src python scripts/owner_governance_gate.py --check`
