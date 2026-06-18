---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-580
display_id: TASK-AR-580
task_uid: f906471c-6aed-4fe3-8ce9-a58a5bf47db6
work_id: TASK-AR-580
work_uid: f906471c-6aed-4fe3-8ce9-a58a5bf47db6
kind: task
parent_id: TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
registered_at: 2026-06-18T14:50:00+09:00
started_at: 2026-06-18T14:36:09+09:00
created_at: 2026-06-18T14:50:00+09:00
updated_at: 2026-06-18T15:00:00+09:00
title: Promote console components and domain patterns
status: completed
priority: P0
difficulty: L
est_hours: 8
est_tokens: 16000
owner: design-system-steward
team: ui-ux
initiative_id: INIT-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-580/UNIT-TASK-AR-580-001.md
reservation_id: RES-20260618-145000-82c7b90d-01
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-component-patterns
created_by: codex-planner
summary: Extend the executable UI asset layer so the console has named component APIs and domain pattern APIs instead of relying on ad hoc card/table/button markup in page renderers.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-18T15:00:00+09:00
verified_by: codex-design-system-component-patterns-580
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000.json
  - reviews/VERIFY-2026-06-18-task-ar-580-20260618150500.json
  - reviews/W4B-2026-06-18-TASK-AR-580.md
resolution: done
completed_at: 2026-06-18T15:00:00+09:00
closed_by: codex-design-system-component-patterns-580
actual_hours: 5
actual_tokens: 14000
---

# TASK-AR-580 - Promote console components and domain patterns

## Goal

- Extend the executable UI asset layer so the console has named component APIs and domain pattern APIs instead of relying on ad hoc card/table/button markup in page renderers.

## Scope

- Add vanilla-JS helpers in src/agent_runtime/ui_design_assets.py and use them from representative existing renderers in src/agent_runtime/ui_console.py. Preserve selectors, routes, data contracts, and visual behavior.

## Acceptance Criteria

- src/agent_runtime/ui_design_assets.py exposes named helpers for Button/Card/Table/Modal primitives and TaskLane, ClaimCard, EvidencePanel, CommandBar, and StateMachinePanel domain patterns.
- src/agent_runtime/ui_console.py uses the new helpers in representative renderers for board lanes/task cards, command cards, evidence panels, and state-machine panels while preserving existing CSS class names.
- tests prove the helpers are served in /app.js, selected helpers are not redefined inside ui_console.py, and the current UI console regression suite remains green.
- docs/design/agent-runtime/DESIGN-SYSTEM.md records the concrete promoted pattern APIs and the remaining one-off boundary.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS --check`
- `python scripts/work_item_classifier.py --check`

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Button, Card, Table, Modal shell primitives | `ui_component` | `src/agent_runtime/ui_design_assets.py::componentButton/componentCard/componentTable/componentModalShell` |
| Task lane and claim card | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternTaskLane/patternClaimCard` |
| Evidence and audit panels | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternEvidencePanel/patternAuditCard` |
| Command bar and state-machine legend | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternCommandBar/patternStateMachinePanelLegend` |
| Remaining SVG/layout-heavy renderers | `one_off_for_now` | `src/agent_runtime/ui_console.py` |

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-18T15:00:00+09:00`
- Resolution: `done`
- Actual hours: `5`
- Actual tokens: `14000`
- Closed by: `codex-design-system-component-patterns-580`
- Evidence:
  - `reviews/VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000.json`
  - `reviews/VERIFY-2026-06-18-task-ar-580-20260618150500.json`
  - `reviews/W4B-2026-06-18-TASK-AR-580.md`
<!-- work-close:end -->
