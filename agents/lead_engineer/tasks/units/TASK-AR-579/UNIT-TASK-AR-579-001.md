---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-579-001
work_uid: 35a9d00e-6d38-470a-ade3-8f799544f004
kind: unit
parent_id: TASK-AR-579
unit_id: UNIT-TASK-AR-579-001
task_id: TASK-AR-579
task_set_id: TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION
initiative_id: INIT-AR-DESIGN-SYSTEM-ASSETIZATION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: design-system-steward
created_at: 2026-06-18T13:20:00+09:00
updated_at: 2026-06-18T14:33:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-assetization
created_by: codex-planner
summary: Extract token, primitive, and pattern asset bundle
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The governance task closed the rules and gate, but the diagnostic still shows no durable UI asset layer and a large ui_console.py monolith. This unit starts the actual assetization without changing the console architecture.
inputs:
  - reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - src/agent_runtime/ui_console.py
  - scripts/design_system_gate.py
  - tests/test_ui_console.py
  - tests/test_design_system_gate.py
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console.py
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - scripts/design_system_gate.py
  - tests/test_ui_design_assets.py
  - tests/test_design_system_gate.py
  - tests/test_ui_console.py
scope: Create and wire the first asset bundle only. Preserve existing DOM/API selectors, app routes, and visual behavior. Do not introduce React/Vite/npm or broad CSS rewrites in this unit.
acceptance:
  - The console still serves /, /app.css, /app.js, and existing UI tests pass.
  - The selected primitive helpers are no longer authored only inside ui_console.py.
  - The new design-system gate fails on newly added raw UI literals but does not fail simply because an edited legacy UI file contains old baseline debt.
  - The design-system contract names the actual asset module and the next extraction boundary.
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q
  - python scripts/design_system_gate.py --check
  - python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check
  - python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION --check
handoff: Report extracted assets, gate behavior, residual UI-console debt, and verification results.
stop_condition: Stop after the first asset layer is wired, tested, documented, and taskset evidence is recorded.
verified_at: 2026-06-18T14:33:00+09:00
verified_by: codex-design-system-assetization-579
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300.json
resolution: done
completed_at: 2026-06-18T14:33:00+09:00
---

# UNIT-TASK-AR-579-001 - Extract token, primitive, and pattern asset bundle

## Context

The governance task closed the rules and gate, but the diagnostic still shows no durable UI asset layer and a large ui_console.py monolith. This unit starts the actual assetization without changing the console architecture.

## Inputs

- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- src/agent_runtime/ui_console.py
- scripts/design_system_gate.py
- tests/test_ui_console.py
- tests/test_design_system_gate.py

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console.py
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- scripts/design_system_gate.py
- tests/test_ui_design_assets.py
- tests/test_design_system_gate.py
- tests/test_ui_console.py

## Scope

Create and wire the first asset bundle only. Preserve existing DOM/API selectors, app routes, and visual behavior. Do not introduce React/Vite/npm or broad CSS rewrites in this unit.

## Steps

1. Add ui_design_assets.py with design token scale CSS, UI primitive JS helpers, and pattern helper aliases matching the current console architecture.
2. Import the asset bundle in ui_console.py and concatenate it into the served CSS/JS so existing renderer functions move out of the page-level monolith.
3. Replace selected inline helper definitions in ui_console.py with calls to the imported asset helpers while preserving public helper names used by existing JS.
4. Make design_system_gate.py diff-aware by default and keep explicit path/all-ui scans for full audits.
5. Add tests for the asset module, served bundle composition, and default gate behavior on added raw literals.
6. Update DESIGN-SYSTEM.md with the concrete module boundary and residual baseline rule.

## Acceptance Criteria

- The console still serves /, /app.css, /app.js, and existing UI tests pass.
- The selected primitive helpers are no longer authored only inside ui_console.py.
- The new design-system gate fails on newly added raw UI literals but does not fail simply because an edited legacy UI file contains old baseline debt.
- The design-system contract names the actual asset module and the next extraction boundary.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION --check`

## Handoff

Report extracted assets, gate behavior, residual UI-console debt, and verification results.

## Stop Boundary

Stop after the first asset layer is wired, tested, documented, and taskset evidence is recorded.

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Type, spacing, and radius scale | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` |
| Progress bar, empty state, state chip, card, and metadata grid helpers | `ui_component` | `src/agent_runtime/ui_design_assets.py::UI_COMPONENTS_JS` |
| Audit and surface metadata helpers | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternAuditMeta/patternSurfaceMeta` |
| Remaining view-specific renderers | `one_off_for_now` | `src/agent_runtime/ui_console.py` |

## Verification Result

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q` -> `163 passed`
- `python scripts/design_system_gate.py --check` -> pass
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check` -> pass
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py` -> pass
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION --check` -> pass
