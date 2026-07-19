---
title: Role Routing Closeout Reliability Registration
date: 2026-07-19
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Role Routing Closeout Reliability Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY`, taskset
`TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY`, `1` task records, and `1` unit specs
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

Implementation must preserve ordinary closeout routing while closing two
specific lifecycle gaps observed in TASK-AR-594: generated overlay claims had
no handoff/log pointers, and releasing an overlay would call the same routing
hook again. Overlay artifacts will be created atomically with deterministic
paths, and release-time review routing will be skipped only when
`claim.overlay` is true.

## Action Board

| Task | Title | Status |
| --- | --- | --- |
| `TASK-AR-601` | Make routed review overlays cleanly releasable | planned |

## Risks / Blockers

- The recursion guard must not suppress review routing for ordinary worker
  claims; end-to-end coverage is required for both paths.
- Role-routing remains controlled by the existing committed flag and must be
  inert when disabled.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
- Continue into `work close`, `work verify`, and AI proposal tools after unit generation is covered.
