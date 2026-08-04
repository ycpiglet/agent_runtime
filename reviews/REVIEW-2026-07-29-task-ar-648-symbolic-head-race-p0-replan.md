---
type: planning
title: TASK-AR-648 Symbolic HEAD Race P0 Replan
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-005
signal: fail
score: 35
priority: P0
tags: [planning-record, task-ar-648, t3-replan, claim-transaction, symbolic-head, race]
---

# TASK-AR-648 Symbolic HEAD Race P0 Replan

## Bottom Line

Root self-review after the first W4a found a release-blocking race in the
explicit claim transaction at product SHA
`e8d25d087d4936acfd445de22342d0cec3f11dc0`. The code validates the symbolic
branch and later compare-and-swaps that branch ref, but another Git process
can switch the worktree `HEAD` to a different branch at the same old object ID
between those operations. The original branch advances, the API reports
success, and the worktree's symbolic `HEAD` does not contain the claim commit.

The first W4a report and machine evidence remain immutable history for that
product SHA, but no longer authorize a release or consumer replay. Bean Wiki
attempt 2 and Allimbot remain stopped.

## Pinned RED-R2 Evidence

| Item | Value |
| --- | --- |
| Superseded product SHA | `e8d25d087d4936acfd445de22342d0cec3f11dc0` |
| Historical W4a | `reviews/W4A-2026-07-29-unit-task-ar-648-005.md` |
| Historical lifecycle SHA | `4cd7d1d9a01893728e39a69a8b6759e89c5064ef` |
| Reproducer | `test_explicit_claim_transaction_keeps_symbolic_head_on_sealed_branch` |
| RED result | `1 failed`; concurrent `git symbolic-ref` returned `0` and moved `HEAD` |
| Defect signature | `defect:claim-commit-symbolic-head-race:f2860072798c6ac5` |

## Integrity Invariant

Success means all three facts hold at one indivisible publication boundary:

1. the real worktree still has symbolic `HEAD` at the originally sealed ref;
2. that ref still points to the starting commit;
3. one compare-and-swap advances that ref to the sealed commit.

A successful update of a branch that is no longer the worktree's symbolic
`HEAD` is failure, even when both branches shared the same old object ID.

## Options Considered

| Option | Decision | Reason |
| --- | --- | --- |
| Recheck symbolic `HEAD` immediately before `update-ref` | rejected | Leaves the same check/use window. |
| Update `HEAD` and branch together with `update-ref --stdin` | rejected | Symbolic `HEAD` aliases the branch and produces duplicate-ref semantics; it does not prevent a concurrent symbolic target change. |
| Hold the real worktree `HEAD.lock` and call ordinary `update-ref` | rejected alone | Git also needs that lock to maintain the checked-out HEAD reflog, so the legitimate update fails. |
| Hold real `HEAD.lock`, update the branch from an isolated detached Git administrative context | selected | Compliant Git branch switching is excluded while Git's own CAS/ref-lock machinery updates the common branch ref without contending for the real worktree HEAD lock. |
| Write loose refs directly | rejected | Bypasses Git's packed-ref, reflog, and compare-and-swap machinery. |

## Repair Boundary

Continue `UNIT-TASK-AR-648-005`; do not create a new consumer or release unit.

1. Create the sealed commit before entering the short publication critical
   section.
2. Create a private mode-`0700` Git administrative directory with detached
   `HEAD` at the starting object and an exact `commondir` link to the real
   common Git directory.
3. Acquire the real worktree-specific `HEAD.lock` with exclusive creation.
4. Revalidate the real symbolic target, ref object, transaction record,
   private index/tree, artifact blobs, and commit message under that lock.
5. Run `git update-ref <original-ref> <new> <old>` with the isolated
   administrative context, preserving Git's ref CAS and ref locking.
6. Release only the lock created by this process and remove every private
   transaction artifact on success and failure.

The critical section excludes hook execution and commit signing so an
ordinary worktree operation is blocked only for final publication.

## Required Regressions

- An equal-OID concurrent `git symbolic-ref` attempt cannot switch `HEAD`.
- A pre-existing external `HEAD.lock` fails closed and is never removed.
- A direct competing branch-ref writer still makes the Git CAS lose.
- The isolated administrative context is removed on success and every
  failure path.
- Detached HEAD, sealed-tree checks, real-index preservation, hook lifecycle,
  reset-plus-clean survival, root/template parity, and ordinary gate behavior
  remain green.

## Verification Reset

- UNIT-005 returns to `verification_status: pending` and phase `red-r2`.
- The first W4a remains unchanged and is superseded only for release use.
- Produce a distinct W4a R2 report and machine evidence at one exact new
  product SHA.
- Require a fresh independent W4b against that SHA before Bean Wiki attempt 2.

## Stop Boundary

Stop on manual ref-file mutation, removal of a lock not owned by this
transaction, success with a changed symbolic `HEAD`, private Git-context leak,
real-index mutation, hook bypass, evidence rewrite, consumer worktree
creation, release, publish, deploy, push, credential access, network delivery,
or any new P0.
