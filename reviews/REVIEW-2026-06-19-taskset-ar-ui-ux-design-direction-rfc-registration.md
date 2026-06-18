---
title: UI UX Design Direction RFC Registration
date: 2026-06-19
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# UI UX Design Direction RFC Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-UI-UX-DESIGN-DIRECTION-CYCLE`, taskset
`TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC`, `3` task records, and `1` unit specs
from one input file.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Input schema | pass | `agent-runtime-work-registration/v1` |
| Reservation ledger | pass | task display IDs fulfilled during registration |
| Generated records | pass | initiative, taskset plan, task files, unit specs included, and generated views refreshed |

## Decision

Use `scripts/work.py new --input <json>` as the deterministic planner-facing
registration path for this taskset shape.

## Action Board

| Task | Title | Status |
| --- | --- | --- |
| `TASK-AR-600` | Run lead-designer UI direction seminar | planned |
| `TASK-AR-601` | Publish UI design direction RFC | planned |
| `TASK-AR-602` | Derive next UI implementation and UX evaluation units | planned |

## Risks / Blockers

- This deterministic path does not perform AI decomposition, assignment, or
  approval bypass.
- Additional work is still needed for closeout automation and proposal-backed
  AI split/criteria/assign behavior.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
- Continue into `work close`, `work verify`, and AI proposal tools after unit generation is covered.
