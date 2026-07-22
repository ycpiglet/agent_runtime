---
title: Release Impact Remediator Registration
date: 2026-07-22
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Release Impact Remediator Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION`, taskset
`TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION`, `7` task records, and `7` unit specs
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
| `TASK-AR-603` | Unify canonical task ID producers and consumers | planned |
| `TASK-AR-604` | Persist canonical task start status | planned |
| `TASK-AR-605` | Make the generated session dashboard self-contained | planned |
| `TASK-AR-606` | Activate configured pre-commit hooks on POSIX hosts | planned |
| `TASK-AR-607` | Make transient-spawn recovery testing deterministic | planned |
| `TASK-AR-608` | Preserve quoted hashes in frontmatter scalars | planned |
| `TASK-AR-609` | Classify initiative records by canonical kind | planned |

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
