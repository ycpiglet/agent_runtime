---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-609
display_id: TASK-AR-609
task_uid: 66ffb2ff-f4c4-43b6-bbf6-0c9700d4513a
work_id: TASK-AR-609
work_uid: 66ffb2ff-f4c4-43b6-bbf6-0c9700d4513a
kind: task
parent_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
registered_at: 2026-07-22T17:45:00+09:00
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-23T07:50:24+09:00
started_at: 2026-07-23T07:17:12+09:00
title: Classify initiative records by canonical kind
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 7000
owner: lead-engineer
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-609/UNIT-TASK-AR-609-001.md
reservation_id: RES-20260722-174500-dbaf8585-07
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Close GitHub issue 300 by preventing taskset records from being duplicated into the initiative level.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_work_item_classifier.py tests/test_template_work_item_classifier.py -q
  - python scripts/work_item_classifier.py --write --check
  - python scripts/regen_host_lock_if_needed.py --check
tags:
  - github-300
  - classifier
  - work-store
verification_status: passed
verified_at: 2026-07-23T07:31:37+09:00
verified_by: codex-root-task-ar-609
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-609-20260723072306.json
  - reviews/VERIFY-2026-07-23-task-ar-609-20260723073137.json
resolution: done
completed_at: 2026-07-23T07:50:24+09:00
closed_by: codex-root-task-ar-609
actual_hours: 0.6
actual_tokens: 28000
---

# TASK-AR-609 - Classify initiative records by canonical kind

## Goal

- Close GitHub #300 by preventing taskset records from being duplicated into the initiative level.

## Scope

- Close GitHub #300 by preventing taskset records from being duplicated into the initiative level.

## Acceptance Criteria

- Only kind=initiative records populate the initiative level.
- Canonical id/work_id fallback order is deterministic.
- Mixed initiative/taskset fixtures contain no cross-level duplicate IDs.

## Verification

- `python -m pytest tests/test_work_item_classifier.py tests/test_template_work_item_classifier.py -q`
- `python scripts/work_item_classifier.py --write --check`
- `python scripts/regen_host_lock_if_needed.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T07:50:24+09:00`
- Resolution: `done`
- Actual hours: `0.6`
- Actual tokens: `28000`
- Closed by: `codex-root-task-ar-609`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-609-20260723072306.json`
  - `reviews/VERIFY-2026-07-23-task-ar-609-20260723073137.json`
<!-- work-close:end -->
