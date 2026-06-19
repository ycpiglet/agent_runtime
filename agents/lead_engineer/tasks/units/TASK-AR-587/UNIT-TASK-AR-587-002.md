---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-587-002
work_uid: a6cd69f4-4144-402c-8480-665eda070eb1
kind: unit
parent_id: TASK-AR-587
unit_id: UNIT-TASK-AR-587-002
task_id: TASK-AR-587
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
summary: Deterministic role accent + console placement
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Role must read at a glance without relying on the avatar alone; accent maps to existing role/status tokens and must be WCAG-safe in both themes.
inputs:
  - src/agent_runtime/ui_design_assets.py (patternAgentAvatar)
  - the role/status token set
  - agents/project/ORG-MODEL.yml (role list)
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
scope: Add a deterministic role->accent mapping drawn in our SVG and place the avatar in at least one view.
acceptance:
  - Role accent is deterministic, token-driven, WCAG AA in both themes, and visible in a console view.
verification:
  - python scripts/design_system_gate.py --check --all-ui
handoff: Agent identity system complete.
stop_condition: If any accent fails WCAG AA in either theme, adjust the token mapping before closing.
---

# UNIT-TASK-AR-587-002 - Deterministic role accent + console placement

## Context

Role must read at a glance without relying on the avatar alone; accent maps to existing role/status tokens and must be WCAG-safe in both themes.

## Inputs

- src/agent_runtime/ui_design_assets.py (patternAgentAvatar)
- the role/status token set
- agents/project/ORG-MODEL.yml (role list)

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py

## Scope

Add a deterministic role->accent mapping drawn in our SVG and place the avatar in at least one view.

## Steps

1. Map each ORG-MODEL role to an accent token deterministically.
2. Draw the accent ring/background in our own SVG around the avatar.
3. Place patternAgentAvatar in agent cards and/or the live agent map.
4. Verify WCAG AA in dark and light; capture desktop+mobile evidence.

## Acceptance Criteria

- Role accent is deterministic, token-driven, WCAG AA in both themes, and visible in a console view.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`

## Handoff

Agent identity system complete.

## Stop Boundary

If any accent fails WCAG AA in either theme, adjust the token mapping before closing.
