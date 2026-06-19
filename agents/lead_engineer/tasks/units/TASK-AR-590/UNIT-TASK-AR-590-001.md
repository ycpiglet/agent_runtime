---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-590-001
work_uid: 2dddc013-c5dd-4066-ab4e-db0f4300615f
kind: unit
parent_id: TASK-AR-590
unit_id: UNIT-TASK-AR-590-001
task_id: TASK-AR-590
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T01:04:15+09:00
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Recolorable unDraw state illustrations
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: unDraw is single-accent recolorable with no attribution; tint to the console accent for instant on-brand empty/error/loading.
inputs:
  - reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 4)
  - existing Empty/Error/Loading handling
  - src/agent_runtime/ui_design_assets.py
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
scope: Vendor a few unDraw SVGs, recolor to accent token, wire into state patterns.
acceptance:
  - State screens show accent-tinted unDraw art; no raw color literals.
verification:
  - python scripts/design_system_gate.py --check --all-ui
handoff: State art done; unit 2 does palette + sparkline.
stop_condition: Confirm unDraw license terms before committing assets.
---

# UNIT-TASK-AR-590-001 - Recolorable unDraw state illustrations

## Context

unDraw is single-accent recolorable with no attribution; tint to the console accent for instant on-brand empty/error/loading.

## Inputs

- reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 4)
- existing Empty/Error/Loading handling
- src/agent_runtime/ui_design_assets.py

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py

## Scope

Vendor a few unDraw SVGs, recolor to accent token, wire into state patterns.

## Steps

1. Vendor relevant unDraw SVGs; record license.
2. Tint via accent token (currentColor/CSS var).
3. Wire into componentEmptyState + error/loading patterns.

## Acceptance Criteria

- State screens show accent-tinted unDraw art; no raw color literals.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`

## Handoff

State art done; unit 2 does palette + sparkline.

## Stop Boundary

Confirm unDraw license terms before committing assets.
