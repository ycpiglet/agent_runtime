---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-570
display_id: TASK-AR-570
task_uid: f004f017-f9e9-44be-bab3-cd86851b6edd
work_id: TASK-AR-570
work_uid: f004f017-f9e9-44be-bab3-cd86851b6edd
kind: task
parent_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
registered_at: 2026-06-17T08:31:23+09:00
created_at: 2026-06-17T08:31:23+09:00
updated_at: 2026-06-17T08:50:16+09:00
started_at: 2026-06-17T08:35:06+09:00
title: Measure low-frequency role and asset usage
status: completed
priority: P0
difficulty: M
est_hours: 3
est_tokens: 2500
owner: lead_engineer
initiative_id: INIT-AR-SELF-IMPROVEMENT-CADENCE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-570/UNIT-TASK-AR-570-001.md
reservation_id: RES-20260617-083123-3d6cedc9-01
origin_type: owner_request
origin_ref: owner-request:low-frequency-agent-skill-self-improvement-cycle
created_by: codex-planner
summary: Create a deterministic baseline that identifies low-frequency agent roles, low-reuse skills/assets, waiver debt, and missing product-surface evidence from current repository state.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_self_improvement_cycle.py -q
  - python scripts/self_improvement_cycle.py assess --json
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-17T08:50:00+09:00
verified_by: le-20260617-083506-kst-3845
evidence_refs:
  - reviews/VERIFY-2026-06-17-task-ar-570-20260617085000.json
resolution: done
completed_at: 2026-06-17T08:50:16+09:00
closed_by: le-20260617-083506-kst-3845
actual_hours: 1.2
actual_tokens: 0
---

# TASK-AR-570 - Measure low-frequency role and asset usage

## Goal

- Create a deterministic baseline that identifies low-frequency agent roles, low-reuse skills/assets, waiver debt, and missing product-surface evidence from current repository state.

## Scope

- Create a deterministic baseline that identifies low-frequency agent roles, low-reuse skills/assets, waiver debt, and missing product-surface evidence from current repository state.

## Acceptance Criteria

- A repeatable command emits role coverage, monitored-role gaps, waived missing-role debt, asset usage/reuse, and advisory scribe/doc-steward status as structured metrics.
- The command classifies each low-frequency role or asset with an evidence-based root cause, not only a missing trigger string.
- Focused tests cover pass, watch, and root-cause classification behavior.

## Verification

- `python -m pytest tests/test_self_improvement_cycle.py -q`
- `python scripts/self_improvement_cycle.py assess --json`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-17T08:50:16+09:00`
- Resolution: `done`
- Actual hours: `1.2`
- Actual tokens: `0`
- Closed by: `le-20260617-083506-kst-3845`
- Evidence:
  - `reviews/VERIFY-2026-06-17-task-ar-570-20260617085000.json`
<!-- work-close:end -->
