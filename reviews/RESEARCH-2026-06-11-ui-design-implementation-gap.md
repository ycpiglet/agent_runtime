---
type: research
title: UI Design Implementation Gap Review
audience: owner
date: 2026-06-11
status: accepted
signal: watch
score: 92
priority: P1
task_set_id: TASKSET-AR-UI-DESIGN-IMPLEMENTATION
tags: [ui-design, implementation-gap, taskset, owner-brief]
---

# UI Design Implementation Gap Review

## Bottom Line

The completed `TASKSET-AR-UI-DESIGN-SYSTEM` records the design decision, but completed tasks are archived out of the live backlog. The missing operational object is an active implementation task set that keeps UI design application visible until the console panes are actually reviewed and polished.

## Signal

`TASKSET-AR-UI-DESIGN-SYSTEM` exists as completed evidence. The active backlog needs separate implementation work so the Owner can see that design direction is not the same as visual QA completion.

## Insight

Design research, design guide publication, CSS token adoption, pane-by-pane application, responsive polish, and visual QA are different work phases. Closing all of them as one completed design-system task set hides remaining design execution risk.

## Decision

Create `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` with active tasks `TASK-AR-278` through `TASK-AR-284`.

## Action Board

| Task | Status | Focus |
| --- | --- | --- |
| `TASK-AR-278` | in_progress | Console shell design implementation |
| `TASK-AR-279` | planned | Backlog pane visual hierarchy |
| `TASK-AR-280` | planned | Agent and command pane treatment |
| `TASK-AR-281` | planned | Evidence and event pane treatment |
| `TASK-AR-282` | planned | Map, planner, source, and write pane treatment |
| `TASK-AR-283` | planned | Responsive and accessibility polish |
| `TASK-AR-284` | planned | Visual QA and Owner handoff |

## Risks / Blockers

- Risk: design research can look complete while pane-level implementation and visual QA remain incomplete.
- Risk: completed tasksets are archived out of the live board, so active implementation must have its own taskset.
- Blocker: none for registration; implementation remains open.

## Next Steps

- Continue `TASK-AR-278` before marking any pane-level design work complete.
- Keep `TASKSET-AR-UI-DESIGN-SYSTEM` closed as research/design evidence.
- Run focused UI tests and Owner governance before closing `TASKSET-AR-UI-DESIGN-IMPLEMENTATION`.
