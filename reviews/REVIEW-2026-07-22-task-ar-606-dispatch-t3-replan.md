---
title: TASK-AR-606 Dispatch T3 Replan
date: 2026-07-22
signal: pass
score: 96
task_id: TASK-AR-606
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-606, github-295, git-hooks]
---

# TASK-AR-606 Dispatch T3 Replan

## Bottom Line

TASK-AR-605 is fully closed and the next registered unit is TASK-AR-606 for
GitHub issue 295. T2 currently passes, but this unit changes the executable
activation contract for repository and generated-host hooks. Refresh the
taskset snapshot with the exact installer and hook anchors before dispatch.
The registered scope and stop boundary remain unchanged.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| W0 | pass | Active claims 0, one clean main worktree, no divergent task branches |
| Prior task | complete | TASK-AR-605 implementation and W6 PRs merged; main CI run `29927077404` passed on rerun attempt 2 |
| Worker readiness | pass | `UNIT-TASK-AR-606-001` declares exact targets, acceptance, verification, handoff, and stop boundary |
| T2 before refresh | pass | `plan_assumption_gate --check` reported zero findings |
| Scope drift | none | Repair executable permission only; do not change hook bodies or enable additional hooks |
| Required action | pass | Re-anchor the hook/install surfaces and create the claim before any implementation worktree |

## Decision

Track both pre-commit hooks as executable and make the existing installation
paths idempotently restore POSIX execute permission when archives or checkout
transport lose it. Windows must skip POSIX permission repair without failing.
The hook command bodies and governance policy remain byte-for-byte unchanged.

## Frontmatter Safety

TASK-AR-608 / GitHub issue 298 already owns the quote-unaware frontmatter
parser defect. Until that task lands, task metadata uses `GitHub issue 295`
instead of `GitHub #295`; prose headings remain unchanged and no parser fix is
included here.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-22-task-ar-606-dispatch-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `scripts/lock_merge_driver.py`
- `src/agent_runtime/templates/project/scripts/lock_merge_driver.py`
- `scripts/bootstrap_dev_env.py`
- `.githooks/pre-commit`
- `src/agent_runtime/templates/project/.githooks/pre-commit`

## Verification Boundary

- Add failure-first mode and installer-repair regressions.
- Run `python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q`.
- Confirm the generated-host lock is current.
- Confirm both index entries report mode `100755`.
- Require independent W4b plus an adversarial cross-platform review before integration.
