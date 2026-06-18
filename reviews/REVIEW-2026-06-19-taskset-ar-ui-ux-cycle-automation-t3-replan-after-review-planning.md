---
type: review
id: REVIEW-2026-06-19-taskset-ar-ui-ux-cycle-automation-t3-replan-after-review-planning
status: accepted
signal: replan
task_set_id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
date: 2026-06-19
tags: [ui, ux, design-system, t3-replan]
---

# UI/UX Cycle Automation T3 Replan After Review Planning

## Trigger

`TASK-AR-598` extended `scripts/ui_ux_cycle.py` with `plan-review`, seminar,
meeting, and beta-tester artifact planning. The taskset's previous T3 snapshot
correctly detects that `scripts/ui_ux_cycle.py` changed before dispatching
`TASK-AR-599`.

## Decision

Refresh taskset assumptions around the landed review-planning conductor before
claiming `TASK-AR-599`.

`TASK-AR-599` should build on the existing conductor by adding proposal-only
next-work intake output. It must not register tasks, mutate UI files, mutate
claims, or bypass W0-W6. The implementation remains bounded to:

- `scripts/ui_ux_cycle.py`
- `tests/test_ui_ux_cycle.py`
- `docs/design/agent-runtime/DESIGN-SYSTEM.md`

## Guardrails

- Add a deterministic `propose --dry-run --json` mode.
- Proposal output must distinguish design-direction RFCs, implementation
  refactors, and UX evaluation passes.
- Proposal output must include role routing, target file boundaries, source
  evidence, and owner-gated registration instructions.
- Write mode may only record proposal artifacts under `reviews/` and refresh
  `reviews/INDEX.md`; it must not create or edit work items, claims, or UI
  source files.
