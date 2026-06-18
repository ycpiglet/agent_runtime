---
title: Noncritical Release Auto-Execution Registration
date: 2026-06-18
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Noncritical Release Auto-Execution Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-RELEASE-AUTOMATION`, taskset
`TASKSET-AR-RELEASE-AUTO-NONCRITICAL`, `2` task records, and `4` unit specs
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
| `TASK-AR-585` | Parameterize the release execution gate (remove hardcoded v0.1.8) | planned |
| `TASK-AR-586` | Wire cadence-bound noncritical auto-release and correct the release-conductor doc | planned |

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
