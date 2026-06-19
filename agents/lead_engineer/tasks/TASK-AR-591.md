---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-591
display_id: TASK-AR-591
task_uid: a5da8af2-1b71-4cc8-a602-05cc0b80725f
work_id: TASK-AR-591
work_uid: a5da8af2-1b71-4cc8-a602-05cc0b80725f
kind: task
parent_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
registered_at: 2026-06-20T05:18:36+09:00
started_at: 2026-06-20T08:12:15+09:00
created_at: 2026-06-20T05:18:36+09:00
updated_at: 2026-06-20T08:25:00+09:00
title: Wire new visual components into live views + boot-verify the console
status: completed
priority: P1
difficulty: M
est_hours: 5
est_tokens: 12000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-VISUAL-SYSTEM-INTEGRATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-591/UNIT-TASK-AR-591-001.md
reservation_id: RES-20260620-051836-edde9f5a-01
origin_type: owner_request
origin_ref: chat:2026-06-19-autonomous-loop
created_by: lead-engineer
summary: Ensure the AR-587..590 visual components actually appear in the relevant live console views, and that the served console boots and renders them without error.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-20T08:25:00+09:00
verified_by: codex-independent-verifier-task-ar-591-20260620
completed_at: 2026-06-20T08:25:00+09:00
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-591-live-wiring.json
  - reviews/W4B-2026-06-20-TASK-AR-591.md
  - reviews/evidence/TASK-AR-591/ops-dashboard-sparkline.png
---

# TASK-AR-591 - Wire new visual components into live views + boot-verify the console

## Goal

- Ensure the AR-587..590 visual components actually appear in the relevant live console views, and that the served console boots and renders them without error.

## Scope

- Audit the served console (ui_console_assets.py renderers) and ensure: patternAgentAvatar is used in every agent listing/identity surface; the layered/force graph rendering is used in dependency/state-machine/live-map views; componentIcon replaces remaining ad-hoc HTML-entity icons everywhere; componentSparkline is used in metric/throughput surfaces; the data-viz palette tokens drive all chart/graph colors; componentEmptyState/ErrorState/LoadingState are used for all empty/error/loading surfaces. Boot the console (python stdlib server) on a test port and verify GET / and the served JS/CSS assets return 200 and parse (node --check on the served JS), with no Python import/runtime errors. Fix any integration gaps found. Keep token-driven (no raw literals); escape all interpolated strings (Python html.escape <-> JS escapeHtml symmetric); JS ASCII-only (cp949 node --check).

## Acceptance Criteria

- The served console boots on a test port; GET / and the served JS/CSS assets return HTTP 200; the served JS passes node --check; no Python import/runtime errors.
- patternAgentAvatar, the graph rendering, componentIcon, componentSparkline, data-viz palette tokens, and the empty/error/loading state components each appear in at least their primary intended live view (documented in the PR).
- No remaining ad-hoc HTML-entity icons where componentIcon applies; design_system_gate --check --all-ui findings=0.
- All interpolated strings escaped; new JS ASCII-only.

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_design_assets.py tests/test_design_system_gate.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/owner_governance_gate.py`

## Result

- Completed live wiring verification for the AR-587..590 visual components.
- Preserved the prior avatar, icon, graph, data-viz token, and empty/error/loading
  integrations, then strengthened the metric surface by rendering
  `componentSparkline` in the live Ops Dashboard eval trend.
- Browser evidence confirms `#/ops/dashboard` renders the eval sparkline with
  `role="img"` and `aria-label="Eval score sparkline, 6 runs"` while keeping the
  detailed trend chart.
