---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-614-001
work_uid: aadafb7b-9fbe-4a4f-be3b-70118186454e
kind: unit
parent_id: TASK-AR-614
unit_id: UNIT-TASK-AR-614-001
task_id: TASK-AR-614
task_set_id: TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT
initiative_id: INIT-AR-TSAW-CLAIM-EMPTY-REFINEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: interface-designer
created_at: 2026-06-19T21:56:00+09:00
updated_at: 2026-06-19T22:24:18+09:00
origin_type: beta_finding
origin_ref: reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md
created_by: codex-ux-evaluator-ar-613
summary: Patch attention workspace claim and empty recovery states
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-613 beta evidence routed BTC-TSAW-CLAIM-001 because live `work.py status` showed an active TASK-AR-613 claim while root `/api/tasksets_board` returned `active_claims=0`. It also routed BTC-TSAW-EMPTY-001 because zero-count lane empty cards reused non-empty reason copy.
inputs:
  - reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md
  - reviews/UX-EVAL-2026-06-19-taskset-board-attention-workspace.md
  - reviews/W4B-2026-06-19-TASK-AR-613.md
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - tests/test_ui_design_assets.py
target_files:
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - tests/test_ui_design_assets.py
  - reviews/VERIFY-2026-06-19-tsaw-claim-empty-refinement.json
  - reviews/INDEX.md
scope: Implement only active-claim lane freshness and empty-lane copy refinement. Do not introduce a new visual direction or change claim lifecycle semantics.
acceptance:
  - A focused test proves a claimed taskset appears in `active_claims` with a visible reason.
  - A focused UI/component test proves zero-count lane copy is not contradictory.
  - The change uses existing design tokens and component/pattern helpers.
  - No task or claim files are written by the UI state/API path.
  - The all-tasksets fallback and task.create proposal-only path remain unchanged.
verification:
  - python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_design_assets.py -q
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/evidence_index_generator.py --check
  - git diff --check
handoff: Report data derivation fields changed, empty-state pattern copy, tests, verification evidence, and any remaining UX risks.
stop_condition: Stop after implementation is source-mutated, tested, self-verified, and ready for independent W4b verification.
verified_at: 2026-06-19T22:24:18+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-06-19-unit-task-ar-614-001-20260619222418.json
---

# UNIT-TASK-AR-614-001 - Patch attention workspace claim and empty recovery states

## Context

TASK-AR-613 beta evidence routed BTC-TSAW-CLAIM-001 because live `work.py status` showed an active TASK-AR-613 claim while root `/api/tasksets_board` returned `active_claims=0`. It also routed BTC-TSAW-EMPTY-001 because zero-count lane empty cards reused non-empty reason copy.

## Inputs

- reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md
- reviews/UX-EVAL-2026-06-19-taskset-board-attention-workspace.md
- reviews/W4B-2026-06-19-TASK-AR-613.md
- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_state.py
- tests/test_ui_console.py
- tests/test_ui_design_assets.py

## Target Files

- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_state.py
- tests/test_ui_console.py
- tests/test_ui_design_assets.py
- reviews/VERIFY-2026-06-19-tsaw-claim-empty-refinement.json
- reviews/INDEX.md

## Scope

Implement only active-claim lane freshness and empty-lane copy refinement. Do not introduce a new visual direction or change claim lifecycle semantics.

## Steps

1. Read TASK-AR-613 beta/UX findings and current Taskset Board attention workspace derivation.
2. Trace how task claims are passed into `build_tasksets_board` and why active claims do not affect lane membership.
3. Adjust state derivation so active claim membership is derived from current claim data rather than stale classification alone.
4. Update the lane pattern/component empty state so zero-count lanes distinguish purpose from current absence.
5. Add focused unit/UI asset tests for active claim lane membership and empty copy.
6. Run W4a verification commands and record evidence.

## Acceptance Criteria

- A focused test proves a claimed taskset appears in `active_claims` with a visible reason.
- A focused UI/component test proves zero-count lane copy is not contradictory.
- The change uses existing design tokens and component/pattern helpers.
- No task or claim files are written by the UI state/API path.
- The all-tasksets fallback and task.create proposal-only path remain unchanged.

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_design_assets.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`
- `git diff --check`

## Handoff

Report data derivation fields changed, empty-state pattern copy, tests, verification evidence, and any remaining UX risks.

## Stop Boundary

Stop after implementation is source-mutated, tested, self-verified, and ready for independent W4b verification.