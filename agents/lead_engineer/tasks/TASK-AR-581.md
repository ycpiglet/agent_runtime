---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-581
display_id: TASK-AR-581
task_uid: f446b363-e61d-4049-a687-d7f984b5bf66
work_id: TASK-AR-581
work_uid: f446b363-e61d-4049-a687-d7f984b5bf66
kind: task
parent_id: TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT
registered_at: 2026-06-18T15:20:00+09:00
started_at: 2026-06-18T15:04:39+09:00
created_at: 2026-06-18T15:20:00+09:00
updated_at: 2026-06-18T15:40:00+09:00
title: Tokenize console typography spacing and radius literals
status: completed
priority: P0
difficulty: L
est_hours: 8
est_tokens: 18000
owner: design-system-steward
team: ui-ux
initiative_id: INIT-AR-DESIGN-SYSTEM-TOKEN-DEBT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-581/UNIT-TASK-AR-581-001.md
reservation_id: RES-20260618-152000-2632eb0a-01
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-token-debt
created_by: codex-planner
summary: Resolve the diagnostic report's token maturity gap for typography, spacing, radius, and raw style literals in the console CSS baseline.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-18T15:40:00+09:00
verified_by: independent-auditor-design-system-581
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500.json
  - reviews/VERIFY-2026-06-18-task-ar-581-20260618154000.json
  - reviews/W4B-2026-06-18-TASK-AR-581.md
resolution: done
completed_at: 2026-06-18T15:40:00+09:00
closed_by: codex-design-system-token-debt-581
actual_hours: 4
actual_tokens: 12000
---

# TASK-AR-581 - Tokenize console typography spacing and radius literals

## Goal

- Resolve the diagnostic report's token maturity gap for typography, spacing, radius, and raw style literals in the console CSS baseline.

## Scope

- Extend the executable token scale in src/agent_runtime/ui_design_assets.py, mechanically replace eligible CSS font-size, padding, margin, gap, and border-radius px literals in src/agent_runtime/ui_console.py with var() token references, replace the remaining raw stroke color with an existing semantic token, and document the residual boundary for non-CSS layout geometry.

## Acceptance Criteria

- src/agent_runtime/ui_design_assets.py exposes token aliases for all px values used by console typography, spacing, and radius CSS declarations.
- src/agent_runtime/ui_console.py no longer contains raw color, font-size, padding, margin, gap, or border-radius literals that design_system_gate --all-ui flags.
- scripts/design_system_gate.py --all-ui --check passes on the current checkout without hiding findings behind a watch-only baseline.
- docs/design/agent-runtime/DESIGN-SYSTEM.md records that full raw-literal audit is now enforced for the existing console baseline and distinguishes remaining layout geometry debt from token debt.

## Verification

- `python scripts/design_system_gate.py --all-ui --check`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT --check`
- `python scripts/work_item_classifier.py --check`

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Typography CSS literals | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` font-size aliases |
| Spacing CSS literals | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` space-px aliases |
| Radius CSS literals | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` radius-px aliases |
| Remaining raw stroke color | `design_token` | `src/agent_runtime/ui_console.py` uses `var(--on-accent)` |
| JS geometry and physical renderer layout | `one_off_for_now` | `src/agent_runtime/ui_console.py` residual decomposition debt |

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-18T15:40:00+09:00`
- Resolution: `done`
- Actual hours: `4`
- Actual tokens: `12000`
- Closed by: `codex-design-system-token-debt-581`
- Evidence:
  - `reviews/VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500.json`
  - `reviews/VERIFY-2026-06-18-task-ar-581-20260618154000.json`
  - `reviews/W4B-2026-06-18-TASK-AR-581.md`
<!-- work-close:end -->
