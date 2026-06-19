---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-609-001
work_uid: 294ef1cb-2964-4577-9025-a3fc40cf7c05
kind: unit
parent_id: TASK-AR-609
unit_id: UNIT-TASK-AR-609-001
task_id: TASK-AR-609
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
initiative_id: INIT-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-designer
created_at: 2026-06-19T15:36:00+09:00
updated_at: 2026-06-19T16:00:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Run Taskset Board IA lead-designer seminar
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-608 closed the mobile overflow refinement, but its independent verification recorded a next-cycle watch: Taskset Board currently contains 49 tasksets, so target discovery and whole-board focus traversal are long. The next UI/UX loop should select a stronger information architecture and visual direction before mutating UI source.
inputs:
  - reviews/W4B-2026-06-19-TASK-AR-608.md
  - reviews/BETA-TEST-2026-06-19-oag-mobile-responsive-refinement.md
  - reviews/UX-EVAL-2026-06-19-oag-mobile-responsive-refinement.md
  - reviews/RFC-2026-06-19-ui-ux-design-direction.md
  - docs/design/agent-runtime/DESIGN.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - scripts/ui_ux_cycle.py
target_files:
  - reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md
  - reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
  - reviews/INDEX.md
scope: Write the seminar decision artifact and refresh the evidence index only. Do not patch docs/design or UI source files in this unit.
acceptance:
  - The seminar is specific enough for a planner to write the RFC task without chat context.
  - Every UI quality dimension has concrete evidence expectations and an assetization class.
  - The chosen direction has explicit implementation boundaries, schema expectations, and a beta-tester follow-up path.
  - No source UI files are changed by this unit.
verification:
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
handoff: Report the selected Taskset Board IA direction, rejected alternatives, assetization implications, RFC target files, and next beta/UX evidence path.
stop_condition: Stop after seminar evidence is complete and ready for independent verification or RFC claim.
verified_at: 2026-06-19T15:58:30+09:00
verified_by: codex-lead-designer-task-ar-609
evidence_refs:
  - reviews/VERIFY-2026-06-19-unit-task-ar-609-001-20260619155830.json
resolution: done
completed_at: 2026-06-19T16:00:00+09:00
closed_by: codex-lead-designer-task-ar-609
actual_hours: 0.8
actual_tokens: 6000
---

# UNIT-TASK-AR-609-001 - Run Taskset Board IA lead-designer seminar

## Context

TASK-AR-608 closed the mobile overflow refinement, but its independent verification recorded a next-cycle watch: Taskset Board currently contains 49 tasksets, so target discovery and whole-board focus traversal are long. The next UI/UX loop should select a stronger information architecture and visual direction before mutating UI source.

## Inputs

- reviews/W4B-2026-06-19-TASK-AR-608.md
- reviews/BETA-TEST-2026-06-19-oag-mobile-responsive-refinement.md
- reviews/UX-EVAL-2026-06-19-oag-mobile-responsive-refinement.md
- reviews/RFC-2026-06-19-ui-ux-design-direction.md
- docs/design/agent-runtime/DESIGN.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- scripts/ui_ux_cycle.py

## Target Files

- reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md
- reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
- reviews/INDEX.md

## Scope

Write the seminar decision artifact and refresh the evidence index only. Do not patch docs/design or UI source files in this unit.

## Steps

1. Read the OAG mobile beta, UX, and W4B evidence that routed the Taskset Board IA watch.
2. Record positions from lead-designer, design-system-steward, interface-designer, and ux-evaluator.
3. Compare at least three directions: progressive drill-down, command-palette/taskset switcher, and attention-lane workspace.
4. Choose one RFC candidate and explicitly reject the weaker alternatives.
5. Classify expected reusable surfaces as design_token, ui_component, pattern_component, or one_off_for_now.
6. Define beta-tester evidence paths and gate commands for the RFC and next implementation taskset.
7. Refresh evidence index and run the recorded verification commands.

## Acceptance Criteria

- The seminar is specific enough for a planner to write the RFC task without chat context.
- Every UI quality dimension has concrete evidence expectations and an assetization class.
- The chosen direction has explicit implementation boundaries, schema expectations, and a beta-tester follow-up path.
- No source UI files are changed by this unit.

## Verification

- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Report the selected Taskset Board IA direction, rejected alternatives, assetization implications, RFC target files, and next beta/UX evidence path.

## Stop Boundary

Stop after seminar evidence is complete and ready for independent verification or RFC claim.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T16:00:00+09:00`
- Resolution: `done`
- Actual hours: `0.8`
- Actual tokens: `6000`
- Closed by: `codex-lead-designer-task-ar-609`
- Evidence:
  - `reviews/VERIFY-2026-06-19-unit-task-ar-609-001-20260619155830.json`
<!-- work-close:end -->
