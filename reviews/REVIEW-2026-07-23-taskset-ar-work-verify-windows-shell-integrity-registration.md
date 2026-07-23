---
title: Work Verify Windows Shell Integrity Registration
date: 2026-07-23
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Work Verify Windows Shell Integrity Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY`, taskset
`TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY`, `1` task records, and `1` unit specs
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
| `TASK-AR-621` | Preserve work-verify command arguments on Windows | planned |

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
