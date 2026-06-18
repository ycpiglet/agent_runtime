---
title: Self Improvement Remediation Registration
date: 2026-06-17
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Self Improvement Remediation Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE`, taskset
`TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE`, `4` task records, and `4` unit specs
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
| `TASK-AR-573` | Create real scribe evidence | planned |
| `TASK-AR-574` | Route dormant monitored roles | planned |
| `TASK-AR-575` | Exercise or retire low-reuse runtime assets | planned |
| `TASK-AR-576` | Publish remediation delta report | planned |

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
