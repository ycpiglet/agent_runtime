---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-575
display_id: TASK-AR-575
task_uid: 93fe873f-43f5-4874-98cb-f92e4126139a
work_id: TASK-AR-575
work_uid: 93fe873f-43f5-4874-98cb-f92e4126139a
kind: task
parent_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
registered_at: 2026-06-17T17:15:00+09:00
created_at: 2026-06-17T17:15:00+09:00
updated_at: 2026-06-17T18:22:52+09:00
title: Exercise or retire low-reuse runtime assets
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 3500
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-575/UNIT-TASK-AR-575-001.md
reservation_id: RES-20260617-171500-692625db-03
origin_type: owner_request
origin_ref: reviews/REPORT-2026-06-17-self-improvement-maturity.md
created_by: codex-planner
summary: Reduce low-reuse runtime asset debt by exercising valuable assets in real workflows or deprecating assets that should no longer be kept.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
started_at: 2026-06-17T18:00:00+09:00
verification:
  - python scripts/runtime_asset_usage.py --check
  - python scripts/self_improvement_cycle.py assess
  - python scripts/evidence_index_generator.py --check
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-17T18:22:32+09:00
verified_by: release-steward-20260617-runtime-assets-575
evidence_refs:
  - reviews/VERIFY-2026-06-17-task-ar-575-20260617182232.json
resolution: done
completed_at: 2026-06-17T18:22:52+09:00
closed_by: release-steward-20260617-runtime-assets-575
actual_hours: 1.6
actual_tokens: 4200
---

# TASK-AR-575 - Exercise or retire low-reuse runtime assets

## Goal

- Reduce low-reuse runtime asset debt by exercising valuable assets in real workflows or deprecating assets that should no longer be kept.

## Scope

- Use the runtime asset registry and usage gate. Do not game usage counts with dummy references.

## Acceptance Criteria

- Low-reuse asset count decreases toward the target_next threshold.
- Each changed asset has keep, exercise, modify, or deprecate rationale.
- runtime_asset_usage.py --check and self_improvement_cycle.py assess reflect the new state.

## Verification

- `python scripts/runtime_asset_usage.py --check`
- `python scripts/self_improvement_cycle.py assess`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-17T18:22:52+09:00`
- Resolution: `done`
- Actual hours: `1.6`
- Actual tokens: `4200`
- Closed by: `release-steward-20260617-runtime-assets-575`
- Evidence:
  - `reviews/VERIFY-2026-06-17-task-ar-575-20260617182232.json`
<!-- work-close:end -->
