---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-571
display_id: TASK-AR-571
task_uid: 610c4d58-2c09-437f-a8a1-0f6eeaa15d04
work_id: TASK-AR-571
work_uid: 610c4d58-2c09-437f-a8a1-0f6eeaa15d04
kind: task
parent_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
registered_at: 2026-06-17T08:31:23+09:00
created_at: 2026-06-17T08:31:23+09:00
started_at: 2026-06-17T09:02:21+09:00
updated_at: 2026-06-17T16:26:25+09:00
title: Generate product-native self-improvement cycle records
status: completed
priority: P0
difficulty: M
est_hours: 3
est_tokens: 2500
owner: lead_engineer
initiative_id: INIT-AR-SELF-IMPROVEMENT-CADENCE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-571/UNIT-TASK-AR-571-001.md
reservation_id: RES-20260617-083123-3d6cedc9-02
origin_type: owner_request
origin_ref: owner-request:low-frequency-agent-skill-self-improvement-cycle
created_by: codex-planner
summary: Use review, meeting, seminar, retro, compound, scribe, and doc-steward surfaces to record a real self-improvement cycle from the metrics baseline.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_self_improvement_cycle.py -q
  - python scripts/self_improvement_cycle.py cycle --dry-run --json
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-17T16:25:54+09:00
verified_by: le-20260617-090221-kst-969f
evidence_refs:
  - reviews/VERIFY-2026-06-17-task-ar-571-20260617162554.json
resolution: done
completed_at: 2026-06-17T16:26:25+09:00
closed_by: le-20260617-090221-kst-969f
actual_hours: 1.5
actual_tokens: 0
---

# TASK-AR-571 - Generate product-native self-improvement cycle records

## Goal

- Use review, meeting, seminar, retro, compound, scribe, and doc-steward surfaces to record a real self-improvement cycle from the metrics baseline.

## Scope

- Use review, meeting, seminar, retro, compound, scribe, and doc-steward surfaces to record a real self-improvement cycle from the metrics baseline.

## Acceptance Criteria

- A cycle command writes a dated REVIEW report and meeting/seminar plans tied to the current task.
- The cycle records retro forward actions and compound/casebook entries only when evidence shows recurring failure or repeated watch debt.
- The cycle explicitly records scribe/doc-steward advisory status and next-cycle thresholds.

## Verification

- `python -m pytest tests/test_self_improvement_cycle.py -q`
- `python scripts/self_improvement_cycle.py cycle --dry-run --json`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-17T16:26:25+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `0`
- Closed by: `le-20260617-090221-kst-969f`
- Evidence:
  - `reviews/VERIFY-2026-06-17-task-ar-571-20260617162554.json`
<!-- work-close:end -->
