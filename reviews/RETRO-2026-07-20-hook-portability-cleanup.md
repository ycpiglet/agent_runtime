---
type: retro
title: Hook Portability and Worktree Cleanup Retro
date: 2026-07-20
task_id: TASK-AR-601
unit_id: UNIT-TASK-AR-601-001
task_set_id: TASKSET-AR-HOOK-PORTABILITY-CLEANUP
status: recorded
signal: pass
---

# Hook Portability and Worktree Cleanup Retro

## Keep

- Keep Codex hook manifests platform-neutral and leave platform-specific wrappers as optional entrypoints rather than shared-manifest dependencies.
- Keep executable Git hook modes and `core.hooksPath=.githooks` under bootstrap verification.
- Keep W4b genuinely independent: its first rejection found a dedicated update-notify contract that the initial focused suite missed.

## Change

- When a shared hook command changes, search event-specific tests and generated-host documentation in addition to the manifest and broad portability test.
- Include event-specific regression files in the unit verification command before the first W4a run.
- At W5, use the serial merge queue from the start. After W4b releases the claim, remove the clean claimed worktree while preserving its committed branch so the claim-first gate and merge-queue checkout can both succeed.

## Result

- The corrected focused suite passed with `56 passed`; the real pre-commit hook, bootstrap check, W4a, independent W4b, and post-integration task verification all passed.
- The task branch was merged through the serial queue and both task-created local branches and the task worktree were removed after ancestor checks.
- No remote push or external repository mutation was performed.
