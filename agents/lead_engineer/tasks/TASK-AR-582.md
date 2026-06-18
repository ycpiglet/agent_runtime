---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-582
display_id: TASK-AR-582
task_uid: 15ac2d6e-173c-4b02-89a3-649ab3e72632
work_id: TASK-AR-582
work_uid: 15ac2d6e-173c-4b02-89a3-649ab3e72632
kind: task
parent_id: TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
registered_at: 2026-06-18T15:55:00+09:00
started_at: 2026-06-18T15:16:35+09:00
created_at: 2026-06-18T15:55:00+09:00
updated_at: 2026-06-18T16:15:00+09:00
title: Split console served asset strings
status: completed
priority: P0
difficulty: L
est_hours: 8
est_tokens: 18000
owner: design-system-steward
team: ui-ux
initiative_id: INIT-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-582/UNIT-TASK-AR-582-001.md
reservation_id: RES-20260618-155500-3fc416dc-01
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-served-asset-split
created_by: codex-planner
summary: Resolve the diagnostic report's single-file HTML/CSS/JS string concentration by moving served assets into a reusable module boundary.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-18T16:15:00+09:00
verified_by: independent-auditor-design-system-582
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000.json
  - reviews/VERIFY-2026-06-18-task-ar-582-20260618161500.json
  - reviews/W4B-2026-06-18-TASK-AR-582.md
resolution: done
completed_at: 2026-06-18T16:15:00+09:00
closed_by: codex-design-system-served-asset-split-582
actual_hours: 4
actual_tokens: 12000
---

# TASK-AR-582 - Split console served asset strings

## Goal

- Resolve the diagnostic report's single-file HTML/CSS/JS string concentration by moving served assets into a reusable module boundary.

## Scope

- Create src/agent_runtime/ui_console_assets.py to own HTML, CSS, and JS strings plus design-system asset composition; update src/agent_runtime/ui_console.py to import and serve those assets; update tests and docs to record the new page assembly boundary.

## Acceptance Criteria

- src/agent_runtime/ui_console.py no longer contains the large HTML, CSS, and JS triple-quoted asset strings.
- src/agent_runtime/ui_console_assets.py owns HTML, CSS, and JS asset composition and still composes UI_TOKEN_SCALE_CSS and UI_COMPONENTS_JS.
- Existing /, /app.css, and /app.js responses remain byte-compatible except for module ownership.
- docs/design/agent-runtime/DESIGN-SYSTEM.md records ui_console_assets.py as the served asset boundary and ui_console.py as API/page response orchestration.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --all-ui --check`
- `python scripts/design_system_gate.py --check`
- `python scripts/design_system_gate.py --path src/agent_runtime/ui_console.py --path src/agent_runtime/ui_console_assets.py --path src/agent_runtime/ui_design_assets.py --check`
- `python -m py_compile src/agent_runtime/ui_console.py src/agent_runtime/ui_console_assets.py src/agent_runtime/ui_design_assets.py scripts/design_system_gate.py`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT --check`
- `python scripts/work_item_classifier.py --check`

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Served HTML/CSS/JS asset strings | `pattern_component` | `src/agent_runtime/ui_console_assets.py` |
| HTTP routing and API response orchestration | `page assembly` | `src/agent_runtime/ui_console.py` |
| Remaining JS view renderers | `one_off_for_now` | `src/agent_runtime/ui_console_assets.py` residual renderer extraction debt |

## Line Count Result

| File | Before | After |
| --- | ---: | ---: |
| `src/agent_runtime/ui_console.py` | 13,269 | 470 |
| `src/agent_runtime/ui_console_assets.py` | 0 | 12,811 |

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-18T16:15:00+09:00`
- Resolution: `done`
- Actual hours: `4`
- Actual tokens: `12000`
- Closed by: `codex-design-system-served-asset-split-582`
- Evidence:
  - `reviews/VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000.json`
  - `reviews/VERIFY-2026-06-18-task-ar-582-20260618161500.json`
  - `reviews/W4B-2026-06-18-TASK-AR-582.md`
<!-- work-close:end -->
