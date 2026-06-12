---
title: Work Registration Unit Scaffold Closeout
date: 2026-06-12
signal: pass
score: 95
tags: [work-registration, work-cli, task-ar-372, unit-specs, readiness-gate]
---

# Work Registration Unit Scaffold Closeout

## Bottom Line

`UNIT-TASK-AR-372-003` is complete: deterministic work registration can now
create optional worker-ready unit specs from structured `tasks[].units[]` input.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Unit input contract | pass | `tests/test_work_registration.py` covers `tasks[].units[]` |
| Readiness gate | pass | generated unit specs are checked with `task_unit_readiness_gate.py` |
| Idempotence | pass | repeated unit-including registration returns `already_exists` |
| Partial-write guard | pass | missing required unit fields fail before `agents/` exists |
| Generated views | pass | `work_item_classifier.py` indexes generated units |

## Insight

- This closes the deterministic registration path from initiative through unit.
- The CLI still does not infer decomposition; it only materializes a
  planner-approved unit contract.
- The next meaningful gap is lifecycle execution: `work close` and `work verify`
  should record actuals, evidence, and verification outcomes without hand-written
  closeout metadata.

## Decision

- Decision: use `tasks[].units[]` for approved unit specs in `work.py new`.
- Decision: keep every required worker-ready unit field explicit; missing fields
  are input failures, not defaults.
- Decision: leave AI `split`, `criteria`, and `assign` behind B-mode proposal
  review.

## Action Board

| Item | State | Owner | Evidence |
| --- | --- | --- | --- |
| `UNIT-TASK-AR-372-001` | done | lead-engineer | `WORK-SCHEMA.yml` and schema gate |
| `UNIT-TASK-AR-372-002` | done | lead-engineer | deterministic task registration CLI |
| `UNIT-TASK-AR-372-003` | done | lead-engineer | deterministic unit spec generation |
| `work close` / `work verify` | open | planning-office | next TASK-AR-372 unit |
| AI `split` / `criteria` / `assign` | deferred | planner | B-mode proposal-gated future units |

## Risks / Blockers

- Existing historical tasks are not bulk-migrated into generated unit specs.
- The CLI still expects planner-approved structured input; it does not create
  units from prose or model output by itself.

## Next

- Add a `work close` / `work verify` unit that records completion metadata,
  evidence refs, actuals, and verification status from commands.
- Keep AI planner tools as proposal generators rather than auto-apply actions.
