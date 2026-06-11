---
id: TASK-AR-281
display_id: TASK-AR-281
task_uid: 082e33ce-bc3e-4dfb-a9dd-9cd7b2193281
registered_at: 2026-06-11
created_at: 2026-06-11
started_at: 2026-06-11T10:17:46+09:00
completed_at: 2026-06-11T10:32:26+09:00
updated_at: 2026-06-11T10:32:26+09:00
title: Apply design treatment to evidence and event panes
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 1100
owner: lead_engineer
task_set_id: TASKSET-AR-UI-DESIGN-IMPLEMENTATION
updated: 2026-06-11
tags: [ui-design, evidence, events, ui-console]
---

# TASK-AR-281 - Apply design treatment to evidence and event panes

## Goal

Make events, errors, evidence, and replay records look audit-ready and severity-aware.

## Acceptance Criteria

- Evidence, event, error, and replay cards use pass/warn/fail treatment with visible labels.
- Event filters remain visible and route-compatible.
- Evidence is treated as a primary UI object, not secondary metadata.

## Completion Evidence

- Added audit-card treatment for events, errors, evidence, and replay records in `src/agent_runtime/ui_console.py`.
- Preserved existing event filter controls and `/api/events` route compatibility.
- Added focused UI test coverage for audit-card hierarchy, visible labels, filters, and pass/warn/fail selectors.
- Focused verification passed with `python -m pytest tests/test_ui_console.py tests/test_ui_state.py tests/test_ui_commands.py -q` (`43 passed`).
- Headless Playwright verification passed on `http://127.0.0.1:8769/` for desktop and mobile with no horizontal overflow or console errors.
