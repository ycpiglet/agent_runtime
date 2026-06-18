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
created_at: 2026-06-18T18:43:04+09:00
updated_at: 2026-06-18T18:43:04+09:00
title: Consolidate transitional px-alias tokens into a semantic scale
status: planned
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
