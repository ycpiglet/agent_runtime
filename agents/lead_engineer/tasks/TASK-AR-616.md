---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-616
display_id: TASK-AR-616
task_uid: 3ff2023d-2a58-4fd9-b3a6-c2b8eafda4d4
work_id: TASK-AR-616
work_uid: 3ff2023d-2a58-4fd9-b3a6-c2b8eafda4d4
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
registered_at: 2026-06-19T23:39:00+09:00
created_at: 2026-06-19T23:39:00+09:00
started_at: 2026-06-19T23:58:57+09:00
updated_at: 2026-06-20T00:23:22+09:00
verification_status: passed
verified_at: 2026-06-20T00:23:00+09:00
verified_by: independent-w4b-task-ar-616-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-616-closeout.json
w4b_evidence: reviews/W4B-2026-06-20-TASK-AR-616.md
title: Run Taskset Board evidence and performance IA seminar
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 7000
owner: lead-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-616/UNIT-TASK-AR-616-001.md
reservation_id: RES-20260619-233900-c1780e1d-01
origin_type: beta_followup
origin_ref: reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md
created_by: codex-ux-evaluator-ar-615
summary: Create a lead-designer seminar artifact that chooses the next Taskset Board IA direction for high evidence-gap counts, slow state loading, and inactive-view layout containment without guessing the implementation before design review.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
resolution: done
completed_at: 2026-06-20T00:23:22+09:00
closed_by: codex-lead-designer-ar-616
actual_hours: 2
actual_tokens: 7000
---

# TASK-AR-616 - Run Taskset Board evidence and performance IA seminar

## Goal

- Create a lead-designer seminar artifact that chooses the next Taskset Board IA direction for high evidence-gap counts, slow state loading, and inactive-view layout containment without guessing the implementation before design review.

## Scope

- Planning and evidence only. Do not edit UI source files. The seminar must cover typography, size and spacing, color and non-color cues, motion, effects, schema, assets, accessibility, responsiveness, interaction recovery, and state-loading budget.

## Acceptance Criteria

- reviews/SEMINAR-2026-06-19-taskset-board-evidence-performance-ia.md records lead-designer, design-system-steward, interface-designer, ux-evaluator, and beta-tester viewpoints.
- The seminar uses TASK-AR-615 evidence as input: evidence_gaps=49, live /api/tasksets_board latency watch, and inactive-view wide-child scan noise.
- The seminar compares at least three directions: stale-evidence grouping, progressive disclosure with lane cap disclosure, and performance-split board loading.
- The selected candidate states design_token, ui_component, pattern_component, and one_off_for_now implications before any implementation task is created.
- The seminar defines evidence requirements for font scale, density, color, animation, focus/effects, schema contracts, assets, accessibility, responsive behavior, beta-tester interaction paths, and API latency.

## Verification

- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-20T00:23:22+09:00`
- Resolution: `done`
- Actual hours: `2`
- Actual tokens: `7000`
- Closed by: `codex-lead-designer-ar-616`
- Evidence:
  - `reviews/VERIFY-2026-06-20-task-ar-616-closeout.json`
<!-- work-close:end -->
