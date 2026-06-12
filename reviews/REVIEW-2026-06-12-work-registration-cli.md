---
title: Work Registration CLI Closeout
date: 2026-06-12
signal: pass
score: 94
tags: [work-registration, work-cli, task-ar-372, metadata, reservation-ledger]
---

# Work Registration CLI Closeout

## Bottom Line

`UNIT-TASK-AR-372-002` is complete: planners now have a deterministic
`scripts/work.py new --input <json>` path for registering an initiative,
taskset plan, tasks, and registration review without hand-editing every surface.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Structured input creation | pass | `tests/test_work_registration.py` creates initiative, plan, two tasks, review, owner-doc pointer, registry row, board, and classification |
| Idempotence | pass | second run returns `already_exists` and does not duplicate reservations |
| Conflict handling | pass | duplicate display IDs and missing required fields fail before partial files |
| Reservation ledger | pass | explicit and auto display IDs become fulfilled reservation rows |
| Board metadata | pass | `backlog_board.py` reads `TASKSET-DEFINITIONS.json` registry |

## Decision

Use JSON as the first deterministic input format. It keeps the command
dependency-free and leaves AI-generated split/criteria/assign behavior for
separate B-mode proposal-gated units.

## Action Board

| Item | Status | Owner | Next Evidence |
| --- | --- | --- | --- |
| `UNIT-TASK-AR-372-002` | done | lead-engineer | `scripts/work.py`, focused tests |
| Unit creation in `work.py` | open | planning-office | next TASK-AR-372 unit |
| AI `split/criteria/assign` tools | deferred | planner | B-mode proposal records |

## Risks / Blockers

- This command creates task records, not worker-ready unit specs yet.
- It updates local repository surfaces only; external approvals and destructive
  work remain out of scope.
- Existing taskset metadata still has hardcoded defaults plus registry overlay;
  a later cleanup can migrate hardcoded definitions into the registry.

## Next

- Extend `work.py` to optionally create worker-ready unit specs from structured
  input.
- Add `work close` only after completion footer and actuals fields are settled.
- Keep AI decomposition, criteria, and assignment behind B-mode proposal review.
