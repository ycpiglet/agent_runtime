---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-583
display_id: TASK-AR-583
task_uid: c8e43f0d-2b3c-4eb2-bafe-1cb67cda51b4
work_id: TASK-AR-583
work_uid: c8e43f0d-2b3c-4eb2-bafe-1cb67cda51b4
kind: task
parent_id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
registered_at: 2026-06-18T18:43:04+09:00
started_at: 2026-06-20T08:52:02+09:00
created_at: 2026-06-18T18:43:04+09:00
updated_at: 2026-06-20T08:55:08+09:00
title: Consolidate transitional px-alias tokens into a semantic scale
status: completed
priority: P2
difficulty: M
est_hours: 4
est_tokens: 8000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
reservation_id: RES-20260618-184304-fbffba5c-01
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-followups
created_by: lead-engineer
summary: Replace the transitional --space-px-* / --radius-px-* aliases in the console asset CSS with a designed semantic scale (for example --space-1..n, --radius-sm/md/lg), mapping existing values onto the nearest scale step, without re-introducing raw literals.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-20T08:55:08+09:00
verified_by: codex-independent-verifier-task-ar-583-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-583-semantic-scale.json
  - reviews/W4B-2026-06-20-TASK-AR-583.md
resolution: done
completed_at: 2026-06-20T08:55:08+09:00
closed_by: codex-design-system-steward-task-ar-583-20260620
actual_hours: 1
actual_tokens: 3500
---

# TASK-AR-583 - Consolidate transitional px-alias tokens into a semantic scale

## Goal

- Replace the transitional --space-px-* / --radius-px-* aliases in the console asset CSS with a designed semantic scale (for example --space-1..n, --radius-sm/md/lg), mapping existing values onto the nearest scale step, without re-introducing raw literals.

## Scope

- Edit token definitions in ui_console_assets.py / ui_design_assets.py and their consumers. Do not change visual behavior beyond intended scale snapping. Land the new scale as experimental, promote to stable per DESIGN-SYSTEM.md maturity tiers. Owner-facing routing: design-system-steward.

## Acceptance Criteria

- ui_console_assets.py / ui_design_assets.py expose a designed semantic spacing and radius scale; transitional --space-px-* / --radius-px-* aliases are removed or re-expressed as semantic-scale references.
- python scripts/design_system_gate.py --check --all-ui reports findings=0 (no raw literals re-introduced).
- DESIGN-SYSTEM.md Executable asset layer and Maturity tiers sections reflect the promoted semantic scale.

## Verification

- `python -m pytest tests/test_design_system_gate.py tests/test_ui_design_assets.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check --all-ui`

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Stable semantic spacing scale | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` |
| Stable semantic radius scale | `design_token` | `src/agent_runtime/ui_design_assets.py::UI_TOKEN_SCALE_CSS` |
| Legacy px alias removal guard | `design_token` gate/test | `tests/test_ui_design_assets.py` |
| Executable asset layer wording | `design_token` documentation | `docs/design/agent-runtime/DESIGN-SYSTEM.md` |

## Result

- Confirmed `ui_design_assets.UI_TOKEN_SCALE_CSS` exposes semantic spacing and
  radius tokens without `--space-px-*` or `--radius-px-*` aliases.
- Updated the design-system operating contract so the executable token layer no
  longer describes the retired aliases as current console infrastructure.
- Added regression coverage that asserts the served CSS contains semantic
  spacing/radius tokens and no transitional px aliases.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-20T08:55:08+09:00`
- Resolution: `done`
- Actual hours: `1`
- Actual tokens: `3500`
- Closed by: `codex-design-system-steward-task-ar-583-20260620`
- Evidence:
  - `reviews/VERIFY-2026-06-20-task-ar-583-semantic-scale.json`
  - `reviews/W4B-2026-06-20-TASK-AR-583.md`
<!-- work-close:end -->
