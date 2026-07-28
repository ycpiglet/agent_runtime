---
title: TASK-AR-639 UNIT-002 T3 Replan
date: 2026-07-28
signal: pass
score: 97
priority: P0
tags: [task-ar-639, unit-002, t3-replan, lifecycle-reconciliation, recovery]
---

# TASK-AR-639 UNIT-002 T3 Replan

## Bottom Line

Continue with `UNIT-TASK-AR-639-002`. The recorded plan assumption for
`scripts/work.py` changed because UNIT-001 intentionally delivered the planned
registration, verification, and honest-closeout seam. No owner objective or
taskset boundary changed.

The UNIT-002 contract is sharpened by the first live closeout: reconcile the
worker lifecycle tuple, exempt only explicit overlays from worker-only
requirements, represent TASK-AR-631 as recovered without a fabricated claim,
and register every recovery/measurement field emitted by lifecycle tools in
both root and consumer schemas.

## T3 Revalidation

| Check | Result | Decision |
| --- | --- | --- |
| `scripts/work.py` anchor | expected drift | UNIT-001 merged in PR #353 and closed in PR #354 |
| Owner objective | unchanged | one reusable runtime with profile-aware host overlays |
| Next unit | unchanged | scout verdict remains `CONTINUE` with UNIT-002 |
| TASK-AR-631 evidence | durable | W4a and independent W4b exist; no historical claim will be synthesized |
| Closeout schema | new observed gap | `measurement_unavailable_reason` is emitted but currently reported as an unknown-field watch |
| Worker/overlay distinction | required | worker claims require task/unit/worktree/branch/pointer correlation; explicit overlays do not |
| Main CI attempt 1 | watch | one existing non-hermetic cadence recovery test flaked after PR CI passed; unchanged failed-job rerun is in progress and does not expand this unit |

## Replanned Boundaries

- Treat active worker claims, current pointer work, and verified current work
  as the enforcement set; do not force a repository-wide migration of every
  legacy completed item.
- Use durable metadata and evidence, not heuristic commit-message scanning, to
  decide whether implementation is tracked.
- A missing historical W2 claim may pass only with an explicit
  recovered-without-claim marker, a non-empty reason, and existing independent
  evidence. The gate must emit a visible watch.
- Do not manufacture claim JSON, timestamps, token counts, costs, or durations.
- Keep overlay exemptions explicit and narrow; a malformed worker claim cannot
  self-identify as an overlay merely by omitting worker fields.
- Mirror executable gate/schema changes into the shipped consumer template
  without importing root-only optional routing dependencies.
- Mark TASK-AR-631 with the new recovery contract in this unit, but defer its
  final `work close` transition until independent W4b approves UNIT-002.

## Verification

- `python -m pytest tests/test_state_sync_gate.py tests/test_task_claim_dispatcher.py tests/test_work_schema_gate.py -q`
- `python scripts/state_sync_gate.py --check`
- `python scripts/work_schema_gate.py --items --check`
- Root/template parity checks for the changed shared gates and schema fields.
- Independent W4b review by an instance that did not implement UNIT-002.

## Decision

Re-record the plan anchors against this review and dispatch UNIT-002 without
`--skip-plan-check`.
