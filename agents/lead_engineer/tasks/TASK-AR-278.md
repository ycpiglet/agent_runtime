---
id: TASK-AR-278
display_id: TASK-AR-278
task_uid: 1238e8f8-9a3d-4f6a-87d2-f0f04e68c278
registered_at: 2026-06-11
created_at: 2026-06-11
started_at: 2026-06-11
updated_at: 2026-06-11T02:48:39+09:00
completed_at: 2026-06-11T02:48:39+09:00
title: Apply Agent Runtime design system to console shell
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-UI-DESIGN-IMPLEMENTATION
updated: 2026-06-11
tags: [ui-design, ui-console, visual-system]
---

# TASK-AR-278 - Apply Agent Runtime design system to console shell

## Goal

Apply the accepted Linear-like operator-console design system to the top-level console shell, metrics, tabs, forms, and detail panel.

## Acceptance Criteria

- `src/agent_runtime/ui_console.py` uses the accepted `--canvas`, `--primary`, and dark operator-console token ladder.
- The existing HTML ids, API routes, and JavaScript behavior stay unchanged.
- `tests/test_ui_console.py` locks the key design tokens.

## Outcome

- Replaced the console CSS shell so the served DOM classes (`shell`, `layout`, `work-surface`, `kanban`, forms, tabs, views, and detail panel) are styled directly.
- Preserved existing HTML ids, API routes, JavaScript selectors, task mutation routes, and runtime command routes.
- Added a quiet `/favicon.ico` response to remove the browser 404 console error during local UI verification.

## Verification

- RED: `python -m pytest tests\test_ui_console.py::test_ui_console_shell_css_targets_served_dom_classes -q` failed on missing `.shell`.
- GREEN: `python -m pytest tests\test_ui_console.py -q` passed with `15 passed`.
- Browser: Playwright desktop `1440x1000` and mobile `390x844` checks reported no horizontal overflow and zero console errors or warnings on `http://127.0.0.1:8766/`.

## Evidence

- `docs/design/agent-runtime/DESIGN.md`
- `docs/superpowers/plans/2026-06-11-ui-design-implementation.md`
- `reviews/RESEARCH-2026-06-11-ui-design-implementation-gap.md`
- `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-278-console-shell.md`
