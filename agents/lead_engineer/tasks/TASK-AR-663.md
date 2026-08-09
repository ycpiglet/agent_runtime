---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-663
display_id: TASK-AR-663
task_uid: 310e61ee-3054-4566-8a16-6e25444221af
work_id: TASK-AR-663
work_uid: 310e61ee-3054-4566-8a16-6e25444221af
kind: task
parent_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
registered_at: 2026-08-09T12:00:00+09:00
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:00:00+09:00
title: Re-key and finish the lost V080 Compound work
status: planned
priority: P1
difficulty: L
est_hours: 16
est_tokens: 32000
owner: lead-engineer
team: quality
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-663/UNIT-TASK-AR-663-001.md
reservation_id: RES-20260809-120000-5c48af85-04
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Restore collision-free authority for the integrated repeated-failure Compound work and truthfully close or expose every remaining verification blocker.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - compound
  - identity-recovery
  - repeated-failure
  - red-first
acceptance:
  - The new task is linked to lost task_uid ef3cb8e5-d5b9-443e-ad93-5948ade62659, its worker claims, role overlays, review chain, and append-only Compound records by immutable digest.
  - Repeated-failure closure requires complete canonical Compound coverage and a prevention destination while ordinary substantial work retains review/retro compatibility.
  - The consumer failure-to-regression skill remains registered and template parity holds.
  - Fresh skeptic and independent W4b have zero P0/P1 for locally testable scope; unavailable native-Windows evidence remains an explicit release blocker rather than a false pass.
  - No historical task, unit, claim, review, receipt, or Compound record is rewritten.
verification:
  - PYTHONPATH=src python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_claim_store.py tests/test_atomic_io.py -q
  - PYTHONPATH=src python scripts/compound_record.py --check
  - PYTHONPATH=src python scripts/runtime_asset_usage.py --check
  - PYTHONPATH=src python scripts/template_mirror_gate.py --check
depends_on:
  - TASK-AR-662
---

# TASK-AR-663 - Re-key and finish the lost V080 Compound work

## Goal

- Restore collision-free authority for the integrated repeated-failure Compound work and truthfully close or expose every remaining verification blocker.

## Scope

- Claim normally, bind all historical claims/reviews/Compound records to the new identity, re-run current closure and failure-to-regression behavior, repair current reds, and obtain fresh skeptic plus independent W4b.

## Acceptance Criteria

- The new task is linked to lost task_uid ef3cb8e5-d5b9-443e-ad93-5948ade62659, its worker claims, role overlays, review chain, and append-only Compound records by immutable digest.
- Repeated-failure closure requires complete canonical Compound coverage and a prevention destination while ordinary substantial work retains review/retro compatibility.
- The consumer failure-to-regression skill remains registered and template parity holds.
- Fresh skeptic and independent W4b have zero P0/P1 for locally testable scope; unavailable native-Windows evidence remains an explicit release blocker rather than a false pass.
- No historical task, unit, claim, review, receipt, or Compound record is rewritten.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_claim_store.py tests/test_atomic_io.py -q`
- `PYTHONPATH=src python scripts/compound_record.py --check`
- `PYTHONPATH=src python scripts/runtime_asset_usage.py --check`
- `PYTHONPATH=src python scripts/template_mirror_gate.py --check`
