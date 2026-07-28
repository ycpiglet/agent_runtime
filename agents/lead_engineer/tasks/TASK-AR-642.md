---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-642
display_id: TASK-AR-642
task_uid: b1117f99-eb93-4481-9e0d-35c08aa4954d
work_id: TASK-AR-642
work_uid: b1117f99-eb93-4481-9e0d-35c08aa4954d
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T23:17:36+09:00
started_at: 2026-07-28T22:14:34+09:00
title: Make sync ownership-aware and explicitly reconcilable
status: completed
priority: P0
difficulty: L
est_hours: 12
est_tokens: 26000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-642/UNIT-TASK-AR-642-001.md
reservation_id: RES-20260728-163601-b8c2a87a-04
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Update safe runtime files without overwriting host state or allowing one expected seam to freeze every unrelated update.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-221434-task-ar-642-642001.json
verification_status: passed
verified_at: 2026-07-28T23:14:33+09:00
verified_by: codex-root-v080-w6
evidence_refs:
  - reviews/VERIFY-2026-07-28-task-ar-642-20260728231433.json
  - reviews/W4B-2026-07-28-unit-task-ar-642-001-approved.md
resolution: done
completed_at: 2026-07-28T23:17:36+09:00
closed_by: codex-root-v080-w6
measurement_unavailable_reason: Task execution included W0 revalidation, ownership-aware sync and lock v2 delivery, two adversarial W4b repair rounds, local and Python 3.10-3.12 matrix CI, claim release, PR integration, and lifecycle closeout before reliable task-level time and token metering was available.
---

# TASK-AR-642 - Make sync ownership-aware and explicitly reconcilable

## Goal

- Update safe runtime files without overwriting host state or allowing one expected seam to freeze every unrelated update.

## Scope

- Apply profile-selected manifests and ownership modes, provide a non-mutating reconcile report, and permit explicit safe-only application without silent merge.

## Acceptance Criteria

- seed_once files stop being managed after installation.
- host_owned and generated files are never overwritten.
- Safe managed updates can be selected explicitly while conflicts remain reported.
- Pinned upstream ref, not the locally installed template version, drives comparison.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py tests/test_doctor.py tests/test_template_smoke.py -q`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-28T23:17:36+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Task execution included W0 revalidation, ownership-aware sync and lock v2 delivery, two adversarial W4b repair rounds, local and Python 3.10-3.12 matrix CI, claim release, PR integration, and lifecycle closeout before reliable task-level time and token metering was available.
- Closed by: `codex-root-v080-w6`
- Evidence:
  - `reviews/VERIFY-2026-07-28-task-ar-642-20260728231433.json`
  - `reviews/W4B-2026-07-28-unit-task-ar-642-001-approved.md`
<!-- work-close:end -->
