---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-610
display_id: TASK-AR-610
task_uid: f31057dc-15b3-4b7e-a512-834bdfa5201c
work_id: TASK-AR-610
work_uid: f31057dc-15b3-4b7e-a512-834bdfa5201c
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
registered_at: 2026-06-19T15:36:00+09:00
created_at: 2026-06-19T15:36:00+09:00
started_at: 2026-06-19T16:14:00+09:00
updated_at: 2026-06-19T18:08:00+09:00
title: Publish Taskset Board IA design RFC
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 7000
owner: lead-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
reservation_id: RES-20260619-153600-cf31ceee-02
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Promote the seminar decision into an accepted design-direction RFC that names the exact IA, visual, token, component, pattern, schema, and beta-evidence boundaries allowed for the next implementation round.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
  - python scripts/ui_ux_cycle.py --root . propose --dry-run --json
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-19T18:00:00+09:00
verified_by: codex-lead-designer-task-ar-610-resume
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-610-20260619174130.json
  - reviews/VERIFY-2026-06-19-task-ar-610-20260619180000.json
resolution: done
completed_at: 2026-06-19T18:08:00+09:00
closed_by: codex-lead-designer-task-ar-610-resume
actual_hours: 1.4
actual_tokens: 9000
---

# TASK-AR-610 - Publish Taskset Board IA design RFC

## Goal

- Promote the seminar decision into an accepted design-direction RFC that names the exact IA, visual, token, component, pattern, schema, and beta-evidence boundaries allowed for the next implementation round.

## Scope

- RFC and accepted design-system documentation only. Do not edit UI source files. Update DESIGN.md or DESIGN-SYSTEM.md only for promoted reusable rules or asset contracts.

## Acceptance Criteria

- reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md states the selected IA/visual direction, target workflow, references, rejected alternatives, risks, and promotion decision.
- The RFC defines typography, density, color/non-color state, motion, effects/focus, schema, assets, accessibility, responsiveness, and interaction requirements for the next implementation.
- The RFC lists minimum design-token, UI-component, pattern-component, and one-off boundaries before implementation.
- DESIGN.md and DESIGN-SYSTEM.md are updated only when the RFC promotes a reusable rule or asset contract.
- The RFC defines beta-tester and UX-evaluator evidence for the next implementation round.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T18:08:00+09:00`
- Resolution: `done`
- Actual hours: `1.4`
- Actual tokens: `9000`
- Closed by: `codex-lead-designer-task-ar-610-resume`
- Evidence:
  - `reviews/VERIFY-2026-06-19-task-ar-610-20260619174130.json`
  - `reviews/VERIFY-2026-06-19-task-ar-610-20260619180000.json`
<!-- work-close:end -->
