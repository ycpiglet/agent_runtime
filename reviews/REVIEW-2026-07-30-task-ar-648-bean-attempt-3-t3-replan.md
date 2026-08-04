---
title: TASK-AR-648 Bean Attempt-3 T3 Replan
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-009
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
signal: pass
score: 99
priority: P0
status: approved
tags: [task-ar-648, t3-replan, bean-wiki, green-replay, portable-continuity]
---

# TASK-AR-648 Bean Attempt-3 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-648-009` as the only runnable TASK-AR-648 unit
after replacing the portable-continuity implementation snapshot with this
post-verification consumer-replay snapshot.

This review authorizes registration, read-only planning, a default
working-tree Runtime claim, and then one new Bean attempt-3 worktree. It does
not authorize mutation of Bean primary or earlier attempts, Allimbot work,
provider-live execution, or any release action.

## Signal

Pass. All 14 drift findings are explained by the approved UNIT-008 product and
lifecycle, and the proposed successor has a complete worker-ready contract.

## T2 Drift Disposition

The previous snapshot fails on exactly 14 anchors. Twelve are the approved
portable-continuity product and regression surfaces:

- root and packaged `task_claim_dispatcher.py`;
- root and packaged `parallel_worktree_gate.py`;
- `src/agent_runtime/doctor.py`;
- packaged `check_agent_docs.py` and standby pointer;
- parallel, claim, doctor, and template-smoke tests; and
- the host lock fixture.

The remaining two are the canonical TASK-AR-648 record and completed
UNIT-008 lifecycle evidence. These changes are fully explained by product
`b82042eba58f1e06e1e73130a189cb72245462a0`, W4a, independent W4b, canonical
verification, claim release, and unit close. They are not unexplained drift.

## Revalidated Product

- Product: `b82042eba58f1e06e1e73130a189cb72245462a0`
- Product tree: `3b63e0c920a47bf89a5f4bb6e4c84d7f1f20f239`
- Template tree: `d61713bc4066d4ea549efcc7826da10929e64e94`
- Lifecycle close: `da15ddf6c9e06c89368b3ccc53c4fca603165b1b`
- W4a: focused `294`, routing `49`, assets `36`, full
  `2678 passed, 3 skipped`
- Independent W4b: `APPROVE`, 99/100, no P0/P1
- Canonical verification: six of six commands passed on the same product
- Product and pilot-validator delta from `b82042eb` to lifecycle close: zero

## Dispatch Decision

Re-anchor the taskset to the current selector, claim, readiness, continuity,
doctor, standby pointer, pilot acceptance, lock, task, unit, W4b, and
verification surfaces. Then require:

1. plan assumptions pass without a bypass;
2. unit readiness passes for UNIT-009;
3. the read-only taskset plan selects UNIT-009 and no historical sibling;
4. Runtime claim creation leaves Runtime HEAD unchanged;
5. Bean attempt 3 is not created until all four conditions pass.

The Runtime unit requests `worker_standard`. `data_integrity` and
`repeated_failure` remain explicit escalation signals, but a configured route
is not evidence of an observed provider model or cost.

## Gate Matrix

| Gate | Required result |
| --- | --- |
| Plan assumptions | Current T3 anchors pass without bypass |
| Unit readiness | UNIT-009 is worker-ready with zero findings |
| Taskset selector | UNIT-009 is the only selected runnable unit |
| Runtime claim | Default `working_tree`; Runtime HEAD unchanged |
| Consumer creation | Only after all preceding gates pass |
| Allimbot | Remains stopped until Bean W4b approves |

## Action

Replace the previous snapshot with the anchors named by this review, run
readiness and plan again, and create the Runtime claim only if both pass.

## Decision

Advance to one fresh Bean attempt 3 after claim creation. Do not reopen
UNIT-006 or reuse either failed green worktree.

## Bean Boundary

Attempt 3 must start at
`357eee4fd8c29c33a949adbe3a0ffa80c874bf42` on a new path and branch. Apply
the exact `core+web-content` product, run three offline traces, and treat
`bean-wiki-editorial-ops` as the editorial authority. The specialist review is
read-only. Content validation may use already-present local tooling only;
dependency installation and network access are forbidden.

## Risk

Attempt 3 crosses a repository boundary and exercises a previously failing
bootstrap seam. A wrong selector, stale pointer, changed source tree, or
content delta is therefore release-blocking even if later checks appear green.

## Stop Boundary

Stop on plan drift, a selector other than UNIT-009, an SCM-persisted default
claim, provenance ambiguity, any P0/P1, host/content mutation, dependency
installation, external effect, Allimbot action, release, version, tag,
package, push, publish, deploy, credential access, or network delivery.

## Next

Record the T3 snapshot, verify UNIT-009 selection and no-commit claim
persistence, then capture immutable Bean baselines before worktree creation.
