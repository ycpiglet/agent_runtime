---
type: planning
title: TASK-AR-648 Actual Worktree HEAD Reflog P1 Replan
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-005
signal: fail
score: 74
priority: P1
tags: [planning-record, task-ar-648, t3-replan, claim-transaction, reflog, linked-worktree]
---

# TASK-AR-648 Actual Worktree HEAD Reflog P1 Replan

## Bottom Line

Independent W4b rejected product SHA
`4c50297416fe4a72673bcf43378e0614c955f0a1`: the protected private-context
CAS advances the branch reflog but omits the actual worktree `HEAD` reflog.
The claim survives, but recovery and audit behavior differs from a native
commit. Bean Wiki attempt 2 and Allimbot therefore remain stopped.

The prior W4a R3 evidence remains immutable historical evidence for that exact
product. It does not authorize a consumer pilot.

## Pinned Failure

| Item | Value |
| --- | --- |
| Rejected product | `4c50297416fe4a72673bcf43378e0614c955f0a1` |
| Independent report | `reviews/W4B-2026-07-29-unit-task-ar-648-005.md` |
| W4b result | `REQUEST_CHANGES`, P1, 74/100 |
| Observed branch reflog | contains the claim commit |
| Observed actual `HEAD` reflog | unchanged at the starting commit |
| Defect signature | `defect:claim-transaction-omits-actual-worktree-head-ref:1d5e935f7b8caef4` |

## Classification

The missing entry does not corrupt the committed tree or move the wrong ref,
so it is not another P0 integrity bypass. It is nevertheless release-blocking:
this code path exists specifically for crash-safe claim recovery and must not
silently remove the normal worktree-local recovery trail, especially in a
linked worktree where `logs/HEAD` belongs to the worktree-specific Git
directory.

## Required Repair Contract

1. Preserve the real worktree-specific `HEAD.lock` exclusion used to prevent
   equal-OID symbolic branch switching.
2. Publish the sealed commit with an old-OID compare-and-swap against the
   originally authorized symbolic branch.
3. Create exactly one actual worktree `HEAD` reflog transition from the
   starting commit to the sealed commit with the same claim action as the
   branch reflog.
4. Keep the `HEAD` reflog publication inside the owned lock and before
   Runtime-invoked `post-commit`; do not append an unguarded record after the
   protected boundary.
5. Use the linked worktree's own Git administrative directory for
   `logs/HEAD`, while the branch ref and branch reflog remain in the common Git
   directory.
6. Fail closed before reporting success if the protected reflog operation
   cannot be completed or verified. Cleanup must never remove or rewrite an
   externally owned lock or unrelated reflog entry.
7. Preserve Git 2.34 behavior and document any platform limitation rather
   than silently claiming portability.

## Failure-First Tests

- Normal worktree: compare native commit behavior with the explicit claim
  transaction and require both branch and actual `HEAD` reflogs to advance
  exactly once to the returned commit.
- Linked worktree with `extensions.worktreeConfig=true`: require the linked
  worktree `logs/HEAD` to advance and the primary worktree `logs/HEAD` to
  remain unchanged.
- Existing equal-OID symbolic-switch, Runtime `post-commit`, external
  `HEAD.lock`, direct ref CAS loss, Git-environment poisoning, cleanup, and
  real-index preservation tests remain green.
- Add a deterministic failure injection around reflog publication and prove
  the function cannot return `ok: true` without a verified actual `HEAD`
  reflog transition.

## Verification Reset

- UNIT-005 returns to `verification_status: pending`.
- Preserve W4a R3 and this W4b as historical evidence.
- Produce a new product SHA, distinct W4a R4 machine evidence/report, and a
  fresh independent W4b.
- Only an approval of that exact product SHA may unlock Bean attempt 2.

## Stop Boundary

Stop on a post-hoc unguarded reflog append, synthetic entry outside the
publication lock, loss of branch CAS, mutation of another worktree's
`logs/HEAD`, external-lock removal, evidence rewrite, consumer worktree
creation, release, publish, deploy, push, credential access, or network
delivery.
