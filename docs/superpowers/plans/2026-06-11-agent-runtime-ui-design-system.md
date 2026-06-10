# Agent Runtime UI Design System Plan

## Objective

Restore and finish the UI research, planning, task registration, and first implementation pass for the Agent Runtime console.

## Scope

1. Register a dedicated UI design task set with non-conflicting task ids.
2. Capture the design decision and research synthesis in project docs.
3. Apply the selected Linear-like operator-console direction to the existing UI console.
4. Preserve the current HTML ids, API routes, and JavaScript behavior.
5. Add tests that lock the chosen design tokens.
6. Update backlog/status records so the work is resumable.

## Task set

`TASKSET-AR-UI-DESIGN-SYSTEM`

| Task | Title | Outcome |
| --- | --- | --- |
| TASK-AR-264 | Capture UI research and plan | Completed research/plan record |
| TASK-AR-265 | Publish design guide | Project-specific design guide |
| TASK-AR-266 | Apply console shell | Linear-like dark operator shell |
| TASK-AR-267 | Restyle operational views | Cards, tabs, lanes, and detail panel updated |
| TASK-AR-268 | Elevate evidence and command states | Status colors and command affordances clarified |
| TASK-AR-269 | Mobile and accessibility polish | Responsive layout and visible labels preserved |
| TASK-AR-270 | Close UI task set | Backlog/status/tests/docs aligned |

## Acceptance criteria

1. `src/agent_runtime/ui_console.py` exposes the new token set while preserving existing app structure.
2. `tests/test_ui_console.py` checks the selected token anchors.
3. `docs/design/agent-runtime/DESIGN.md` records the product-specific design direction.
4. Task files exist for every UI task and are marked completed with evidence.
5. Backlog and status documents record the closeout.
6. `BACKLOG-BOARD.md` is regenerated from task metadata.

## Validation plan

Run focused UI and backlog-board tests, then run Owner governance gate after the task metadata and generated board are synchronized.
