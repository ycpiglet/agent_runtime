---
title: v0.8 Adoption and Enforcement Registration
date: 2026-07-28
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# v0.8 Adoption and Enforcement Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-V080-ADOPTION-ENFORCEMENT`, taskset
`TASKSET-AR-V080-ADOPTION-ENFORCEMENT`, `13` task records, and `15` unit specs
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
| `TASK-AR-639` | Restore lifecycle truth and Work CLI producer-consumer parity | planned |
| `TASK-AR-640` | Introduce profile and ownership-aware host configuration | planned |
| `TASK-AR-641` | Build brownfield adopt planning and generated-tree filtering | planned |
| `TASK-AR-642` | Make sync ownership-aware and explicitly reconcilable | planned |
| `TASK-AR-643` | Enforce consumer template and skill dependency closure | planned |
| `TASK-AR-644` | Provide cross-platform start, compact, and resume continuity hooks | planned |
| `TASK-AR-645` | Make compound and scribe task-linked and host-configurable | planned |
| `TASK-AR-646` | Make model routing economically effective and auditable | planned |
| `TASK-AR-647` | Adopt native Allimbot events and security-service guardrails | planned |
| `TASK-AR-648` | Run the Bean Wiki web-content pilot | planned |
| `TASK-AR-649` | Run the Allimbot security-service pilot | planned |
| `TASK-AR-650` | Rehearse Autofolio v0.6 to v0.8 migration | planned |
| `TASK-AR-651` | Prepare v0.8.0 release candidate from pilot evidence | planned |

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
