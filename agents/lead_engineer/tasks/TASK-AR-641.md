---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-641
display_id: TASK-AR-641
task_uid: eb3e329f-b0e1-4bfc-9a8f-de3bf752a38d
work_id: TASK-AR-641
work_uid: eb3e329f-b0e1-4bfc-9a8f-de3bf752a38d
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T21:55:47+09:00
started_at: 2026-07-28T20:54:00+09:00
title: Build brownfield adopt planning and generated-tree filtering
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
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-641/UNIT-TASK-AR-641-001.md
reservation_id: RES-20260728-163601-b8c2a87a-03
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Let an existing repository understand exactly what Agent Runtime would add, own, preserve, or conflict with before any mutation.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-205400-task-ar-641-641001.json
verification_status: passed
verified_at: 2026-07-28T21:55:09+09:00
verified_by: codex-root-v080-w6
evidence_refs:
  - reviews/VERIFY-2026-07-28-task-ar-641-20260728215509.json
  - reviews/VERIFY-2026-07-28-unit-task-ar-641-001-20260728213523.json
  - reviews/W4B-2026-07-28-unit-task-ar-641-001-approved.md
resolution: done
completed_at: 2026-07-28T21:55:47+09:00
closed_by: codex-root-v080-w6
measurement_unavailable_reason: Task execution included W0 revalidation, iterative adversarial W4b repair, live read-only Bean Wiki and Allimbot probes, local and Python 3.10-3.12 matrix CI, PR integration, and lifecycle closeout before reliable task-level time and token metering was available.
---

# TASK-AR-641 - Build brownfield adopt planning and generated-tree filtering

## Goal

- Let an existing repository understand exactly what Agent Runtime would add, own, preserve, or conflict with before any mutation.

## Scope

- Add adopt --plan, pre-adoption doctor mode, generated-directory filtering, host asset detection, and a machine-readable ownership/conflict report.

## Acceptance Criteria

- Bean Wiki and Allimbot inventory excludes generated and ignored trees.
- Existing AGENTS, Claude agents, skills, and product docs are detected as host assets.
- adopt --plan is read-only and reports planned writes and conflicts.
- doctor distinguishes pre-adoption readiness from broken installation.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py tests/test_doctor.py tests/test_adoption.py -q`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-28T21:55:47+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Task execution included W0 revalidation, iterative adversarial W4b repair, live read-only Bean Wiki and Allimbot probes, local and Python 3.10-3.12 matrix CI, PR integration, and lifecycle closeout before reliable task-level time and token metering was available.
- Closed by: `codex-root-v080-w6`
- Evidence:
  - `reviews/VERIFY-2026-07-28-task-ar-641-20260728215509.json`
  - `reviews/VERIFY-2026-07-28-unit-task-ar-641-001-20260728213523.json`
  - `reviews/W4B-2026-07-28-unit-task-ar-641-001-approved.md`
<!-- work-close:end -->
