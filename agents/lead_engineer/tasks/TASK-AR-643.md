---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-643
display_id: TASK-AR-643
task_uid: 34e50cc4-74b2-4fed-b538-6127b71a1efe
work_id: TASK-AR-643
work_uid: 34e50cc4-74b2-4fed-b538-6127b71a1efe
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T00:56:59+09:00
started_at: 2026-07-28T23:42:28+09:00
title: Enforce consumer template and skill dependency closure
status: completed
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-643/UNIT-TASK-AR-643-001.md
reservation_id: RES-20260728-163601-b8c2a87a-05
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Guarantee that every capability advertised to a clean host has all executable dependencies in the selected profile.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-234228-task-ar-643-643001.json
verification_status: passed
verified_at: 2026-07-29T00:53:18+09:00
verified_by: codex-root-v080-w6
evidence_refs:
  - reviews/VERIFY-2026-07-29-task-ar-643-20260729003452.json
  - reviews/VERIFY-2026-07-29-task-ar-643-20260729005318.json
resolution: done
completed_at: 2026-07-29T00:56:59+09:00
closed_by: codex-root-v080-w6
measurement_unavailable_reason: "\u001eagent-runtime-work-scalar-v1:Task execution included W0 revalidation, profile-aware dependency closure, generic work/session/report delivery, clean-host and built-wheel verification, independent W4b review, Python 3.10-3.12 CI, claim release, PR #364 integration at 442d31ef, and merged-main closeout before reliable task-level time and token metering was available."
---

# TASK-AR-643 - Enforce consumer template and skill dependency closure

## Goal

- Guarantee that every capability advertised to a clean host has all executable dependencies in the selected profile.

## Scope

- Add a dependency-closure gate, ship or rewire missing work/release/session helpers, and expand clean-host smoke to exercise declared skills.

## Acceptance Criteria

- Every shipped SKILL dependency exists in its effective profile.
- work.py and required helpers execute in a clean installed host.
- Template smoke exercises work status/new/verify and session closeout dependencies.
- Profile reduction never leaves dangling docs or hook commands.

## Verification

- `python -m pytest tests/test_template_smoke.py tests/test_runtime_asset_usage.py tests/test_wheel_dotfiles_packaging.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-29T00:56:59+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Task execution included W0 revalidation, profile-aware dependency closure, generic work/session/report delivery, clean-host and built-wheel verification, independent W4b review, Python 3.10-3.12 CI, claim release, PR #364 integration at 442d31ef, and merged-main closeout before reliable task-level time and token metering was available.
- Closed by: `codex-root-v080-w6`
- Evidence:
  - `reviews/VERIFY-2026-07-29-task-ar-643-20260729003452.json`
  - `reviews/VERIFY-2026-07-29-task-ar-643-20260729005318.json`
<!-- work-close:end -->
