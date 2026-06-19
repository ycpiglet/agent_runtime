---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-613-001
work_uid: 5a42d774-01c5-4d0f-91d5-bb18a8e6b799
kind: unit
parent_id: TASK-AR-613
unit_id: UNIT-TASK-AR-613-001
task_id: TASK-AR-613
task_set_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
initiative_id: INIT-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: ux-evaluator
created_at: 2026-06-19T18:35:00+09:00
updated_at: 2026-06-19T21:53:53+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-interface-designer-task-ar-611
summary: Record Taskset Board attention workspace beta and UX evidence
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Owner asked for UI/UX improvement loops that include beta-tester and evaluator evidence rather than screenshot-only completion claims.
inputs:
  - reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md
  - reviews/BETA-PLAN-2026-06-19-taskset-board-attention-workspace.md
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_state.py
target_files:
  - reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md
  - reviews/UX-EVAL-2026-06-19-taskset-board-attention-workspace.md
  - reviews/INDEX.md
scope: Record exploratory evidence only. Do not patch UI source files in this unit.
acceptance:
  - Evidence lists exact action path, viewport, data state, expected result, observed result, pass/fail status, and screenshot or trace reference when available.
  - Recovery and edge states are attempted, not merely listed.
  - No UI source files are changed by the evaluation unit.
  - Every actionable defect has an owner and assetization class.
verification:
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
  - python scripts/ui_ux_cycle.py --root . assess --json
handoff: Report beta paths, defects, accessibility and responsive findings, BTC-TSAW ids, and whether the next UI/UX cycle needs design exploration or implementation refinement.
stop_condition: Stop after beta and UX evidence are complete and ready for independent W4b verification.
verified_at: 2026-06-19T21:45:07+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-06-19-unit-task-ar-613-001-20260619214507.json
resolution: done
completed_at: 2026-06-19T21:53:53+09:00
closed_by: codex-ux-evaluator-ar-613
actual_hours: 1.5
actual_tokens: 12000
---

# UNIT-TASK-AR-613-001 - Record Taskset Board attention workspace beta and UX evidence

## Context

The Owner asked for UI/UX improvement loops that include beta-tester and evaluator evidence rather than screenshot-only completion claims.

## Inputs

- reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md
- reviews/BETA-PLAN-2026-06-19-taskset-board-attention-workspace.md
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_state.py

## Target Files

- reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md
- reviews/UX-EVAL-2026-06-19-taskset-board-attention-workspace.md
- reviews/INDEX.md

## Scope

Record exploratory evidence only. Do not patch UI source files in this unit.

## Steps

1. Launch or inspect the local UI surface for the implemented Taskset Board route.
2. Execute unknown-target discovery from the first viewport and record the selected lane reason.
3. Type a known taskset id or title fragment into the switcher and jump to the matching detail.
4. Traverse by keyboard through lane controls, switcher, selected card, relation detail, and all-tasksets fallback.
5. Repeat the main path at desktop and 390x844 mobile viewport.
6. Exercise empty lane, stale evidence, blocked command, interrupted claim, expired claim, and no active claim recovery states.
7. Review reduced-motion and non-color-only state cues.
8. Assign BTC-TSAW ids to every visible defect and refresh evidence index.

## Acceptance Criteria

- Evidence lists exact action path, viewport, data state, expected result, observed result, pass/fail status, and screenshot or trace reference when available.
- Recovery and edge states are attempted, not merely listed.
- No UI source files are changed by the evaluation unit.
- Every actionable defect has an owner and assetization class.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`

## Handoff

Report beta paths, defects, accessibility and responsive findings, BTC-TSAW ids, and whether the next UI/UX cycle needs design exploration or implementation refinement.

## Stop Boundary

Stop after beta and UX evidence are complete and ready for independent W4b verification.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T21:53:53+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `12000`
- Closed by: `codex-ux-evaluator-ar-613`
- Evidence:
  - `reviews/VERIFY-2026-06-19-unit-task-ar-613-001-20260619214507.json`
<!-- work-close:end -->
