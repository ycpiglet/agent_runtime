---
type: planning
title: TASK-AR-648 Post-Commit HEAD Race P0 Replan
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-005
signal: fail
score: 38
priority: P0
tags: [planning-record, task-ar-648, t3-replan, claim-transaction, post-commit, symbolic-head]
---

# TASK-AR-648 Post-Commit HEAD Race P0 Replan

## Bottom Line

W4a R2 machine verification passed product SHA
`14652f4a9623817b90b3e4f4b3ac4c28bb57fe0b`, but pre-report adversarial
self-review found that the guard released the real worktree `HEAD.lock` before
running the Runtime-invoked `post-commit` hook. A hook could switch symbolic
`HEAD` to an equal-OID sibling branch, return success, and make the guard
return `ok: true` while current `HEAD` did not contain the published claim.

The passing machine evidence remains immutable historical evidence for the
superseded product SHA. It does not authorize independent W4b, Bean Wiki, or
Allimbot.

## Pinned RED-R3 Evidence

| Item | Value |
| --- | --- |
| Superseded product SHA | `14652f4a9623817b90b3e4f4b3ac4c28bb57fe0b` |
| Historical verification | `reviews/VERIFY-2026-07-29-unit-task-ar-648-005-20260729213242.json` |
| Historical result | `2633 passed, 3 skipped`; missing the post-hook sequence |
| Reproducer | `test_post_commit_hook_cannot_switch_symbolic_head_after_publication` |
| RED result | `1 failed`; post hook switched branches and no warning was reported |
| Defect signature | `defect:claim-post-commit-symbolic-head-race:d12d0dfbbb046fc1` |

## Classification

This is not the unavoidable race after a function returns. Agent Runtime
itself invokes the hook inside the claim transaction and therefore owns its
ordering. Releasing the publication lock before that call opened a deterministic
internal gap in the promised success state.

## Selected Repair

Keep `post-commit` after the branch compare-and-swap, matching its
post-publication meaning, but execute it while the already-owned real
worktree-specific `HEAD.lock` remains held. A compliant Git symbolic switch
inside the hook then fails. Hook failure remains a non-rollback warning because
the sealed commit is already published. Release the owned lock immediately
after the hook, using the existing device/inode ownership token.

Rejected alternatives:

- rechecking after the hook detects the invalid state only after the hook has
  already switched the worktree;
- switching the branch back would overwrite an intentional concurrent action;
- skipping `post-commit` would silently change the documented hook lifecycle;
- treating a Runtime-invoked hook as an external race would make the API's
  success result misleading.

## Required Regression

- Configure a real executable `post-commit` hook that runs
  `git symbolic-ref HEAD refs/heads/concurrent-branch`.
- The hook executes once, its switch fails because the actual per-worktree
  lock exists, and the result exposes a post-hook warning.
- The guard returns success only with the original symbolic ref still pointing
  to the sealed claim commit.
- Existing pre/prepare/commit-msg behavior, linked-worktree coverage, direct
  ref CAS loss, environment sanitization, private cleanup, real-index
  preservation, and reset-plus-clean survival remain green.

## Verification Reset

- UNIT-005 returns to `verification_status: pending` and phase `red-r3`.
- Preserve both prior W4a histories without rewriting them.
- Produce new machine evidence and a distinct W4a R3 report at one exact
  product SHA, then obtain a fresh independent W4b.

## Stop Boundary

Stop on post-hoc ref rollback, hook omission, an unowned lock removal, success
with symbolic HEAD off the claim commit, product evidence rewrite, consumer
worktree creation, release, publish, deploy, push, credential access, network
delivery, or any new P0.
