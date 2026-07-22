---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-607
display_id: TASK-AR-607
task_uid: 7d42af70-4f7a-4a00-a23d-32e6c57edada
work_id: TASK-AR-607
work_uid: 7d42af70-4f7a-4a00-a23d-32e6c57edada
kind: task
parent_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
registered_at: 2026-07-22T17:45:00+09:00
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-23T01:01:01+09:00
started_at: 2026-07-23T00:18:48+09:00
title: Make transient-spawn recovery testing deterministic
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 8000
owner: lead-engineer
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-607/UNIT-TASK-AR-607-001.md
reservation_id: RES-20260722-174500-dbaf8585-05
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Close GitHub issue 297 by isolating release-cadence transient-spawn recovery state so the regression cannot intermittently report false metrics.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_release_cadence_trigger.py -q
tags:
  - github-297
  - ci-flake
  - release-cadence
verification_status: passed
verified_at: 2026-07-23T00:39:10+09:00
verified_by: codex-root-task-ar-607
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-607-20260723003910.json
resolution: done
completed_at: 2026-07-23T01:01:01+09:00
closed_by: codex-root
actual_hours: 0.7
actual_tokens: 50000
---

# TASK-AR-607 - Make transient-spawn recovery testing deterministic

## Goal

- Close GitHub #297 by isolating release-cadence transient-spawn recovery state so the regression cannot intermittently report false metrics.

## Scope

- Close GitHub #297 by isolating release-cadence transient-spawn recovery state so the regression cannot intermittently report false metrics.

## Acceptance Criteria

- The transient-spawn recovery test passes repeatedly and in collection order.
- The test still proves one failed spawn followed by successful recovery.
- Release-cadence production behavior is unchanged unless a real isolation defect is proven.

## Verification

- `python -m pytest tests/test_release_cadence_trigger.py -q`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T01:01:01+09:00`
- Resolution: `done`
- Actual hours: `0.7`
- Actual tokens: `50000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-607-20260723003910.json`
<!-- work-close:end -->
