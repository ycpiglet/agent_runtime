---
type: integration-decision
title: Remote Main Integration and Task ID Collision
date: 2026-07-22
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
status: approved
owner: lead-engineer
signal: pass
score: 96
---

# Remote main integration and TASK-AR-600 collision

## Bottom Line

The published remote task keeps `TASK-AR-600`, while the unstarted local
release task moves to `TASK-AR-602`; both histories remain intact and the
normal merge path stays safe.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Published identity preserved | pass | remote auto-merge task remains `TASK-AR-600` |
| Local identity deconflicted | pass | release task and unit resolve as `TASK-AR-602` |
| Integration strategy | pass | normal merge; no force-push or history discard |

## Context

The local upstream-intake taskset registered the v0.7.0 release task as
`TASK-AR-600` at `2026-07-19T10:28:06+09:00`. A parallel taskset later
registered a different `TASK-AR-600` at `2026-07-19T10:34:25+09:00` and was
published to `origin/main` through PR #292. The records have distinct UUIDs,
but their human-facing IDs and canonical paths collide, so a normal merge
cannot preserve both records.

## Decision

- Preserve the already-published remote `TASK-AR-600` identity for the
  auto-merge integrity task.
- Reclassify the still-unstarted local v0.7.0 release task, and its unit, to the
  next unreserved display ID: `TASK-AR-602` / `UNIT-TASK-AR-602-001`.
- Preserve the release task UUIDs, registration timestamp, parent taskset,
  reservation group, scope, acceptance criteria, and planned execution order.
- Update only references that currently resolve to the local release task,
  then merge `origin/main` normally. Do not force-push or discard either lane.
- Regenerate board/classification views after the merge and re-record plan
  assumptions before dispatching the next implementation claim.

## Action Board

| Action | Owner | Status |
| --- | --- | --- |
| Rename the unpublished release record | lead-engineer | complete |
| Merge `origin/main` and regenerate views | lead-engineer | complete |
| Revalidate both tasksets before dispatch | lead-engineer | required |

## Verification

- `TASK-AR-600` and `TASK-AR-602` each resolve to exactly one task file and one
  unit directory after integration.
- `python scripts/task_identity.py check`
- `python scripts/backlog_board.py --check`
- `python scripts/taskset_work_gate.py --check --task-set-id TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT`
- `python scripts/taskset_work_gate.py --check --task-set-id TASKSET-AR-AUTO-MERGE-INTEGRITY`
- `git rev-list --left-right --count main...origin/main` reports no behind
  commits before the next push.

## Scope boundary

This decision repairs the merge-time identity collision only. It does not
implement the remote auto-merge task or change release readiness by itself.

## Risks / Blockers

- Stale references to the old local `TASK-AR-600` identity would route release
  work to the wrong record; identity and generated-view gates must remain green.
- A force-push would discard published work and is outside this decision.

## Next

- Record post-merge assumptions for both affected tasksets.
- Dispatch only the next registered, unclaimed unit after all T2 checks pass.
