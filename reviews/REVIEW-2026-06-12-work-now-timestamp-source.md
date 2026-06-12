---
title: Work Now Timestamp Source Closeout
date: 2026-06-12
signal: pass
score: 95
tags: [work-registration, work-cli, task-ar-372, timestamps, metadata]
---

# Work Now Timestamp Source Closeout

## Bottom Line

`UNIT-TASK-AR-372-004` is complete: the root checkout now has the canonical
`scripts/now.py` timestamp generator and the Work CLI exposes it through
`python scripts/work.py now`.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Root time source | pass | `scripts/now.py` |
| Work CLI surface | pass | `scripts/work.py now` |
| Output formats | pass | `tests/test_now.py` validates local, UTC, date, and epoch shapes |
| Registration regression | pass | `tests/test_work_registration.py` still passes |

## Insight

- This closes the broken root reference to `scripts/now.py` without a broad
  timestamp refactor.
- The work CLI can now be the deterministic entry point for generated metadata
  timestamps.
- Future closeout and verification commands should call this same utility
  rather than duplicating date formatting.

## Decision

- Decision: use `scripts/now.py` as the root canonical timestamp script.
- Decision: expose the same behavior as `work.py now` for users staying inside
  the Work CLI.
- Decision: leave repo-wide timestamp caller migration gradual and opportunistic.

## Action Board

| Item | State | Owner | Evidence |
| --- | --- | --- | --- |
| `UNIT-TASK-AR-372-004` | done | lead-engineer | `scripts/now.py`, `work.py now`, tests |
| `work close` | open | planning-office | next TASK-AR-372 unit |
| `work verify` | open | planning-office | next TASK-AR-372 unit |
| AI `split` / `criteria` / `assign` | deferred | planner | B-mode proposal-gated future units |

## Risks / Blockers

- Some existing scripts still call `datetime.now()` directly; this unit does not
  claim repo-wide migration.
- Local timezone output depends on the host timezone by design.

## Next

- Implement `work verify` and `work close` so completion metadata, evidence refs,
  actuals, and verification timestamps are generated rather than hand-written.
