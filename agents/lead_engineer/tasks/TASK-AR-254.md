---
id: TASK-AR-254
display_id: TASK-AR-254
task_uid: 1515a1ec-6b56-4d60-a684-313ce4de7447
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
title: Create task worktree before task-set claim
status: completed
priority: P0
importance: High
difficulty: M
est_hours: 4
est_tokens: 1000
task_set_id: TASKSET-AR-COLLAB-CONCURRENCY
team: agent-runtime-core
owner: worktree-dispatcher
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:20:00+09:00
completed_at: 2026-06-10T23:20:00+09:00
tags: [worktree, taskset, dispatcher]
audit_log: [scripts/taskset_dispatcher.py, tests/test_taskset_dispatcher.py]
---

## Goal

Make task-set start create the missing task worktree before claim creation, preventing false isolation claims.

## Completion Criteria

- `taskset_dispatcher start` runs the worktree command when the target worktree is missing.
- Claim creation still happens only after worktree preflight passes.
- Tests use `AGENT_RUNTIME_GIT` to prove the create path without touching real git state.

## Result

- Added worktree creation before claim creation.
- Preserved duplicate task-set claim and worktree validation behavior.
