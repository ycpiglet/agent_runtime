---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-589-001
work_uid: cf4683ed-48c8-48e6-ad66-3cd178fa6b1b
kind: unit
parent_id: TASK-AR-589
unit_id: UNIT-TASK-AR-589-001
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
summary: Self-host Geist + Geist Mono as font tokens
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Geist/Geist Mono are OFL 1.1, built for dev tools, matching the stated direction. Self-host variable woff2; no CDN.
inputs:
  - reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 3)
  - src/agent_runtime/ui_console_assets.py (CSS/tokens)
  - docs/design/agent-runtime/DESIGN.md
target_files:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
scope: Add @font-face for self-hosted woff2 + wire to type tokens.
acceptance:
  - Console uses self-hosted Geist/Geist Mono via tokens; no font CDN; OFL recorded.
verification:
  - python scripts/design_system_gate.py --check --all-ui
handoff: Fonts done; unit 2 adds icons.
stop_condition: If OFL terms or a self-host artifact are unclear, flag before committing binaries.
completed_at: 2026-06-20T05:55:00+09:00
verification_evidence: reviews/W4B-2026-06-20-TASK-AR-589.md
---

# UNIT-TASK-AR-589-001 - Self-host Geist + Geist Mono as font tokens

## Context

Geist/Geist Mono are OFL 1.1, built for dev tools, matching the stated direction. Self-host variable woff2; no CDN.

## Inputs

- reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 3)
- src/agent_runtime/ui_console_assets.py (CSS/tokens)
- docs/design/agent-runtime/DESIGN.md

## Target Files

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py

## Scope

Add @font-face for self-hosted woff2 + wire to type tokens.

## Steps

1. Vendor Geist + Geist Mono woff2 (confirm OFL); record license.
2. Add @font-face and bind font-family tokens.
3. Verify rendering + fallback stack.

## Acceptance Criteria

- Console uses self-hosted Geist/Geist Mono via tokens; no font CDN; OFL recorded.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`

## Handoff

Fonts done; unit 2 adds icons.

## Stop Boundary

If OFL terms or a self-host artifact are unclear, flag before committing binaries.
