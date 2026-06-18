---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-579
display_id: TASK-AR-579
task_uid: ae9daa9c-87ca-4ce5-8496-b3e7d537548f
work_id: TASK-AR-579
work_uid: ae9daa9c-87ca-4ce5-8496-b3e7d537548f
kind: task
parent_id: TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION
registered_at: 2026-06-18T13:20:00+09:00
started_at: 2026-06-18T14:15:52+09:00
created_at: 2026-06-18T13:20:00+09:00
updated_at: 2026-06-18T14:33:00+09:00
title: Extract first UI asset layer from console
status: completed
priority: P0
difficulty: L
est_hours: 6
est_tokens: 12000
owner: design-system-steward
team: ui-ux
initiative_id: INIT-AR-DESIGN-SYSTEM-ASSETIZATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-579/UNIT-TASK-AR-579-001.md
reservation_id: RES-20260618-132000-7fce0b06-01
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-assetization
created_by: codex-planner
summary: Create the first executable UI asset layer for Agent Runtime: design token scale, reusable UI primitive helpers, domain pattern helpers, and a diff-aware design-system gate that supports incremental refactoring of the existing console baseline.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-18T14:33:00+09:00
verified_by: codex-design-system-assetization-579
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300.json
  - reviews/VERIFY-2026-06-18-task-ar-579-20260618143800.json
resolution: done
completed_at: 2026-06-18T14:33:00+09:00
closed_by: codex-design-system-assetization-579
actual_hours: 4
actual_tokens: 12000
---

# TASK-AR-579 - Extract first UI asset layer from console

## Goal

- Create the first executable UI asset layer for Agent Runtime: design token scale, reusable UI primitive helpers, domain pattern helpers, and a diff-aware design-system gate that supports incremental refactoring of the existing console baseline.

## Scope

- Add a Python-served UI asset module and use it from src/agent_runtime/ui_console.py for existing progress, empty-state, audit metadata, and surface metadata helpers. Update gate logic and tests. Do not migrate to a frontend framework or rewrite unrelated console views.

## Acceptance Criteria

- src/agent_runtime/ui_design_assets.py exists as the first executable design-system asset layer with a token scale CSS bundle and UI component/pattern JS bundle.
- src/agent_runtime/ui_console.py imports and serves those assets instead of keeping the selected primitive and pattern helpers only inside the page monolith.
- docs/design/agent-runtime/DESIGN-SYSTEM.md records the concrete asset module and the baseline-budget rule for incremental UI refactors.
- scripts/design_system_gate.py default mode checks added UI diff lines so baseline literals in unchanged ui_console.py do not block safe extraction, while explicit path/all-ui scans remain available for full debt audits.
- Focused tests prove the asset layer is served, imported, and reused by the console, and prove the gate catches newly-added raw literals.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION --check`

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Type, spacing, and radius scale | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` |
| Progress bar, empty state, state chip, card, and metadata grid helpers | `ui_component` | `src/agent_runtime/ui_design_assets.py::UI_COMPONENTS_JS` |
| Audit and surface metadata helpers | `pattern_component` | `src/agent_runtime/ui_design_assets.py::patternAuditMeta/patternSurfaceMeta` |
| Remaining view-specific renderers | `one_off_for_now` | `src/agent_runtime/ui_console.py` |

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-18T14:33:00+09:00`
- Resolution: `done`
- Actual hours: `4`
- Actual tokens: `12000`
- Closed by: `codex-design-system-assetization-579`
- Evidence:
  - `reviews/VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300.json`
  - `reviews/VERIFY-2026-06-18-task-ar-579-20260618143800.json`
<!-- work-close:end -->
