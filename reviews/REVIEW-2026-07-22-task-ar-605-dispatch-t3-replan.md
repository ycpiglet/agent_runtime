---
title: TASK-AR-605 Dispatch T3 Replan
date: 2026-07-22
signal: pass
score: 96
task_id: TASK-AR-605
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-605, github-294, session-dashboard]
---

# TASK-AR-605 Dispatch T3 Replan

## Bottom Line

TASK-AR-604 is fully closed and the next registered unit is TASK-AR-605 for
GitHub #294. The taskset-wide plan snapshot was narrowed during prior task
integration, so refresh it before dispatch with the session-dashboard pair
that this unit actually changes. The task goal and scope remain unchanged.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| W0 | pass | Active claims 0, one clean main worktree, no divergent task branches |
| Prior task | complete | PR #307 and W6 PR #308 merged; both post-merge main workflows passed |
| Worker readiness | pass | `UNIT-TASK-AR-605-001` contains exact scope, targets, acceptance, verification, and stop boundary |
| Scope drift | none | Continue the registered clean-template read-only fallback; do not ship repository-only `work.py` |
| Required action | pass | Re-anchor the dashboard pair and create the claim before a worktree |

## Decision

Implement a bounded read-only fallback inside the live/template
`session_dashboard.py` copies. Preserve the richer repository path when
`work.py` is importable. A clean generated host must return structured W0
output rather than `ModuleNotFoundError`, and fallback diagnostics must remain
non-mutating and explicit.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-22-task-ar-605-dispatch-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `scripts/session_dashboard.py`
- `src/agent_runtime/templates/project/scripts/session_dashboard.py`

## Verification Boundary

- Add a failure-first clean-template execution regression.
- Run `python -m pytest tests/test_session_dashboard.py -q`.
- Confirm live/template parity and a current generated-host lock.
- Repeat W4a, independent W4b, and high-risk skeptic review before PR
  integration.

