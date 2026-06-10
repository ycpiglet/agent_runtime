---
id: TASK-AR-278
display_id: TASK-AR-278
task_uid: 1238e8f8-9a3d-4f6a-87d2-f0f04e68c278
registered_at: 2026-06-11
created_at: 2026-06-11
started_at: 2026-06-11
updated_at: 2026-06-11T00:00:00+09:00
title: Apply Agent Runtime design system to console shell
status: in_progress
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

## Evidence

- `docs/design/agent-runtime/DESIGN.md`
- `docs/superpowers/plans/2026-06-11-ui-design-implementation.md`
- `reviews/RESEARCH-2026-06-11-ui-design-implementation-gap.md`
