---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-618
display_id: TASK-AR-618
task_uid: 30389a6c-e64c-42f4-9b99-df4c280ff6b7
work_id: TASK-AR-618
work_uid: 30389a6c-e64c-42f4-9b99-df4c280ff6b7
kind: task
parent_id: TASKSET-AR-WORK-CLI-INTEGRITY
registered_at: 2026-07-23T08:40:51+09:00
created_at: 2026-07-23T08:40:51+09:00
updated_at: 2026-07-23T12:39:01+09:00
started_at: 2026-07-23T12:15:49+09:00
title: Resolve exact task and unit selectors deterministically
status: completed
priority: P1
difficulty: S
est_hours: 2
est_tokens: 5000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-WORK-CLI-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-618/UNIT-TASK-AR-618-001.md
reservation_id: RES-20260723-084051-a1975741-02
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-work-cli-integrity-design.md
created_by: codex-root-planner
summary: Give exact task records and exact unit records deterministic selector precedence while preserving genuine ambiguity failures.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_work_verify.py tests/test_work_close.py tests/test_work_assign.py tests/test_work_criteria.py -q
  - python scripts/work_schema_gate.py --check
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-07-23T12:38:00+09:00
verified_by: /root/task-ar-618
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-618-20260723123800.json
resolution: done
completed_at: 2026-07-23T12:39:01+09:00
closed_by: /root/task-ar-618
actual_hours: 1.5
actual_tokens: 7000
---

# TASK-AR-618 - Resolve exact task and unit selectors deterministically

## Goal

- Allow generic work commands to address a canonical task by exact ID without treating its descendant units as competing matches.

## Scope

- Change only scripts/work.py candidate resolution and focused verify, close, assign, and criteria tests; do not alter hierarchy or command-specific mutation contracts.

## Acceptance Criteria

- An exact task ID resolves only the canonical task record even when one or more units exist below it.
- An exact unit ID and an explicit relative or absolute path retain their current deterministic behavior.
- Missing records and genuinely duplicated canonical unit records remain bounded failures rather than arbitrary selection.

## Verification

- `python -m pytest tests/test_work_verify.py tests/test_work_close.py tests/test_work_assign.py tests/test_work_criteria.py -q`
- `python scripts/work_schema_gate.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T12:39:01+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `7000`
- Closed by: `/root/task-ar-618`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-618-20260723123800.json`
<!-- work-close:end -->
