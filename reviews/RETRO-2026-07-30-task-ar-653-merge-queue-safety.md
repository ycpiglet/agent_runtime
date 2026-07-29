---
id: RETRO-2026-07-30-task-ar-653-merge-queue-safety
title: TASK-AR-653 merge-queue safety retrospective
kind: retrospective
status: completed
signal: pass-with-followup
date: 2026-07-30
task_id: TASK-AR-653
task_set_id: TASKSET-AR-MERGE-QUEUE-SAFETY
---

# TASK-AR-653 Merge-Queue Safety Retrospective

## Outcome

TASK-AR-653 made merge-queue state safe across concurrent processes and linked
worktrees. Mutations now use a repository-common bounded lock, queue and
feedback state resolve to one primary-checkout location, writes use atomic
replacement with durability barriers, and declared task dependencies are
validated and processed in stable topological order. Unknown, cyclic, unmet,
and PR-handoff-only dependencies fail closed.

PR [#387](https://github.com/ycpiglet/agent_runtime/pull/387) passed the Python
3.10, 3.11, and 3.12 matrix and merged as
`1a6854c9574ef36e439fa9059ee8b6ac8f690d8a`. The local full package suite
finished with `2589 passed, 3 skipped`; task-level closeout verification
reconfirmed all 22 focused tests and both root/template parity checks. The
reserved TASK-AR-648 dispatcher/state-sync scope and TASK-AR-652 self-hosted
CI scope were not changed.

## What Worked

- The independent W4b did not merely approve the first implementation. It
  blocked four concrete gaps: split physical queues across linked worktrees,
  premature termination of unrelated entries after a failed predecessor,
  PR handoff incorrectly satisfying a dependency, and a stale generated host
  lock.
- Re-running adversarial process-level scenarios after correction proved that
  a shared lock and a shared state path are both necessary. Either one alone
  leaves a race or a split-brain queue.
- Dependency failure now isolates only the affected descendants. Independent
  entries continue, while dependents remain pending until a genuinely merged
  predecessor exists.
- The implementation and its shipped project template remained byte-identical,
  and the merge-integrator guidance documents the same fail-closed contract.
- Keeping the implementation on a dedicated branch let the separately running
  Runtime session proceed without touching its reserved files.

## Friction and Corrections

- The first PR run found `BACKLOG-BOARD.md` stale. Running the canonical board
  generator refreshed both the board and archive projection, after which the
  complete owner-governance gate passed locally and in CI.
- The next full-suite run found that the repository's exact task-set fixture
  omitted `TASKSET-AR-MERGE-QUEUE-SAFETY`. Adding the registered task set made
  the targeted test, the local full suite, and all supported Python CI jobs
  pass.
- Early lifecycle commits used the documented no-verify escape after the
  shared workspace's unrelated projections blocked the aggregate hook.
  Before integration, the branch regenerated its own projections and later
  commits passed the normal owner-governance hook.
- GitHub private-email protection required rewriting only unpublished commit
  metadata to the repository owner's noreply address. Tree equality was
  checked before the rewritten branch was pushed.
- GitHub Actions merged the green PR immediately after the final matrix job.
  W6 therefore fetched and verified the remote merge before removing the
  implementation worktree and branch.

## Durable Rules

1. Cross-worktree synchronization requires one lock namespace and one physical
   state location; sharing only the Git common lock is insufficient.
2. Independent verification should exercise competing processes and linked
   worktrees, not just mock the lock helper.
3. A dependency is satisfied only by a successful merge. A pushed branch or PR
   handoff is not equivalent to integration.
4. Queue processing should continue unrelated work after a predecessor fails,
   while preserving affected descendants as pending.
5. New task-set registration must update exact task-set fixtures and regenerate
   all derived board/archive views before the first PR CI run.
6. Merge-queue integrity prevents mechanical integration races, but it does not
   eliminate semantic or visual design drift. Host projects still need a
   design contract, declared semantic ownership, and visual regression gates.

## Evidence

- Worker verification:
  `reviews/VERIFY-2026-07-30-unit-task-ar-653-001-20260730082201.json`
- Independent W4b:
  `reviews/VERIFY-2026-07-30-task-ar-653-independent.md`
- W6 task verification:
  `reviews/VERIFY-2026-07-30-task-ar-653-20260730084810.json`
- Pull request: `#387`
- Green matrix workflow: `30500209876`
- Merge commit: `1a6854c9574ef36e439fa9059ee8b6ac8f690d8a`
