---
title: TASK-AR-648 Blocked Unit Redispatch P0 Replan
date: 2026-07-29
status: active
signal: stop
score: 0
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-007
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [replan, taskset-dispatch, blocked-unit, claim-first, release-blocker]
---

# TASK-AR-648 Blocked Unit Redispatch P0 Replan

## Bottom Line

Do not claim the portable-continuity unit yet. The pre-claim canonical
`taskset_dispatcher.py plan` selected historical
`UNIT-TASK-AR-648-002`, whose status is `blocked`, instead of the newly
registered planned unit.

No claim or worktree was created. Repair unit selection first, obtain
independent approval, then claim the separately registered continuity unit.

## Reproducer

At Runtime `573b3cdfbcc5e7255bbb2a503b7568e723c946a6`, after registering a planned
continuity unit and pointing `TASK-AR-648.unit_spec` at it:

```text
python scripts/taskset_dispatcher.py plan \
  TASKSET-AR-V080-ADOPTION-ENFORCEMENT \
  --agent-role lead-engineer \
  --team-id evaluation-office \
  --mode orchestrator \
  --now 2026-07-29T23:36:00+09:00 \
  --json
```

returned:

```text
next_task_id=TASK-AR-648
unit_id=UNIT-TASK-AR-648-002
unit_spec_path=agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-002.md
```

`UNIT-002` is a preserved failed Bean remediation with
`status: blocked` and `verification_status: failed`.

## Root Cause

`_ready_unit_for_task` removes only done statuses. It leaves `blocked` units
inside `open_units`, looks for `worker_ready`, `ready`, or `in_progress`, and
falls back to the lexicographically first item when none matches. A task with
blocked history and a new `planned` unit therefore redispatches the oldest
failure.

This is P0 in this workflow because following the generated claim command would
re-enter a frozen remediation scope and wrong worktree policy.

## Required Contract

- Normal plan/start must never select `blocked`, failed, cancelled, rejected,
  or other terminal/non-runnable units.
- Select an explicit runnable current unit deterministically:
  `in_progress`, then `worker_ready`/`ready`, then `planned`/`assigned`.
- When the task's canonical `unit_spec` names one runnable unit, prefer it over
  historical siblings.
- If a task has unit specs but none are runnable, stop without emitting a claim
  command.
- Unknown unit status must fail closed rather than enter the fallback.
- Preserve dependency and model-routing checks for the selected unit.

## Sequence

1. Move portable continuity remediation to `UNIT-008`.
2. Use `UNIT-007` only for blocked-unit selection repair.
3. Capture RED tests before editing the selector.
4. Run focused, full, source/template parity, governance, and independent W4b.
5. Only after exact-product approval may `UNIT-008` be claimed.

## Stop Boundary

Stop on any blocked-unit selection, ambiguous fallback, implicit resume,
source/template drift, Bean or Allimbot mutation, consumer commit,
release/version/tag/package action, push, publish, deploy, credential access,
network delivery, or independent P0/P1.
