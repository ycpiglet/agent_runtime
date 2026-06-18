---
title: Design System Debt Consolidation Registration
date: 2026-06-18
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Design System Debt Consolidation Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION`, taskset
`TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION`, `2` task records, and `0` unit specs
from one input file.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Input schema | pass | `agent-runtime-work-registration/v1` |
| Reservation ledger | pass | task display IDs fulfilled during registration |
| Generated records | pass | initiative, taskset plan, task files, unit specs deferred, and generated views refreshed |

## Decision

Use `scripts/work.py new --input <json>` as the deterministic planner-facing
registration path for this taskset shape.

## Action Board

| Task | Title | Status |
| --- | --- | --- |
| `TASK-AR-583` | Consolidate transitional px-alias tokens into a semantic scale | planned |
| `TASK-AR-584` | Promote remaining view-specific JS renderers into pattern modules | planned |

## Risks / Blockers

- This deterministic path does not perform AI decomposition, assignment, or
  approval bypass.
- Additional work is still needed for closeout automation and proposal-backed
  AI split/criteria/assign behavior.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
- Continue into unit spec generation, `work close`, `work verify`, and AI proposal tools.
