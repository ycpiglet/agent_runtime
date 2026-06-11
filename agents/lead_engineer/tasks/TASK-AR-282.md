---
id: TASK-AR-282
display_id: TASK-AR-282
task_uid: 3d7b5d8e-d813-44b1-9574-76cbd2d6d282
registered_at: 2026-06-11
created_at: 2026-06-11
started_at: 2026-06-11T10:47:46+09:00
completed_at: 2026-06-11T10:59:38+09:00
updated_at: 2026-06-11T10:59:38+09:00
title: Apply design treatment to map planner source and write panes
status: completed
priority: P2
difficulty: M
est_hours: 3
est_tokens: 1000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-DESIGN-IMPLEMENTATION
updated: 2026-06-11
tags: [ui-design, maps, planner, sources, writes]
---

# TASK-AR-282 - Apply design treatment to map planner source and write panes

## Goal

Bring graph, state-machine, roadmap, planner, source, and write surfaces into the same operator-console design model.

## Acceptance Criteria

- Map and planner panes use the accepted card, border, and status language.
- Source and write panes preserve read/write boundaries.
- Derived map/source views do not look like direct mutation controls.

## Completion Evidence

- Added shared surface-card treatment for graph, state-machine, roadmap, planning, source, and write command surfaces in `src/agent_runtime/ui_console.py`.
- Preserved read/write boundaries with explicit Boundary and Mutation labels, including read-only map/source surfaces and write command surfaces.
- Added focused UI coverage for map, planner, source, and write pane card markers, metadata labels, and boundary styling.
- Focused verification passed with `python -m pytest tests/test_ui_console.py tests/test_ui_state.py tests/test_ui_commands.py -q` (`44 passed`).
- `python -m py_compile src/agent_runtime/ui_console.py` and `python scripts/owner_governance_gate.py` passed.
- Headless Playwright verification passed on `http://127.0.0.1:8770/` for desktop and mobile map/planner/source/write tab checks with no horizontal overflow or console errors.
