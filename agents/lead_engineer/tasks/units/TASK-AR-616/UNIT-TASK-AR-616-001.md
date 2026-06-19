---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-616-001
work_uid: b05a4606-c19c-4c5c-8957-eb156dfd364e
kind: unit
parent_id: TASK-AR-616
unit_id: UNIT-TASK-AR-616-001
task_id: TASK-AR-616
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-designer
created_at: 2026-06-19T23:39:00+09:00
updated_at: 2026-06-19T23:39:00+09:00
origin_type: beta_followup
origin_ref: reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md
created_by: codex-ux-evaluator-ar-615
summary: Run evidence overload and performance IA lead-designer seminar
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-615 closed BTC-TSAW-CLAIM-001 and BTC-TSAW-EMPTY-001, but its beta/UX evidence recommended a broader lead-designer cycle for evidence-gap overload, state-build latency, and performance-aware Taskset Board IA.
inputs:
  - reviews/BETA-TEST-2026-06-19-tsaw-claim-empty-refinement.md
  - reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md
  - reviews/W4B-2026-06-19-TASK-AR-615.md
  - reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
  - docs/design/agent-runtime/DESIGN.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - scripts/ui_ux_cycle.py
target_files:
  - reviews/SEMINAR-2026-06-19-taskset-board-evidence-performance-ia.md
  - reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
  - reviews/INDEX.md
scope: Write the seminar decision artifact and refresh the evidence index only. Do not patch design docs or UI source files in this unit.
acceptance:
  - The seminar is specific enough for a planner to write the RFC task without chat context.
  - Every UI quality dimension has concrete evidence expectations and an assetization class.
  - The chosen direction has explicit implementation boundaries, schema expectations, latency expectations, and a beta-tester follow-up path.
  - No UI source files are changed by this unit.
verification:
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
handoff: Report the selected Taskset Board evidence/performance IA direction, rejected alternatives, assetization implications, RFC target files, and next beta/UX evidence path.
stop_condition: Stop after seminar evidence is complete and ready for independent verification or RFC claim.
---

# UNIT-TASK-AR-616-001 - Run evidence overload and performance IA lead-designer seminar

## Context

TASK-AR-615 closed BTC-TSAW-CLAIM-001 and BTC-TSAW-EMPTY-001, but its beta/UX evidence recommended a broader lead-designer cycle for evidence-gap overload, state-build latency, and performance-aware Taskset Board IA.

## Inputs

- reviews/BETA-TEST-2026-06-19-tsaw-claim-empty-refinement.md
- reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md
- reviews/W4B-2026-06-19-TASK-AR-615.md
- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
- docs/design/agent-runtime/DESIGN.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- scripts/ui_ux_cycle.py

## Target Files

- reviews/SEMINAR-2026-06-19-taskset-board-evidence-performance-ia.md
- reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
- reviews/INDEX.md

## Scope

Write the seminar decision artifact and refresh the evidence index only. Do not patch design docs or UI source files in this unit.

## Steps

1. Read the TASK-AR-615 beta, UX, and W4B evidence.
2. Record positions from lead-designer, design-system-steward, interface-designer, ux-evaluator, and beta-tester.
3. Compare stale-evidence grouping, lane cap disclosure/progressive drill-in, and performance-split board loading.
4. Choose one RFC candidate and explicitly reject weaker alternatives.
5. Classify expected reusable surfaces as design_token, ui_component, pattern_component, or one_off_for_now.
6. Define beta-tester evidence paths and gate commands for the RFC and next implementation taskset.
7. Refresh evidence index and run the recorded verification commands.

## Acceptance Criteria

- The seminar is specific enough for a planner to write the RFC task without chat context.
- Every UI quality dimension has concrete evidence expectations and an assetization class.
- The chosen direction has explicit implementation boundaries, schema expectations, latency expectations, and a beta-tester follow-up path.
- No UI source files are changed by this unit.

## Verification

- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Report the selected Taskset Board evidence/performance IA direction, rejected alternatives, assetization implications, RFC target files, and next beta/UX evidence path.

## Stop Boundary

Stop after seminar evidence is complete and ready for independent verification or RFC claim.
