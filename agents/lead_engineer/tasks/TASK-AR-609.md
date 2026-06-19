---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-609
display_id: TASK-AR-609
task_uid: c01a0cfe-be2a-4adf-aab5-c3bc71426ab9
work_id: TASK-AR-609
work_uid: c01a0cfe-be2a-4adf-aab5-c3bc71426ab9
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
registered_at: 2026-06-19T15:36:00+09:00
created_at: 2026-06-19T15:36:00+09:00
started_at: 2026-06-19T15:39:11+09:00
updated_at: 2026-06-19T16:01:00+09:00
title: Run Taskset Board IA design seminar
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 6000
owner: lead-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-609/UNIT-TASK-AR-609-001.md
reservation_id: RES-20260619-153600-cf31ceee-01
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Create a lead-designer seminar artifact that chooses how the next Taskset Board design cycle should reduce long target discovery and focus traversal without repeating the current card/list-heavy visual language by default.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-19T16:00:30+09:00
verified_by: codex-lead-designer-task-ar-609
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-609-20260619160030.json
resolution: done
completed_at: 2026-06-19T16:01:00+09:00
closed_by: codex-lead-designer-task-ar-609
actual_hours: 1.0
actual_tokens: 7000
---

# TASK-AR-609 - Run Taskset Board IA design seminar

## Goal

- Create a lead-designer seminar artifact that chooses how the next Taskset Board design cycle should reduce long target discovery and focus traversal without repeating the current card/list-heavy visual language by default.

## Scope

- Planning and evidence only. Do not edit UI source files. The seminar must cover typography, size and spacing, color and non-color cues, motion, effects, schema, assets, accessibility, responsiveness, and interaction recovery.

## Acceptance Criteria

- reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md records lead-designer, design-system-steward, interface-designer, and ux-evaluator viewpoints.
- The seminar uses the latest OAG mobile beta/W4B evidence and the 49-taskset board watch as the user problem, not a generic visual-refresh request.
- The seminar compares at least three direction options and selects one RFC candidate with rejected alternatives and rationale.
- The selected candidate states token, UI component, pattern component, and one-off implications before any implementation task is created.
- The seminar defines evidence requirements for font scale, density, color, animation, focus/effects, schema contracts, assets, accessibility, responsive behavior, and beta-tester interaction paths.

## Verification

- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T16:01:00+09:00`
- Resolution: `done`
- Actual hours: `1.0`
- Actual tokens: `7000`
- Closed by: `codex-lead-designer-task-ar-609`
- Evidence:
  - `reviews/VERIFY-2026-06-19-task-ar-609-20260619160030.json`
<!-- work-close:end -->
