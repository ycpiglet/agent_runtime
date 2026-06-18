---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-574
display_id: TASK-AR-574
task_uid: d1df7596-2722-48db-a3cc-4cd26068c3ed
work_id: TASK-AR-574
work_uid: d1df7596-2722-48db-a3cc-4cd26068c3ed
kind: task
parent_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
registered_at: 2026-06-17T17:15:00+09:00
created_at: 2026-06-17T17:15:00+09:00
updated_at: 2026-06-17T17:56:12+09:00
title: Route dormant monitored roles
status: completed
priority: P0
difficulty: M
est_hours: 2
est_tokens: 3000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-574/UNIT-TASK-AR-574-001.md
reservation_id: RES-20260617-171500-692625db-02
origin_type: owner_request
origin_ref: reviews/REPORT-2026-06-17-self-improvement-maturity.md
created_by: codex-planner
summary: Route council, progress-scout, release-steward, reviewer, and skeptic into real review or council evidence so monitored role gaps decrease.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
started_at: 2026-06-17T17:43:07+09:00
verification:
  - python scripts/collaboration_governance_gate.py --check
  - python scripts/self_improvement_cycle.py assess
  - python scripts/evidence_index_generator.py --check
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-17T17:55:59+09:00
verified_by: reviewer-20260617-role-evidence-574
evidence_refs:
  - reviews/VERIFY-2026-06-17-task-ar-574-20260617175559.json
resolution: done
completed_at: 2026-06-17T17:56:12+09:00
closed_by: reviewer-20260617-role-evidence-574
actual_hours: 1.1
actual_tokens: 3200
---

# TASK-AR-574 - Route dormant monitored roles

## Goal

- Route council, progress-scout, release-steward, reviewer, and skeptic into real review or council evidence so monitored role gaps decrease.

## Scope

- Use product-native review/council/seminar/task-claim evidence. Do not mark roles as exercised from prose alone.

## Acceptance Criteria

- At least three monitored role gaps are removed or converted into explicit blockers with evidence.
- A review/council record states which roles were exercised and which remain missing.
- self_improvement_cycle.py assess reports role_gaps lower than 6 or explains the blocker.

## Verification

- `python scripts/collaboration_governance_gate.py --check`
- `python scripts/self_improvement_cycle.py assess`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-17T17:56:12+09:00`
- Resolution: `done`
- Actual hours: `1.1`
- Actual tokens: `3200`
- Closed by: `reviewer-20260617-role-evidence-574`
- Evidence:
  - `reviews/VERIFY-2026-06-17-task-ar-574-20260617175559.json`
<!-- work-close:end -->
