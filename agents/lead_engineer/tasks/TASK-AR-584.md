---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-584
display_id: TASK-AR-584
task_uid: ba370d39-6930-4201-b2f7-504b66928001
work_id: TASK-AR-584
work_uid: ba370d39-6930-4201-b2f7-504b66928001
kind: task
parent_id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
registered_at: 2026-06-18T18:43:04+09:00
created_at: 2026-06-18T18:43:04+09:00
updated_at: 2026-06-19T01:36:21+09:00
title: Promote remaining view-specific JS renderers into pattern modules
status: completed
started_at: 2026-06-19T00:58:28+09:00
verification_status: passed
verified_at: 2026-06-19T01:27:09+09:00
verified_by: independent-verifier-task-ar-584-20260619
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-584-20260619011843.json
  - reviews/VERIFY-2026-06-19-task-ar-584-root-integration-20260619013817.json
w4b_evidence: reviews/W4B-2026-06-19-TASK-AR-584.md
priority: P2
difficulty: L
est_hours: 6
est_tokens: 12000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
reservation_id: RES-20260618-184304-fbffba5c-02
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-followups
created_by: lead-engineer
summary: Move view-specific JS renderers (data-heavy SVG layouts, calendar grids, office-map placement, import/export previews, ops dashboard charts) from the served renderer asset into pattern modules with stable APIs, reducing one-off renderer debt.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
resolution: done
completed_at: 2026-06-19T01:36:21+09:00
closed_by: uiux-pattern-renderers-20260619-584
actual_hours: 2.5
actual_tokens: 12000
---

# TASK-AR-584 - Promote remaining view-specific JS renderers into pattern modules

## Goal

- Move view-specific JS renderers (data-heavy SVG layouts, calendar grids, office-map placement, import/export previews, ops dashboard charts) from the served renderer asset into pattern modules with stable APIs, reducing one-off renderer debt.

## Scope

- Extract renderers into pattern helpers in ui_design_assets.py and reuse them from ui_console_assets.py. Preserve rendered behavior; verify visually. Land new pattern APIs as experimental, promote on adoption. Owner-facing routing: interface-designer with design-system-steward review.

## Acceptance Criteria

- At least the SVG-layout and calendar-grid renderers are served through stable pattern APIs in ui_design_assets.py and consumed by ui_console_assets.py.
- DESIGN-SYSTEM.md Executable asset layer pattern table lists the newly promoted pattern APIs and their console usage.
- python scripts/design_system_gate.py --check --all-ui reports findings=0.

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_design_assets.py -q`
- `python scripts/design_system_gate.py --check --all-ui`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T01:36:21+09:00`
- Resolution: `done`
- Actual hours: `2.5`
- Actual tokens: `12000`
- Closed by: `uiux-pattern-renderers-20260619-584`
- Evidence:
  - `reviews/VERIFY-2026-06-19-task-ar-584-20260619011843.json`
  - `reviews/VERIFY-2026-06-19-task-ar-584-root-integration-20260619013817.json`
<!-- work-close:end -->
