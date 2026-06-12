---
title: Work Close Command
date: 2026-06-12
signal: pass
score: 95
tags: [work-cli, closeout, task-ar-372, evidence]
---

# Work Close Command

## Bottom Line

`scripts/work.py close <id>` now gives work items a deterministic done-closeout
path: passed verification evidence and actuals are required before the command
writes completion metadata.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Done evidence guard | pass | `tests/test_work_close.py` blocks pending verification and missing refs |
| Actuals guard | pass | closeout refuses missing `actual_hours` and `actual_tokens` |
| Metadata write | pass | `status`, `resolution`, `completed_at`, `closed_by`, `actual_*` |
| Generated closeout block | pass | marker-delimited `## Closeout` section |
| Generated views | pass | board, work classification, and evidence index refresh after close |
| Schema catalog | pass | `actual_hours` and `closed_by` registered in `WORK-SCHEMA.yml` |
| Self-hosting closeout | pass | `UNIT-TASK-AR-372-006` verified and closed by `work close` |

## Insight

- `work verify` records command evidence; `work close` consumes that evidence
  and refuses to convert pending or unverifiable work into `completed`.
- The generated closeout block uses stable markers so reruns replace the
  machine-owned section instead of accumulating conflicting footers.
- Non-done resolutions are represented by the same command surface, but this
  slice focuses verification on the `done` path because that is the DoD-critical
  route.

## Decision

- Decision: `resolution=done` requires `verification_status: passed`, at least
  one passed verification JSON in `evidence_refs`, `actual_hours`, and
  `actual_tokens`.
- Decision: closeout writes `closed_by` as a lifecycle/audit field rather than
  overloading role/team ownership.
- Decision: `work close` remains deterministic; AI split, criteria, and assign
  proposal behavior stays out of this unit.

## Action Board

| Item | Status | Note |
| --- | --- | --- |
| `work close` CLI | done | deterministic closeout command added |
| `tests/test_work_close.py` | done | success and guardrail coverage |
| `WORK-SCHEMA.yml` | done | closeout fields registered |
| `UNIT-TASK-AR-372-006` | done | verified by `work verify`, closed by `work close` |

## Risks / Blockers

- Existing legacy tasks may still have hand-written completion metadata; backfill
  should remain gradual.
- Failed or stale verification evidence is intentionally not accepted for done
  closeout.

## Next

- Use `work verify` and `work close` together for future deterministic unit
  closeout.
- Continue with proposal-gated `split`, `criteria`, and `assign` tools as
  separate planner-approved units.
