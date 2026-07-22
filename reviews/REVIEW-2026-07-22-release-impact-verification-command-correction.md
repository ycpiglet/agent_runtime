---
type: planning
title: Release-impact verification command correction
date: 2026-07-22
signal: pass
score: 98
tags: [planning-record, verification, task-ar-600, release-impact]
---

# Release-impact verification command correction

## Bottom Line

Pre-dispatch readiness found that `TASK-AR-600` and four newly registered tasks referenced
`scripts/root_template_parity_gate.py`, which does not exist in this repository. No claim or
implementation had started. The worker records are corrected to use their focused parity assertions
plus the existing deterministic host-lock check.

## Decision

- `TASK-AR-600`: replace the nonexistent command with
  `python scripts/regen_host_lock_if_needed.py --check` because only the managed template helper is
  in scope and the host lock is its shipping oracle.
- `TASK-AR-603`, `TASK-AR-604`, `TASK-AR-605`, and `TASK-AR-608`: remove the nonexistent command;
  their focused tests must assert root/template equality, and the already recorded host-lock command
  remains mandatory.
- Refresh the affected T0 plan snapshots before W2 dispatch. Do not use `--skip-plan-check`.

## Action Board

| Action | Status |
| --- | --- |
| Correct task and unit verification commands | Done |
| Re-run unit readiness and assumption checks | Next |
| Claim `TASK-AR-600` only after T2 passes | Next |

