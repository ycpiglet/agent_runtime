---
title: TASK-AR-648 Bean Wiki Attempt 5 Registration
date: 2026-07-30
status: active
signal: pass
score: 99
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-014
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, bean-wiki, pilot, isolation, model-economy]
---

# TASK-AR-648 Bean Wiki Attempt 5 Registration

## Bottom Line

Register one fifth Bean replay only after exact Runtime product
`34427e1fe18d6c4db8a81142616ccad24cc6e7de` passed W4a and fresh independent
W4b. This unit authorizes writes only in a new disposable Bean checkout.
Allimbot and every release surface remain blocked.

## Registration Path

`work.py new` cannot append one unit beneath the already-canonical
TASK-AR-648 without also attempting to recreate its existing parent graph.
The established existing-task procedure is therefore used: add one canonical
unit spec, refresh generated views, record T0/T3 assumptions explicitly, and
run readiness plus canonical selection. No plan-check bypass is permitted.

## Isolation Decision

Attempt 5 gets a newly created frozen control at the same Bean commit. The
roles are:

| Checkout | Role | Decision |
| --- | --- | --- |
| New attempt 5 | `disposable_target` | The only authorized write root |
| New control 5 | `frozen_control` | Any snapshot change blocks |
| Live Bean primary | `live_observation` | External drift is watch-only; pilot targeting blocks |
| Attempts 1–4 | historical evidence | Never written and not reused as the fresh oracle |

All before-snapshots are captured after worktree creation and before the first
target write. Roots must be canonical, pairwise disjoint, and non-nested.

## Model-Economy Decision

The Runtime claim starts from `worker_standard` because it coordinates a
cross-repository fifth replay with data-integrity stop conditions. Inside Bean,
deterministic adoption and restart/Scribe use `worker_low`; only the single
editorial judgment task uses a selectively invoked `worker_standard`
specialist. Provider execution, usage, token, cost, and savings claims stay
unavailable unless directly observed.

## Promotion Rule

The attempt becomes green only when its exact evidence passes causal isolation,
host/content preservation, taskset completion, installed Owner governance,
Runtime pilot acceptance, W4a, and fresh independent W4b with no P0/P1.
Otherwise this unit closes blocked and no consumer-side repair is allowed.

## Exclusions

- No Bean primary, prior attempt, frozen-control, Autofolio, or Allimbot write
- No content or generated content-index edit
- No dependency install, provider-live call, credential access, or network use
- No consumer commit, release, version, tag, package, push, publish, or deploy
