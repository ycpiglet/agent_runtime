---
id: TASK-AR-279
display_id: TASK-AR-279
task_uid: 3cf6f3eb-bd8d-4dbf-9775-b9e66384c279
registered_at: 2026-06-11
created_at: 2026-06-11
updated_at: 2026-06-11T08:01:53+09:00
title: Apply visual hierarchy to backlog pane
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 1100
owner: lead_engineer
task_set_id: TASKSET-AR-UI-DESIGN-IMPLEMENTATION
started_at: 2026-06-11T04:51:27+09:00
completed_at: 2026-06-11T08:01:53+09:00
updated: 2026-06-11
tags: [ui-design, backlog, ui-console]
---

# TASK-AR-279 - Apply visual hierarchy to backlog pane

## Goal

Make backlog lanes and task cards easier to scan for status, priority, owner, task set, and evidence without relying on color alone.

## Acceptance Criteria

- Backlog lanes use the active design tokens from `docs/design/agent-runtime/DESIGN.md`.
- Task cards keep id, status, priority, task set, and evidence labels visible.
- Existing task create/update/reorder/archive behavior remains unchanged.

## Outcome

- Added task state enrichment so UI task records expose `task_set_id`, `evidence_count`, and `evidence_label`.
- Reworked backlog cards to show visible labels for status, priority, owner, task set, and evidence without depending on color alone.
- Added lane count badges and mobile card metadata collapse while preserving existing task create/update/reorder/archive routes.

## Verification

- RED: `python -m pytest tests\test_ui_state.py::test_ui_state_enriches_tasks_with_task_set_and_evidence_count -q` failed with missing `task_set_id`.
- RED: `python -m pytest tests\test_ui_console.py::test_ui_console_backlog_cards_surface_status_priority_taskset_and_evidence -q` failed with missing card hierarchy classes.
- RED: mobile metadata assertion failed until `.task-card-meta` was included in the `@media (max-width: 760px)` one-column rule.
- GREEN: `python -m pytest tests\test_ui_console.py tests\test_ui_state.py -q` passed with `29 passed`.
- Focused regression: `python -m pytest tests\test_ui_console.py tests\test_ui_state.py tests\test_ui_commands.py tests\test_backlog_board_tasksets.py -q` passed with `43 passed`.
- Slow follow-up regression: `python -m pytest tests\test_template_message_queue.py -q` passed with `49 passed`; `python -m pytest tests\test_template_smoke.py tests\test_warning_summary_gate_report_summary.py tests\test_warning_summary_strict_ref_policy.py tests\test_verify_rsi_planning_taskset.py -q` passed with `20 passed`.
- Compile: `python -m py_compile src\agent_runtime\ui_console.py src\agent_runtime\ui_state.py` passed.
- Browser: Playwright on `http://127.0.0.1:8767/` confirmed desktop `1440x1000` and mobile `390x844` have visible card labels, no horizontal overflow, and `0` console errors/warnings.
- Full-suite note: `python -m pytest -q` was attempted twice but exceeded local time limits without failure output, so full-suite pass is not claimed for this task.

## Evidence

- `src/agent_runtime/ui_state.py`
- `src/agent_runtime/ui_console.py`
- `tests/test_ui_state.py`
- `tests/test_ui_console.py`
- `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-279-backlog-hierarchy.md`
