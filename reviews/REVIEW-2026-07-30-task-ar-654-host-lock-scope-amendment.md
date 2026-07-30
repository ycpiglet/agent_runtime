---
type: planning
title: TASK-AR-654 host lock scope amendment
date: 2026-07-30
signal: pass
score: 99
tags: [planning-record, task-ar-654, scope-amendment, host-lock]
---

# TASK-AR-654 host lock scope amendment

## Bottom Line

The focused merge-queue suite and root/template parity passed. The mandatory
template drift check then correctly reported that the packaged merge-queue
change requires regenerating
`tests/fixtures/host/agent_runtime.lock.json`. The registered unit and active
claim omitted that deterministic artifact. No lock edit occurred before this
amendment.

## Decision

- Add `tests/fixtures/host/agent_runtime.lock.json` to the TASK-AR-654 unit and
  active claim footprints.
- Add the lock drift check to the task and unit verification commands.
- Re-record T0/T3 assumptions with this review and the lock as anchors before
  regenerating it in the claimed worktree.
- Keep every other boundary unchanged; this does not add release, workflow,
  configuration, or TASK-AR-648 pilot scope.
