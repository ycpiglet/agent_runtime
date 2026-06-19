---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-604-001
work_uid: ffb40f96-7fd2-4cea-8423-a3873ba599ba
kind: unit
parent_id: TASK-AR-604
unit_id: UNIT-TASK-AR-604-001
task_id: TASK-AR-604
task_set_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
initiative_id: INIT-AR-OPERATOR-ATTENTION-GRAPH
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: ux-evaluator
created_at: 2026-06-19T09:08:00+09:00
updated_at: 2026-06-19T12:22:48+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Record beta-tester and UX-evaluator evidence
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Owner asked for UI/UX cycles that use beta-tester and evaluator evidence rather than screenshot-only claims. This unit verifies the first operator_attention_graph implementation after it lands.
inputs:
  - reviews/RFC-2026-06-19-ui-ux-design-direction.md
  - reviews/BETA-PLAN-2026-06-19-operator-attention-graph.md
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
target_files:
  - reviews/BETA-TEST-2026-06-19-operator-attention-graph.md
  - reviews/UX-EVAL-2026-06-19-operator-attention-graph.md
  - reviews/INDEX.md
scope: Record exploratory evidence only. Do not patch UI source files in this unit.
acceptance:
  - Evidence lists exact actions, viewport, environment, expected result, observed result, and pass/fail status.
  - Recovery and edge states are attempted, not merely listed.
  - No UI source files are changed by the evaluation unit.
  - Any defect becomes a BTC-style follow-up candidate rather than an untracked note.
verification:
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
  - python scripts/ui_ux_cycle.py --root . assess --json
handoff: Report beta paths, defects, accessibility/responsive findings, and whether another UI/UX cycle should propose a new design direction or implementation refinement.
stop_condition: Stop after beta and UX evidence are complete and ready for independent verification.
verified_at: 2026-06-19T12:12:40+09:00
verified_by: codex-ux-evaluator-oag-604-resume
evidence_refs:
  - reviews/VERIFY-2026-06-19-unit-task-ar-604-001-20260619100700.json
  - reviews/VERIFY-2026-06-19-unit-task-ar-604-001-20260619121240.json
resolution: done
completed_at: 2026-06-19T12:22:48+09:00
closed_by: codex-ux-evaluator-oag-604-resume
actual_hours: 1.8
actual_tokens: 12000
---

# UNIT-TASK-AR-604-001 - Record beta-tester and UX-evaluator evidence

## Context

The Owner asked for UI/UX cycles that use beta-tester and evaluator evidence rather than screenshot-only claims. This unit verifies the first operator_attention_graph implementation after it lands.

## Inputs

- reviews/RFC-2026-06-19-ui-ux-design-direction.md
- reviews/BETA-PLAN-2026-06-19-operator-attention-graph.md
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py

## Target Files

- reviews/BETA-TEST-2026-06-19-operator-attention-graph.md
- reviews/UX-EVAL-2026-06-19-operator-attention-graph.md
- reviews/INDEX.md

## Scope

Record exploratory evidence only. Do not patch UI source files in this unit.

## Steps

1. Launch or inspect the local UI surface required by the implementation task.
2. Execute desktop and mobile user-like paths using click or keyboard actions.
3. Exercise empty graph, stale evidence, blocked command, and interrupted claim recovery states.
4. Record accessibility observations for labels, focus order, reduced motion, and non-color-only state.
5. Assign BTC-style IDs to every visible defect and link reproduction paths.
6. Refresh evidence index and run recorded verification commands.

## Acceptance Criteria

- Evidence lists exact actions, viewport, environment, expected result, observed result, and pass/fail status.
- Recovery and edge states are attempted, not merely listed.
- No UI source files are changed by the evaluation unit.
- Any defect becomes a BTC-style follow-up candidate rather than an untracked note.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`

## Handoff

Report beta paths, defects, accessibility/responsive findings, and whether another UI/UX cycle should propose a new design direction or implementation refinement.

## Stop Boundary

Stop after beta and UX evidence are complete and ready for independent verification.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T12:22:48+09:00`
- Resolution: `done`
- Actual hours: `1.8`
- Actual tokens: `12000`
- Closed by: `codex-ux-evaluator-oag-604-resume`
- Evidence:
  - `reviews/VERIFY-2026-06-19-unit-task-ar-604-001-20260619100700.json`
  - `reviews/VERIFY-2026-06-19-unit-task-ar-604-001-20260619121240.json`
<!-- work-close:end -->
