---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-581-001
work_uid: c8a58acd-4d44-432a-9e4f-26836ad13899
kind: unit
parent_id: TASK-AR-581
unit_id: UNIT-TASK-AR-581-001
task_id: TASK-AR-581
task_set_id: TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT
initiative_id: INIT-AR-DESIGN-SYSTEM-TOKEN-DEBT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: design-system-steward
created_at: 2026-06-18T15:20:00+09:00
updated_at: 2026-06-18T15:40:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-token-debt
created_by: codex-planner
summary: Tokenize console CSS literal debt
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: AR-578 added the operating contract and AR-579/580 promoted reusable assets. The diagnostic still shows typography, spacing, and radius literals as a maturity gap. This unit makes the full design-system raw-literal audit pass for the console baseline by moving eligible CSS values onto tokens.
inputs:
  - reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - scripts/design_system_gate.py
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console.py
  - tests/test_design_system_gate.py
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console.py
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - tests/test_ui_design_assets.py
  - tests/test_design_system_gate.py
  - agents/lead_engineer/tasks/TASK-AR-581.md
  - agents/lead_engineer/tasks/units/TASK-AR-581/UNIT-TASK-AR-581-001.md
scope: Tokenize CSS literal debt only. Do not redesign visuals, change routes/data contracts, or split the entire console module in this unit.
acceptance:
  - Full design-system raw-literal scan passes with --all-ui.
  - Default diff-aware design-system gate still passes.
  - The served CSS still includes the token scale and existing UI console regression tests remain green.
  - Residual debt is limited to physical module decomposition and non-CSS layout geometry, not typography/spacing/radius CSS literals.
verification:
  - python scripts/design_system_gate.py --all-ui --check
  - python scripts/design_system_gate.py --check
  - python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_design_assets.py --check
  - python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q
  - python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT --check
  - python scripts/work_item_classifier.py --check
handoff: Report token aliases added, full-audit gate result, test result, and remaining physical decomposition debt.
stop_condition: Stop after token CSS literal debt is removed, all-ui gate passes, documentation/evidence are recorded, and the claim is released.
verified_at: 2026-06-18T15:35:00+09:00
verified_by: codex-design-system-token-debt-581
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500.json
  - reviews/VERIFY-2026-06-18-task-ar-581-20260618154000.json
  - reviews/W4B-2026-06-18-TASK-AR-581.md
resolution: done
completed_at: 2026-06-18T15:40:00+09:00
---

# UNIT-TASK-AR-581-001 - Tokenize console CSS literal debt

## Context

AR-578 added the operating contract and AR-579/580 promoted reusable assets. The diagnostic still shows typography, spacing, and radius literals as a maturity gap. This unit makes the full design-system raw-literal audit pass for the console baseline by moving eligible CSS values onto tokens.

## Inputs

- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- scripts/design_system_gate.py
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console.py
- tests/test_design_system_gate.py
- tests/test_ui_design_assets.py
- tests/test_ui_console.py

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console.py
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- tests/test_ui_design_assets.py
- tests/test_design_system_gate.py
- agents/lead_engineer/tasks/TASK-AR-581.md
- agents/lead_engineer/tasks/units/TASK-AR-581/UNIT-TASK-AR-581-001.md

## Scope

Tokenize CSS literal debt only. Do not redesign visuals, change routes/data contracts, or split the entire console module in this unit.

## Steps

1. Add token aliases for observed typography, spacing, and radius values.
2. Replace eligible CSS font-size, padding, margin, gap, and border-radius px values with token references.
3. Replace the remaining raw stroke color with a semantic token.
4. Tighten tests so all-ui design-system audit is part of the expected passing baseline.
5. Update DESIGN-SYSTEM.md with the enforced raw-literal audit status and residual non-CSS layout boundary.
6. Run verification and record W4 evidence.

## Acceptance Criteria

- Full design-system raw-literal scan passes with --all-ui.
- Default diff-aware design-system gate still passes.
- The served CSS still includes the token scale and existing UI console regression tests remain green.
- Residual debt is limited to physical module decomposition and non-CSS layout geometry, not typography/spacing/radius CSS literals.

## Verification

- `python scripts/design_system_gate.py --all-ui --check`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT --check`
- `python scripts/work_item_classifier.py --check`

## Handoff

Report token aliases added, full-audit gate result, test result, and remaining physical decomposition debt.

## Stop Boundary

Stop after token CSS literal debt is removed, all-ui gate passes, documentation/evidence are recorded, and the claim is released.

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Typography CSS literals | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` font-size aliases |
| Spacing CSS literals | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` space-px aliases |
| Radius CSS literals | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` radius-px aliases |
| Remaining raw stroke color | `design_token` | `src/agent_runtime/ui_console.py` uses `var(--on-accent)` |
| JS geometry and physical renderer layout | `one_off_for_now` | `src/agent_runtime/ui_console.py` residual decomposition debt |

## Verification Result

- `python scripts/design_system_gate.py --all-ui --check` -> pass, `findings=0`
- `python scripts/design_system_gate.py --check` -> pass
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_design_assets.py --check` -> pass
- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q` -> `168 passed`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py` -> pass
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT --check` -> pass
- `python scripts/work_item_classifier.py --check` -> pass
