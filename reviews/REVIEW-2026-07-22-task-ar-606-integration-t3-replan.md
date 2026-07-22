---
title: TASK-AR-606 Integration T3 Replan
date: 2026-07-22
signal: pass
score: 99
task_id: TASK-AR-606
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-606, github-295, integration]
---

# TASK-AR-606 Integration T3 Replan

## Bottom Line

TASK-AR-606 changed the declared hook activation anchors as planned. Initial
W4a and independent W4b passed, but the required skeptic review found linked
ancestor, multi-link, TOCTOU, and false-success installer boundaries. The
first rework closed those paths; independent and skeptic rechecks then found
one remaining FIFO blocking case. Failure-first rework added nonblocking
special-file handling. Final task/unit W4a and both independent review roles
now APPROVE the accepted implementation.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Drift type | expected implementation drift | Hook modes, installer/bootstrap logic, focused tests, and generated lock changed after T0 |
| Scope impact | no expansion | Executable activation only; no hook body or additional hook changed |
| Final W4a | pass | Task and unit each record `24 passed, 2 skipped`, a current lock, and two `100755` modes |
| Independent W4b | APPROVE | `reviews/W4B-2026-07-22-TASK-AR-606-REWORK2.md` |
| Skeptic review | APPROVE | `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC-REWORK2.md` |
| Required action | pass | Re-record anchors and keep an integration claim through PR merge and post-merge main CI |

## Accepted Implementation

- Both tracked pre-commit hooks use mode `100755` while preserving their
  original blob IDs and command bodies.
- POSIX repair opens a real `.githooks` directory and final hook with
  `O_NOFOLLOW`, requires single-link regular files, validates and changes the
  same descriptor, and uses `O_NONBLOCK` before rejecting special files.
- A missing, linked, non-regular, multi-link, or unrepairable POSIX hook
  returns installer failure before `core.hooksPath` is configured.
- Windows skips POSIX mode operations. Bootstrap remains watch-only and
  reports `FIX` without blocking when activation cannot be repaired.

## Preserved Review History

- The initial independent APPROVE and skeptic REJECT remain recorded.
- The first rework independent/skeptic REJECT reports preserve the FIFO gap.
- Final REWORK2 reports both APPROVE exact implementation HEAD
  `92a07e583c96c2fa79ee651eb1ed7fab60a659b1`.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-22-task-ar-606-integration-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `scripts/lock_merge_driver.py`
- `src/agent_runtime/templates/project/scripts/lock_merge_driver.py`
- `scripts/bootstrap_dev_env.py`
- `.githooks/pre-commit`
- `src/agent_runtime/templates/project/.githooks/pre-commit`

## Decision

Release the implementation and generated review claims with the final REWORK2
evidence, refresh the taskset assumptions, create an integration claim on the
existing branch/worktree, and open a pull request that closes GitHub issue
295. Merge only after the Linux-backed CI matrix validates the native POSIX
chmod, actual Git hook execution, FIFO timeout regression, and the full
package suite. Then verify main CI before W5/W6 closeout.
