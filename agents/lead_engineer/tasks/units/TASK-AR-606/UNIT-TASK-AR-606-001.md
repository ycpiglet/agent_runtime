---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-606-001
work_uid: 9527db89-80a6-40d5-9529-d131c454384f
kind: unit
parent_id: TASK-AR-606
unit_id: UNIT-TASK-AR-606-001
task_id: TASK-AR-606
task_set_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
initiative_id: INIT-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: ux-evaluator
created_at: 2026-06-19T12:26:00+09:00
updated_at: 2026-06-19T12:26:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Record claim-aware adapter beta and UX evidence
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: This unit validates that the adapter fix resolved TASK-AR-604's routed findings and that relation state remains usable across desktop/mobile and recovery states.
inputs:
  - reviews/BETA-TEST-2026-06-19-operator-attention-graph.md
  - reviews/UX-EVAL-2026-06-19-operator-attention-graph.md
  - reviews/W4B-2026-06-19-TASK-AR-604.md
  - src/agent_runtime/ui_console_assets.py
target_files:
  - reviews/BETA-TEST-2026-06-19-oag-claim-aware-relation-adapter.md
  - reviews/UX-EVAL-2026-06-19-oag-claim-aware-relation-adapter.md
  - reviews/INDEX.md
scope: Record exploratory evidence only. Do not patch UI source files in this unit.
acceptance:
  - Evidence lists exact actions, viewport, data state, expected result, observed result, and pass/fail status.
  - Recovery and edge states are attempted rather than only described.
  - No UI source files are changed by the evaluation unit.
  - The handoff recommends either another implementation refinement or a new design-direction cycle.
verification:
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
  - python scripts/ui_ux_cycle.py --root . assess --json
handoff: Report beta paths, defects, accessibility/responsive findings, and the next UI/UX cycle decision.
stop_condition: Stop after beta/UX evidence is complete and ready for independent verification.
---

# UNIT-TASK-AR-606-001 - Record claim-aware adapter beta and UX evidence

## Context

This unit validates that the adapter fix resolved TASK-AR-604's routed findings and that relation state remains usable across desktop/mobile and recovery states.

## Inputs

- reviews/BETA-TEST-2026-06-19-operator-attention-graph.md
- reviews/UX-EVAL-2026-06-19-operator-attention-graph.md
- reviews/W4B-2026-06-19-TASK-AR-604.md
- src/agent_runtime/ui_console_assets.py

## Target Files

- reviews/BETA-TEST-2026-06-19-oag-claim-aware-relation-adapter.md
- reviews/UX-EVAL-2026-06-19-oag-claim-aware-relation-adapter.md
- reviews/INDEX.md

## Scope

Record exploratory evidence only. Do not patch UI source files in this unit.

## Steps

1. Launch the local UI surface from the implementation worktree.
2. Execute active claim, no-claim, expired claim, interrupted claim, and guarded command paths.
3. Check desktop and mobile layout, focus order, non-color-only labels, and reduced-motion behavior.
4. Assign BTC-style IDs to remaining user-visible defects.
5. Refresh evidence index and run recorded verification commands.

## Acceptance Criteria

- Evidence lists exact actions, viewport, data state, expected result, observed result, and pass/fail status.
- Recovery and edge states are attempted rather than only described.
- No UI source files are changed by the evaluation unit.
- The handoff recommends either another implementation refinement or a new design-direction cycle.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`

## Handoff

Report beta paths, defects, accessibility/responsive findings, and the next UI/UX cycle decision.

## Stop Boundary

Stop after beta/UX evidence is complete and ready for independent verification.
