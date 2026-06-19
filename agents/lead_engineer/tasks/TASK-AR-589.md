---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-589
display_id: TASK-AR-589
task_uid: f283db13-7e6b-47dc-848c-205bfbec2f22
work_id: TASK-AR-589
work_uid: f283db13-7e6b-47dc-848c-205bfbec2f22
kind: task
parent_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
registered_at: 2026-06-20T01:04:15+09:00
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T05:55:00+09:00
title: Typography + icon foundation (Geist OFL fonts + Lucide icons)
status: done
priority: P2
difficulty: M
est_hours: 5
est_tokens: 10000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-589/UNIT-TASK-AR-589-001.md
reservation_id: RES-20260620-010415-e5a1738e-03
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Self-host OFL fonts (Geist + Geist Mono) as font tokens and vendor the Lucide (ISC) inline-SVG icon set behind a componentIcon helper.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
completed_at: 2026-06-20T05:55:00+09:00
verification_status: passed
verification_evidence: reviews/W4B-2026-06-20-TASK-AR-589.md
---

# TASK-AR-589 - Typography + icon foundation (Geist OFL fonts + Lucide icons)

## Goal

- Self-host OFL fonts (Geist + Geist Mono) as font tokens and vendor the Lucide (ISC) inline-SVG icon set behind a componentIcon helper.

## Scope

- Add self-hosted woff2 Geist + Geist Mono with @font-face wired to typography tokens (no Google/CDN at runtime; record OFL). Vendor Lucide SVGs (ISC) and add a componentIcon(name) helper returning inline SVG that inherits currentColor/tokens. Land as experimental; classify per assetization rules. Confirm OFL/ISC terms before committing the binaries.

## Acceptance Criteria

- Geist + Geist Mono are self-hosted (woff2) and bound to typography tokens; no runtime font CDN; OFL recorded.
- Lucide icons are vendored (ISC, recorded) and exposed via componentIcon returning inline SVG that inherits token color.
- design_system_gate --all-ui passes; a representative screen shows the new fonts + icons with desktop+mobile evidence.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
