---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-639
display_id: TASK-AR-639
task_uid: 5affd6b2-dabd-4550-adf9-83a4282be1f0
work_id: TASK-AR-639
work_uid: 5affd6b2-dabd-4550-adf9-83a4282be1f0
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T19:18:44+09:00
started_at: 2026-07-28T17:55:15+09:00
title: Restore lifecycle truth and Work CLI producer-consumer parity
status: completed
priority: P0
difficulty: L
est_hours: 10
est_tokens: 24000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-639/UNIT-TASK-AR-639-001.md
reservation_id: RES-20260728-163601-b8c2a87a-01
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-175515-task-ar-639-639002.json
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Make registered work executable and make implemented-but-unclaimed work visible without fabricating history.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-07-28T19:18:31+09:00
verified_by: le-20260728-170130-kst-codexroot-v080-639-001
evidence_refs:
  - reviews/VERIFY-2026-07-28-task-ar-639-20260728191831.json
resolution: done
completed_at: 2026-07-28T19:18:44+09:00
closed_by: le-20260728-170130-kst-codexroot-v080-639-001
measurement_unavailable_reason: Task execution combined two units, repeated adversarial W4b repairs, PR and main CI, and historical recovery before reliable task-level time and token metering was available.
---

# TASK-AR-639 - Restore lifecycle truth and Work CLI producer-consumer parity

## Goal

- Make registered work executable and make implemented-but-unclaimed work visible without fabricating history.

## Scope

- Fix task registration/verification metadata parity, add an honest recovery representation for legacy missing-claim work, and make state reconciliation block projection drift.

## Acceptance Criteria

- A task produced by work.py new can be verified and closed without manual frontmatter repair.
- State reconciliation detects task, unit, claim, pointer, board, branch, and verification contradictions.
- Missing historical claims are represented as explicit recovery evidence and never synthesized as if W2 occurred.
- Unknown historical cost or duration is representable without writing a misleading zero.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_state_sync_gate.py -q`
- `python scripts/state_sync_gate.py --check`
- `python scripts/work_schema_gate.py --items --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-28T19:18:44+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Task execution combined two units, repeated adversarial W4b repairs, PR and main CI, and historical recovery before reliable task-level time and token metering was available.
- Closed by: `le-20260728-170130-kst-codexroot-v080-639-001`
- Evidence:
  - `reviews/VERIFY-2026-07-28-task-ar-639-20260728191831.json`
<!-- work-close:end -->
