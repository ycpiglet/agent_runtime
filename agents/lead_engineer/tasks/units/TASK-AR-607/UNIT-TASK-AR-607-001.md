---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-607-001
work_uid: 820b626a-7679-4e6f-838e-db4df48a77e3
kind: unit
parent_id: TASK-AR-607
unit_id: UNIT-TASK-AR-607-001
task_id: TASK-AR-607
task_set_id: TASKSET-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT
initiative_id: INIT-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: interface-designer
created_at: 2026-06-19T14:04:00+09:00
updated_at: 2026-06-19T14:43:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Constrain Taskset Board mobile layout
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-606 accepted the claim-aware relation adapter but routed BTC-OAG-CLAIM-MOBILE-001: at a 390x844 viewport, Taskset Board document width was 641px. The likely source is fixed min-width/grid behavior in the Taskset Board toolbar, cards, relation body, child rows, or swimlane columns.
inputs:
  - reviews/BETA-TEST-2026-06-19-oag-claim-aware-relation-adapter.md
  - reviews/UX-EVAL-2026-06-19-oag-claim-aware-relation-adapter.md
  - reviews/W4B-2026-06-19-TASK-AR-606.md
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_console.py
  - tests/test_ui_console_e2e.py
  - tests/test_ui_design_assets.py
target_files:
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_console.py
  - tests/test_ui_console_e2e.py
  - tests/test_ui_design_assets.py
  - reviews/VERIFY-2026-06-19-oag-mobile-responsive-refinement.json
  - reviews/INDEX.md
scope: Implement only responsive layout constraints for Taskset Board and relation-panel surfaces. Do not alter taskset data schema, claim adapter state mapping, or broad console theming.
acceptance:
  - A browser-level test proves `documentElement.scrollWidth <= window.innerWidth` for Taskset Board at `390x844`.
  - Tests still prove claim-aware relation chips and command readiness labels exist.
  - No raw color, spacing, radius, shadow, or type literal is introduced outside token definitions.
  - The fix is classified as pattern_component responsive refinement with no new design direction.
  - The desktop Taskset Board layout remains usable and relation panel content remains visible.
verification:
  - python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_design_assets.py -q
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/evidence_index_generator.py --check
handoff: Report selectors changed, responsive constraints added, assetization classification, desktop/mobile test results, and any remaining UX risks.
stop_condition: Stop after the mobile overflow fix passes focused tests and W4a evidence is ready for independent verification.
verified_at: 2026-06-19T14:31:21+09:00
verified_by: codex-interface-designer-ar-607
evidence_refs:
  - reviews/VERIFY-2026-06-19-unit-task-ar-607-001-20260619143121.json
resolution: done
completed_at: 2026-06-19T14:43:00+09:00
closed_by: codex-interface-designer-ar-607
actual_hours: 0.9
actual_tokens: 12000
---

# UNIT-TASK-AR-607-001 - Constrain Taskset Board mobile layout

## Context

TASK-AR-606 accepted the claim-aware relation adapter but routed BTC-OAG-CLAIM-MOBILE-001: at a 390x844 viewport, Taskset Board document width was 641px. The likely source is fixed min-width/grid behavior in the Taskset Board toolbar, cards, relation body, child rows, or swimlane columns.

## Inputs

- reviews/BETA-TEST-2026-06-19-oag-claim-aware-relation-adapter.md
- reviews/UX-EVAL-2026-06-19-oag-claim-aware-relation-adapter.md
- reviews/W4B-2026-06-19-TASK-AR-606.md
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_console.py
- tests/test_ui_console_e2e.py
- tests/test_ui_design_assets.py

## Target Files

- src/agent_runtime/ui_console_assets.py
- tests/test_ui_console.py
- tests/test_ui_console_e2e.py
- tests/test_ui_design_assets.py
- reviews/VERIFY-2026-06-19-oag-mobile-responsive-refinement.json
- reviews/INDEX.md

## Scope

Implement only responsive layout constraints for Taskset Board and relation-panel surfaces. Do not alter taskset data schema, claim adapter state mapping, or broad console theming.

## Steps

1. Read TASK-AR-606 beta, UX, and W4b findings.
2. Trace CSS selectors that can widen Taskset Board at 390px: toolbar, card grid minmax, relation body, child rows, add-task row, chips, and swimlanes.
3. Add mobile constraints under the existing responsive breakpoint using design tokens and stable pattern selectors.
4. Keep text visible through wrapping or stacking rather than clipping important state labels.
5. Add focused CSS contract tests and update any existing mobile E2E overflow assertion for Taskset Board.
6. Run W4a verification commands and record evidence.

## Acceptance Criteria

- A browser-level test proves `documentElement.scrollWidth <= window.innerWidth` for Taskset Board at `390x844`.
- Tests still prove claim-aware relation chips and command readiness labels exist.
- No raw color, spacing, radius, shadow, or type literal is introduced outside token definitions.
- The fix is classified as pattern_component responsive refinement with no new design direction.
- The desktop Taskset Board layout remains usable and relation panel content remains visible.

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_design_assets.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Report selectors changed, responsive constraints added, assetization classification, desktop/mobile test results, and any remaining UX risks.

## Stop Boundary

Stop after the mobile overflow fix passes focused tests and W4a evidence is ready for independent verification.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T14:43:00+09:00`
- Resolution: `done`
- Actual hours: `0.9`
- Actual tokens: `12000`
- Closed by: `codex-interface-designer-ar-607`
- Evidence:
  - `reviews/VERIFY-2026-06-19-unit-task-ar-607-001-20260619143121.json`
<!-- work-close:end -->
