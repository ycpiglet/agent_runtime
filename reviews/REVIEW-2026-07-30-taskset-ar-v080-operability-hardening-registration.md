---
title: v0.8 Operability Hardening Registration
date: 2026-07-30
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# v0.8 Operability Hardening Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-V080-OPERABILITY-HARDENING`, taskset
`TASKSET-AR-V080-OPERABILITY-HARDENING`, `7` task records, and `7` unit specs
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
| `TASK-AR-652` | Bind model tiers to actual execution and economic receipts | planned |
| `TASK-AR-653` | Close the Scribe source-debt and active-work loop | planned |
| `TASK-AR-654` | Require Compound for declared repeated failures | planned |
| `TASK-AR-655` | Add atomic heartbeat and renewal to task claims | planned |
| `TASK-AR-656` | Make lifecycle hooks composable and deduplicated | planned |
| `TASK-AR-657` | Ship consumer adoption and failure operating skills | planned |
| `TASK-AR-658` | Expose Runtime operability health in the read-only UI | planned |

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
