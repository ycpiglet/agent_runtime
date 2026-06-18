---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-580-001
work_uid: c649a1b1-b4f6-44db-94cf-ccaa86f8bdeb
kind: unit
parent_id: TASK-AR-580
unit_id: UNIT-TASK-AR-580-001
task_id: TASK-AR-580
task_set_id: TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
initiative_id: INIT-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: design-system-steward
created_at: 2026-06-18T14:50:00+09:00
updated_at: 2026-06-18T15:00:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-component-patterns
created_by: codex-planner
summary: Promote component and domain pattern helpers
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: AR-579 created the first asset layer. This unit promotes the named component/pattern APIs that the diagnostic report called out as still missing: Button/Card/Modal/Table and TaskLane/ClaimCard/EvidencePanel/CommandBar/StateMachinePanel.
inputs:
  - reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console.py
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console.py
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
  - agents/lead_engineer/tasks/TASK-AR-580.md
  - agents/lead_engineer/tasks/units/TASK-AR-580/UNIT-TASK-AR-580-001.md
scope: Promote named helpers and wire representative existing renderers. Do not migrate to React, do not redesign the visual language, and do not attempt a full ui_console.py decomposition in one unit.
acceptance:
  - The new helpers are classified as ui_component or pattern_component in ASSETIZATION_CLASSES.
  - Task lane/task card, command, evidence, and state-machine renderers use promoted helpers.
  - Existing UI tests remain green and design-system gate passes.
  - Remaining one-off renderers are explicitly documented as residual debt.
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q
  - python scripts/design_system_gate.py --check
  - python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check
  - python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS --check
  - python scripts/work_item_classifier.py --check
handoff: Report promoted helpers, representative usages, tests, and residual one-off boundaries.
stop_condition: Stop after named component/pattern helpers are wired, tested, documented, and W4 evidence is recorded.
verified_at: 2026-06-18T15:00:00+09:00
verified_by: codex-design-system-component-patterns-580
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000.json
  - reviews/VERIFY-2026-06-18-task-ar-580-20260618150500.json
  - reviews/W4B-2026-06-18-TASK-AR-580.md
resolution: done
completed_at: 2026-06-18T15:00:00+09:00
---

# UNIT-TASK-AR-580-001 - Promote component and domain pattern helpers

## Context

AR-579 created the first asset layer. This unit promotes the named component/pattern APIs that the diagnostic report called out as still missing: Button/Card/Modal/Table and TaskLane/ClaimCard/EvidencePanel/CommandBar/StateMachinePanel.

## Inputs

- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console.py
- tests/test_ui_design_assets.py
- tests/test_ui_console.py

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console.py
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- tests/test_ui_design_assets.py
- tests/test_ui_console.py
- agents/lead_engineer/tasks/TASK-AR-580.md
- agents/lead_engineer/tasks/units/TASK-AR-580/UNIT-TASK-AR-580-001.md

## Scope

Promote named helpers and wire representative existing renderers. Do not migrate to React, do not redesign the visual language, and do not attempt a full ui_console.py decomposition in one unit.

## Steps

1. Add named UI component helpers for button, card, modal shell, table, and metadata surfaces.
2. Add named pattern helpers for TaskLane, ClaimCard, EvidencePanel, CommandBar, and StateMachinePanel that preserve existing CSS selectors.
3. Replace representative inline markup in ui_console.py with helper calls.
4. Extend tests to prove the helpers are served and used.
5. Update DESIGN-SYSTEM.md with promoted API boundaries.
6. Run verification and record W4 evidence.

## Acceptance Criteria

- The new helpers are classified as ui_component or pattern_component in ASSETIZATION_CLASSES.
- Task lane/task card, command, evidence, and state-machine renderers use promoted helpers.
- Existing UI tests remain green and design-system gate passes.
- Remaining one-off renderers are explicitly documented as residual debt.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS --check`
- `python scripts/work_item_classifier.py --check`

## Handoff

Report promoted helpers, representative usages, tests, and residual one-off boundaries.

## Stop Boundary

Stop after named component/pattern helpers are wired, tested, documented, and W4 evidence is recorded.

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Button, Card, Table, Modal shell primitives | `ui_component` | `src/agent_runtime/ui_design_assets.py::componentButton/componentCard/componentTable/componentModalShell` |
| Task lane and claim card | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternTaskLane/patternClaimCard` |
| Evidence and audit panels | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternEvidencePanel/patternAuditCard` |
| Command bar and state-machine legend | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternCommandBar/patternStateMachinePanelLegend` |
| Remaining SVG/layout-heavy renderers | `one_off_for_now` | `src/agent_runtime/ui_console.py` |

## Verification Result

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q` -> `167 passed`
- `python scripts/design_system_gate.py --check` -> pass
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check` -> pass
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py` -> pass
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS --check` -> pass
- `python scripts/work_item_classifier.py --check` -> pass
