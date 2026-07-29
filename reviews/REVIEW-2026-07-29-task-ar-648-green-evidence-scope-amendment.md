---
type: planning
title: TASK-AR-648 Bean green evidence scope amendment
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-002
signal: pass
score: 99
priority: P0
tags: [planning-record, task-ar-648, scope-amendment, bean-wiki, green-replay]
---

# TASK-AR-648 Bean green evidence scope amendment

## Bottom Line

The integrated five-P0 repair is fixed at
`1c44a0e5dfb1c94b173d9e45086802be5cbe3c1a`. Its full suite passed with
`2580 passed, 3 skipped`, and the independent integrated reviewer returned
`APPROVE`. No Runtime file has yet been written to the fresh Bean Wiki replay
worktree.

The active unit names the original red fixture and report, but its replan
explicitly requires those artifacts to remain immutable. This amendment adds
distinct green artifacts before the replay begins; it does not authorize
rewriting the red evidence.

## Decision

- Add `tests/fixtures/pilots/bean-wiki/evidence-green.json` as the sanitized,
  pinned green replay fixture.
- Add `reviews/PILOT-BEAN-WIKI-v080-GREEN.md` as the green replay report.
- Add `reviews/W4B-2026-07-29-unit-task-ar-648-002.md` as the independent
  verification report for the exact integrated repair and replay evidence.
- Add `reviews/INDEX.md` as the mechanically regenerated evidence index for
  the new amendment, green report, and W4b report.
- Keep `scripts/pilot_acceptance.py` and `tests/test_pilot_acceptance.py` in
  scope so the validator can preserve the red contract while validating a
  separate green contract and rejecting false-green tampering.
- Add this amendment to the active unit and claim footprints and re-record
  the taskset plan assumptions before any new Agent Runtime evidence file is
  written.

## Invariants

- `reviews/PILOT-BEAN-WIKI-v080.md` and
  `tests/fixtures/pilots/bean-wiki/evidence.json` remain byte-identical.
- The Bean replay remains offline and disposable: no host commit, origin push,
  publish, deploy, credential read, network delivery, or `src/content`
  mutation.
- A green contract requires zero P0 findings, zero adoption/reconcile
  conflicts, fresh configured state projection, no example-derived
  classification findings, preserved host/content digests, and pinned full
  host and Runtime commit identities.
- Requested, selected, resolved, and observed model fields remain distinct.
  Token, cost, or savings claims remain unavailable unless an authoritative
  provider observation exists.

## Stop Boundary

Stop on any new P0, red-evidence mutation, absolute local path in sanitized
evidence, unsupported model/cost claim, host/content mutation, external
effect, primary-checkout mutation, or failure of independent verification.
