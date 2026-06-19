---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-592
display_id: TASK-AR-592
task_uid: 57b81740-6ec9-4d0e-a165-c352867258f2
work_id: TASK-AR-592
work_uid: 57b81740-6ec9-4d0e-a165-c352867258f2
kind: task
parent_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
registered_at: 2026-06-20T05:18:36+09:00
started_at: 2026-06-20T07:13:38+09:00
created_at: 2026-06-20T05:18:36+09:00
updated_at: 2026-06-20T07:40:00+09:00
title: Accessibility + responsive pass on the new visual system
status: completed
priority: P2
difficulty: M
est_hours: 5
est_tokens: 12000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-VISUAL-SYSTEM-INTEGRATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-592/UNIT-TASK-AR-592-001.md
reservation_id: RES-20260620-051836-edde9f5a-02
origin_type: owner_request
origin_ref: chat:2026-06-19-autonomous-loop
created_by: lead-engineer
summary: Ensure the new visual components meet WCAG AA (contrast, roles, labels, keyboard, reduced-motion) and render responsively (desktop + mobile widths) in both themes.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-20T07:40:00+09:00
verified_by: codex-independent-verifier-task-ar-592-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-592-a11y-responsive.json
  - reviews/W4B-2026-06-20-TASK-AR-592.md
  - reviews/evidence/TASK-AR-592/desktop-dependencies.png
  - reviews/evidence/TASK-AR-592/mobile-dependencies.png
  - reviews/evidence/TASK-AR-592/mobile-workload.png
  - reviews/evidence/TASK-AR-592/knowledge-graph.png
resolution: done
completed_at: 2026-06-20T07:40:00+09:00
closed_by: codex-interface-designer-task-ar-592-20260620
actual_hours: 3
actual_tokens: 12000
---

# TASK-AR-592 - Accessibility + responsive pass on the new visual system

## Goal

- Ensure the new visual components meet WCAG AA (contrast, roles, labels, keyboard, reduced-motion) and render responsively (desktop + mobile widths) in both themes.

## Scope

- Audit patternAgentAvatar, the graph, componentIcon, componentSparkline, the data-viz palette, and the state illustrations for: WCAG AA contrast in dark+light; appropriate ARIA roles/labels (graphs/sparklines as img with labels, decorative avatars aria-hidden, state components role=status/alert); keyboard operability of any interactive graph nodes; prefers-reduced-motion respected. Add responsive CSS so the new visuals degrade gracefully at mobile widths. Token-driven; escaping symmetric; ASCII JS.

## Acceptance Criteria

- New visual components carry correct ARIA roles/labels (decorative SVGs aria-hidden; informative ones role=img + aria-label; state components role=status/alert).
- Contrast of palette/status/graph colors meets WCAG AA in both dark and light themes.
- prefers-reduced-motion disables non-essential animation; interactive graph nodes are keyboard operable.
- Responsive CSS keeps the new visuals usable at mobile widths; design_system_gate --all-ui green.

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_design_assets.py tests/test_design_system_gate.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/owner_governance_gate.py`
