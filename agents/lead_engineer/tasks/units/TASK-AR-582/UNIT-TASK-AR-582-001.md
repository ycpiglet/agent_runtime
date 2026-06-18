---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-582-001
work_uid: a0565c50-281d-41f6-a4b9-8b146fb81294
kind: unit
parent_id: TASK-AR-582
unit_id: UNIT-TASK-AR-582-001
task_id: TASK-AR-582
task_set_id: TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
initiative_id: INIT-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: design-system-steward
created_at: 2026-06-18T15:55:00+09:00
updated_at: 2026-06-18T16:15:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-served-asset-split
created_by: codex-planner
summary: Move served HTML CSS JS assets out of ui_console
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: AR-581 closed CSS raw-literal token debt. The diagnostic still identifies ui_console.py as a single module that owns the HTML, CSS, and JS strings. This unit creates a physical served-asset boundary without changing frontend behavior.
inputs:
  - reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - src/agent_runtime/ui_console.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
target_files:
  - src/agent_runtime/ui_console.py
  - src/agent_runtime/ui_console_assets.py
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
  - agents/lead_engineer/tasks/TASK-AR-582.md
  - agents/lead_engineer/tasks/units/TASK-AR-582/UNIT-TASK-AR-582-001.md
scope: Move served asset strings only. Do not rewrite JS renderers, redesign visuals, or change API/data behavior.
acceptance:
  - ui_console.py line count drops materially because served asset strings moved out.
  - ui_console_assets.py contains the served asset strings and design asset composition.
  - UI console regression tests and design-system gates pass.
  - Residual one-off renderer debt remains explicitly documented separately from served asset ownership.
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q
  - python scripts/design_system_gate.py --all-ui --check
  - python scripts/design_system_gate.py --check
  - python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_console_assets.py --path src/agent_runtime/ui_design_assets.py --check
  - python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_console_assets.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT --check
  - python scripts/work_item_classifier.py --check
handoff: Report new asset module boundary, line-count reduction, tests, and remaining renderer pattern debt.
stop_condition: Stop after served asset strings are moved, behavior is verified, evidence is recorded, and the claim is released.
verified_at: 2026-06-18T16:10:00+09:00
verified_by: codex-design-system-served-asset-split-582
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000.json
  - reviews/VERIFY-2026-06-18-task-ar-582-20260618161500.json
  - reviews/W4B-2026-06-18-TASK-AR-582.md
resolution: done
completed_at: 2026-06-18T16:15:00+09:00
---

# UNIT-TASK-AR-582-001 - Move served HTML CSS JS assets out of ui_console

## Context

AR-581 closed CSS raw-literal token debt. The diagnostic still identifies ui_console.py as a single module that owns the HTML, CSS, and JS strings. This unit creates a physical served-asset boundary without changing frontend behavior.

## Inputs

- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- src/agent_runtime/ui_console.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_design_assets.py
- tests/test_ui_console.py

## Target Files

- src/agent_runtime/ui_console.py
- src/agent_runtime/ui_console_assets.py
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- tests/test_ui_design_assets.py
- tests/test_ui_console.py
- agents/lead_engineer/tasks/TASK-AR-582.md
- agents/lead_engineer/tasks/units/TASK-AR-582/UNIT-TASK-AR-582-001.md

## Scope

Move served asset strings only. Do not rewrite JS renderers, redesign visuals, or change API/data behavior.

## Steps

1. Create ui_console_assets.py containing the HTML, CSS, and JS strings.
2. Keep CSS and JS composition with ui_design_assets in the new asset module.
3. Update ui_console.py to import ui_console_assets and serve its HTML/CSS/JS constants.
4. Update tests to verify the new module boundary and served asset behavior.
5. Update DESIGN-SYSTEM.md with the new served asset layer.
6. Run verification and record W4 evidence.

## Acceptance Criteria

- ui_console.py line count drops materially because served asset strings moved out.
- ui_console_assets.py contains the served asset strings and design asset composition.
- UI console regression tests and design-system gates pass.
- Residual one-off renderer debt remains explicitly documented separately from served asset ownership.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --all-ui --check`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_console_assets.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_console_assets.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT --check`
- `python scripts/work_item_classifier.py --check`

## Handoff

Report new asset module boundary, line-count reduction, tests, and remaining renderer pattern debt.

## Stop Boundary

Stop after served asset strings are moved, behavior is verified, evidence is recorded, and the claim is released.

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Served HTML/CSS/JS asset strings | `pattern_component` | `src/agent_runtime/ui_console_assets.py` |
| HTTP routing and API response orchestration | `page assembly` | `src/agent_runtime/ui_console.py` |
| Remaining JS view renderers | `one_off_for_now` | `src/agent_runtime/ui_console_assets.py` residual renderer extraction debt |

## Verification Result

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q` -> `169 passed`
- `python scripts/design_system_gate.py --all-ui --check` -> pass, `findings=0`
- `python scripts/design_system_gate.py --check` -> pass
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_console_assets.py --path src/agent_runtime/ui_design_assets.py --check` -> pass
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_console_assets.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py` -> pass
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT --check` -> pass
- `python scripts/work_item_classifier.py --check` -> pass
