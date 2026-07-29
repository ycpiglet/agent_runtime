---
type: planning
title: TASK-AR-648 Auto-review Overlay Claim P0 Replan
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-004
signal: pass
score: 98
priority: P0
tags: [planning-record, task-ar-648, t3-replan, overlay-claim, role-routing, gate-contract]
---

# TASK-AR-648 Auto-review Overlay Claim P0 Replan

## Bottom Line

The staged-only claim repair at product SHA
`5ae787d556908d923be46ebc9498bee628a3065b` passed independent W4b, but the
approved high-risk release immediately exposed a new P0 in the Runtime's own
review-routing harness. Consumer pilots remain stopped.

`role_routing.py` generated an active skeptic overlay using the canonical
`agent-runtime-task-claim/v1` schema while omitting six fields required by
`parallel_worktree_gate.py` and all persistence metadata. The gate produced
seven blocks. Releasing the synthetic review claim removed the six
active-field blocks, but the untracked released claim still produced
`task-claim:claim-not-committed`.

A second self-host probe then proved that the explicit SCM success path is
circular: `claim_guard` stages an authorized claim and invokes `git commit`,
the installed pre-commit hook runs the same gate, and the gate blocks because
the commit-in-progress claim is not yet in `HEAD`. The dispatcher returns
success with a warning, but `HEAD` remains unchanged and the three artifacts
remain staged.

These findings are not reasons to weaken the new `HEAD` durability check. The
producer and validator must share one explicit overlay contract, and the
explicit commit path needs a transaction-scoped exception that disappears as
soon as `git commit` exits.

## Exact Evidence

| Surface | Observation |
| --- | --- |
| validated product SHA | `5ae787d556908d923be46ebc9498bee628a3065b` |
| W4a lifecycle SHA | `52544a8aebbb6e11732cab62ef7fdc25bb742491` |
| independent W4b | `APPROVE`, 98/100 |
| W4b report | `reviews/W4B-2026-07-29-unit-task-ar-648-003-r2.md` |
| auto-dispatched claim | `CLAIM-REVIEW-TASK-AR-648-skeptic-closeout` |
| active-state gate | 7 block / 4 watch |
| missing active fields | `callsite_id`, `pane_id`, `phase`, `progress_pct`, `worktree_path`, `branch` |
| missing persistence | no `mode` or `scm_commit_authorized` |
| released-state gate | 1 block / 4 watch |
| skeptic verdict | `REQUEST_CHANGES`, 62/100 |
| skeptic report | `reviews/SKEPTIC-2026-07-29-task-ar-648-overlay-claim-contract.md` |
| explicit SCM hook probe | dispatcher 0, HEAD unchanged, three artifacts staged |
| explicit SCM gate finding | `task-claim:authorized-commit-not-persisted` |
| defect signatures | `defect:auto-review-overlay-claim-self-blocks-gate:a3d83ae935bfebcb`; `defect:explicit-claim-commit-self-blocked-by-precommit:d2c3c2517cc6eb7f` |

The W4b full suite remained green at `2600 passed, 3 skipped`; this P0 was
observed only when the live feature-flagged release seam generated the next
review overlay.

## Repair Contract

1. Keep orchestration overlays distinct from worker checkouts. An explicit
   `overlay: true` review/scout/council claim may omit `worktree_path` and
   `branch`; no other active claim may use that exception.
2. Every active overlay must still carry canonical identity and lifecycle
   fields: `callsite_id`, `pane_id`, `phase`, `progress_pct`, handoff/log
   pointers, and parent linkage.
3. Overlay producers must declare
   `persistence: {mode: working_tree, scm_commit_authorized: false}`. Runtime
   routing must not silently commit host artifacts.
4. Concurrent review overlays for one parent task set must explicitly set
   `allow_parallel_task_set: true`.
5. The gate must report intentional out-of-HEAD overlay persistence as a watch,
   never as a pass and never as ambiguous persistence.
6. A real high-risk dispatcher release must create auditor plus skeptic
   overlays and the immediate gate must have zero block findings.
7. `claim_guard` may pass a child-process-only transaction marker to the
   explicit `git commit`. The marker must name the exact repository and claim
   JSON paths, and the gate may honor it only when the indexed blob equals the
   current authorized `scm_commit` record.
8. Missing, malformed, mismatched, ambient, wrong-root, unstaged, or
   working-tree-mode markers must never bypass the gate. The marker must not
   survive into the caller after `git commit` exits.
9. The staged-only authorized-claim hook-failure regression must remain
   blocking. The overlay exception cannot apply to non-overlay claims or
   `scm_commit_authorized: true`.
10. A real Runtime-style pre-commit hook must allow the explicit claim-only
    commit to complete, while a later failing hook still leaves artifacts
    staged and makes the ordinary post-failure gate block.

## Lifecycle

- `UNIT-TASK-AR-648-003` remains blocked after its Runtime W4b because its
  stop condition forbids continuation after a newly observed P0.
- `UNIT-TASK-AR-648-004` owns only the overlay producer/gate contract repair
  and the subsequent fresh Bean replay.
- Write failing tests before product edits, run focused plus full W4a, and
  require a new independent W4b.
- Do not create Bean attempt 2 until that W4b approves the exact repair SHA.

## Evidence Preservation

Commit the W4b approval, skeptic `REQUEST_CHANGES`, generated review claim, and
release lifecycle traces as red operational evidence. A one-time
`--no-verify` governance commit is permitted because the defect itself makes
the pre-commit gate circular: the untracked released overlay cannot enter
`HEAD` while the gate requires it to already be in `HEAD`.

Do not amend, reset, delete, or reinterpret the evidence after the product
repair.

## Stop Boundary

Stop on a broad overlay exemption, implicit SCM commit, lost parent linkage,
duplicate task-set collision, ambient transaction bypass, staged-authorized
post-failure regression, new P0, consumer host/content mutation, credential
access, network delivery, publish, deploy, origin push, unsupported model/cost
claim, or failed independent verification.
