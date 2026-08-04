---
title: TASK-AR-648 Bean Attempt-2 T3 Replan
date: 2026-07-29
status: active
signal: pass
score: 98
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-006
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [replan, plan-assumptions, bean-wiki, claim-integrity, green-replay]
---

# TASK-AR-648 Bean Attempt-2 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-648-006`, but refresh the taskset assumptions before
claim creation. The T2 dispatch gate correctly stopped the first attempt
because UNIT-005 changed all three claim-publication enforcement surfaces that
the previous snapshot pinned. Those changes are the independently approved
prerequisite for this replay, not unrelated drift.

## T2 Finding

| Anchor | Previous SHA-256 | Current SHA-256 | Decision |
| --- | --- | --- | --- |
| `scripts/task_claim_dispatcher.py` | `88b10afeef39717c3c57298f05419dbc7fbff30f16d65b45004ced31000cbaef` | `a4ae2185c2cce2abdb27e1444f0b190f821d11faa7543a498fd0bf988fa8d37e` | accept approved UNIT-005 product |
| `scripts/claim_guard.py` | `9419e5a89f211cf388c05137b925fa44ed8e373bbd5ab325cf2b390731a33aa3` | `8b1ebc3e11b2d4975bfb1fd8501350ec7ed41e500cb39c7fae64e4fb22533111` | accept approved UNIT-005 product |
| `scripts/parallel_worktree_gate.py` | `d727a62f9a16477709eb703dd1b8ddf4cc10d3a5c3e2a567dd528a831c924b28` | `52a5e0b544a5b4ee1a4f8d9468048e776dd683c5868c051f5e0951fe1219e38b` | accept approved UNIT-005 product |
| `scripts/work.py` | `55b952a8ebe376962d9cc0f28b1242e493365e7b557b25c5fe5c5228d0981dae` | `55b952a8ebe376962d9cc0f28b1242e493365e7b557b25c5fe5c5228d0981dae` | retain unchanged registration anchor |

The first claim command exited nonzero before writing a claim. No bypass flag
was used.

## Revalidated Product

- Exact product commit:
  `6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39`.
- Canonical W4a: focused claim/gate/dispatcher `154 passed`, routing
  `49 passed`, full suite `2644 passed, 3 skipped`.
- Independent W4b: `APPROVE`, 97/100, focused `203 passed`, the same full-suite
  result, and no P0/P1.
- Product surfaces and templates have no delta from the exact product commit to
  this lifecycle commit; later commits contain records only.
- Default claim persistence remains `working_tree`. Explicit SCM publication is
  outside the Bean pilot and consumer commits remain forbidden.

## Decision

Replace the previous taskset assumption snapshot with this T3 record and the
same four executable anchors. Then rerun T2 and create only the registered
UNIT-006 claim. The original Bean baseline, failed attempt 1, Allimbot, and
release boundaries do not change.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-29-task-ar-648-bean-attempt-2-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `scripts/claim_guard.py`
- `scripts/parallel_worktree_gate.py`

## Stop Boundary

Stop if T2 still reports drift, claim creation moves Runtime or Bean `HEAD`,
claim persistence is not `working_tree`, or any P0/P1, host/content mutation,
consumer commit, external effect, Allimbot action, or release action appears.
