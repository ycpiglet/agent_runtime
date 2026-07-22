---
type: planning
title: TASK-AR-600 host lock scope amendment
date: 2026-07-22
signal: pass
score: 99
tags: [planning-record, task-ar-600, scope-amendment, host-lock]
---

# TASK-AR-600 host lock scope amendment

## Bottom Line

The first focused tests passed, then the deterministic lock check correctly reported that changing
the managed template helper requires regenerating `tests/fixtures/host/agent_runtime.lock.json`.
The registered unit and active claim omitted that generated artifact. No lock edit occurred before
this amendment.

## Decision

- Add `tests/fixtures/host/agent_runtime.lock.json` to the TASK-AR-600 unit and active claim
  footprints.
- Re-record T0/T3 assumptions with the lock as an anchor before regenerating it in the claimed
  worktree.
- Keep all other scope boundaries unchanged; no workflow, secret, branch-protection, or merge-policy
  surface is added.

