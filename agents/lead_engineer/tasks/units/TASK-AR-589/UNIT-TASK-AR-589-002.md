---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-589-002
work_uid: 71d2004c-d301-45e4-844b-5f757acb6037
kind: unit
parent_id: TASK-AR-589
unit_id: UNIT-TASK-AR-589-002
task_id: TASK-AR-589
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
status: done
verification_status: passed
owner: lead-engineer
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T05:55:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Vendor Lucide icon set + componentIcon helper
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Lucide is ISC, clean stroke icons matching the Linear/Notion look; use as inline SVG inheriting currentColor.
inputs:
  - src/agent_runtime/ui_design_assets.py
  - the existing icon usages / entity glyphs
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
scope: Vendor the needed Lucide SVGs (ISC) + componentIcon(name) returning token-colored inline SVG.
acceptance:
  - Icons render via componentIcon as token-colored inline SVG; Lucide ISC license recorded.
verification:
  - python -m pytest tests/test_design_system_gate.py -q
handoff: Icon foundation done.
stop_condition: Keep scope to vendored subset; do not pull a build-required icon package.
completed_at: 2026-06-20T05:55:00+09:00
verification_evidence: reviews/W4B-2026-06-20-TASK-AR-589.md
---

# UNIT-TASK-AR-589-002 - Vendor Lucide icon set + componentIcon helper

## Context

Lucide is ISC, clean stroke icons matching the Linear/Notion look; use as inline SVG inheriting currentColor.

## Inputs

- src/agent_runtime/ui_design_assets.py
- the existing icon usages / entity glyphs

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py

## Scope

Vendor the needed Lucide SVGs (ISC) + componentIcon(name) returning token-colored inline SVG.

## Steps

1. Vendor the icon subset actually used (ISC); record license.
2. Add componentIcon(name) -> inline SVG inheriting currentColor.
3. Replace ad-hoc glyphs/entities (e.g. &#9776;) with componentIcon where sensible.

## Acceptance Criteria

- Icons render via componentIcon as token-colored inline SVG; Lucide ISC license recorded.

## Verification

- `python -m pytest tests/test_design_system_gate.py -q`

## Handoff

Icon foundation done.

## Stop Boundary

Keep scope to vendored subset; do not pull a build-required icon package.
