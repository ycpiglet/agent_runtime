---
title: v0.8 Operability Hardening T0 Replan
date: 2026-07-30
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
status: approved
signal: pass
priority: P1
reviewer: codex-root-task-ar-650-planner
tags: [t0, replan, operability, registration, release-dependency]
---

# v0.8 Operability Hardening T0 Replan

## Trigger

The initial T0 snapshot was recorded while
`TASKSET-AR-V080-OPERABILITY-HARDENING` was created. Immediately afterward,
the design record was updated with the concrete task IDs produced by that
registration and the corresponding TASK-AR-651 dependency boundary.
`plan_assumption_gate.py --check` correctly reported
`anchor-hash-changed` for the design record.

## Drift classification

This is an expected post-registration documentation change, not a scope or
authority expansion.

- The seven registered tasks are the same model-routing, Scribe, Compound,
  task-claim, hook, consumer-skill, and UI work already approved in the design.
- Priority remains six release-critical P1 tasks followed by one non-blocking
  P2 UI task.
- TASK-AR-651 now names TASK-AR-652 through TASK-AR-657 as prerequisites,
  implementing the existing release-blocked decision.
- Basketball remains excluded.
- Provider calls, credentials, installs, consumer commits, version changes,
  tags, pushes, publication, deployment, and release remain outside scope.

The implementation anchors `scripts/model_routing.py`,
`scripts/task_claim_dispatcher.py`, and `scripts/work.py` did not change during
this documentation update.

## Decision

Accept the generated task IDs and RC dependency mapping as the concrete form
of the original plan. Re-record the same four anchors after this review, then
require the assumption gate to pass before dispatch.

The next eligible task remains TASK-AR-652. No worktree or claim is created by
this replan, and no transition into RC work is approved.
