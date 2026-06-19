---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-612-001
work_uid: 8744ac56-1bf7-4ba8-b72e-b1e86087fa81
kind: unit
parent_id: TASK-AR-612
unit_id: UNIT-TASK-AR-612-001
task_id: TASK-AR-612
task_set_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
initiative_id: INIT-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: interface-designer
created_at: 2026-06-19T18:35:00+09:00
updated_at: 2026-06-19T20:39:21+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-interface-designer-task-ar-611
summary: Add Taskset Board attention lane schema and workspace UI
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-610 accepted taskset_attention_workspace after OAG beta evidence showed 49 tasksets make whole-board scanning and focus traversal too long.
inputs:
  - reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md
  - reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md
  - docs/design/agent-runtime/DESIGN.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - tests/test_ui_design_assets.py
target_files:
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - tests/test_ui_design_assets.py
  - reviews/VERIFY-2026-06-19-taskset-board-attention-workspace-implementation.json
  - reviews/INDEX.md
scope: Source mutation is limited to declared UI state, UI asset, design asset, focused test, verification evidence, and review-index files. Do not change task/claim SSoT files, write APIs, dispatcher behavior, or unrelated console views.
acceptance:
  - Active, guarded, interrupted, stale or missing evidence, recently changed, ready next action, empty lane, and no active claim paths are visibly labelled.
  - Keyboard traversal reaches lane controls, switcher, active card, relation detail, and all-tasksets fallback without tabbing through every taskset first.
  - At 390x844, lanes, switcher, and detail stack without document-level horizontal overflow.
  - Reduced-motion mode removes movement-dependent meaning if transitions are introduced.
  - No raw color, spacing, radius, shadow, or type literals are introduced outside token definitions.
  - The implementation preserves existing /api/tasksets_board aliases and task.create proposal-only behavior.
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py tests/test_ui_state.py -q
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/evidence_index_generator.py --check
  - git diff --check
handoff: Report changed helpers, lane derivation fields, assetization classification, focused tests, beta evidence dependency, and any remaining one-off or schema gaps.
stop_condition: Stop after the attention workspace implementation is source-mutated, tested, self-verified, and ready for independent W4b verification.
verified_at: 2026-06-19T20:24:24+09:00
verified_by: codex-interface-designer-task-ar-612
evidence_refs:
  - reviews/VERIFY-2026-06-19-unit-task-ar-612-001-20260619202424.json
resolution: done
completed_at: 2026-06-19T20:39:21+09:00
closed_by: codex-interface-designer-task-ar-612
actual_hours: 2.4
actual_tokens: 52000
---

# UNIT-TASK-AR-612-001 - Add Taskset Board attention lane schema and workspace UI

## Context

TASK-AR-610 accepted taskset_attention_workspace after OAG beta evidence showed 49 tasksets make whole-board scanning and focus traversal too long.

## Inputs

- reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md
- reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md
- docs/design/agent-runtime/DESIGN.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_state.py
- tests/test_ui_console.py
- tests/test_ui_design_assets.py

## Target Files

- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_state.py
- tests/test_ui_console.py
- tests/test_ui_design_assets.py
- reviews/VERIFY-2026-06-19-taskset-board-attention-workspace-implementation.json
- reviews/INDEX.md

## Scope

Source mutation is limited to declared UI state, UI asset, design asset, focused test, verification evidence, and review-index files. Do not change task/claim SSoT files, write APIs, dispatcher behavior, or unrelated console views.

## Steps

1. Read the RFC assetization table and current tasksets_board API tests.
2. Derive attention lane data in ui_state.py from the named schema fields without writing task or claim records.
3. Add reusable ui_design_assets helpers for quick switcher, lane filter, attention lane, or relation detail only where current helpers cannot cover the surface.
4. Wire ui_console_assets.py so the first Taskset Board viewport renders attention lanes, switcher, and relation detail before the full all-tasksets fallback.
5. Preserve expanded/collapsed full board behavior and command proposal path for adding tasks.
6. Add focused state and UI tests for lane reasons, switcher empty and selected states, keyboard/focus anchors, mobile CSS anchors, and existing claim-summary behavior.
7. Run W4a verification commands and record evidence.

## Acceptance Criteria

- Active, guarded, interrupted, stale or missing evidence, recently changed, ready next action, empty lane, and no active claim paths are visibly labelled.
- Keyboard traversal reaches lane controls, switcher, active card, relation detail, and all-tasksets fallback without tabbing through every taskset first.
- At 390x844, lanes, switcher, and detail stack without document-level horizontal overflow.
- Reduced-motion mode removes movement-dependent meaning if transitions are introduced.
- No raw color, spacing, radius, shadow, or type literals are introduced outside token definitions.
- The implementation preserves existing /api/tasksets_board aliases and task.create proposal-only behavior.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py tests/test_ui_state.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`
- `git diff --check`

## Handoff

Report changed helpers, lane derivation fields, assetization classification, focused tests, beta evidence dependency, and any remaining one-off or schema gaps.

## Stop Boundary

Stop after the attention workspace implementation is source-mutated, tested, self-verified, and ready for independent W4b verification.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T20:39:21+09:00`
- Resolution: `done`
- Actual hours: `2.4`
- Actual tokens: `52000`
- Closed by: `codex-interface-designer-task-ar-612`
- Evidence:
  - `reviews/VERIFY-2026-06-19-unit-task-ar-612-001-20260619202424.json`
<!-- work-close:end -->
