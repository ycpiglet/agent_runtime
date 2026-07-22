---
title: TASK-AR-604 Integration T3 Replan
date: 2026-07-22
signal: pass
score: 97
task_id: TASK-AR-604
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-604, github-293, integration]
---

# TASK-AR-604 Integration T3 Replan

## Bottom Line

TASK-AR-604 changed the two declared taskset-dispatcher anchors as expected,
then passed W4a, independent W4b, and the required skeptic review at exact
HEAD `efefcd785fb446a480fe910e76d445ef162531a6`. Re-anchor the accepted
implementation before creating a narrow integration-phase claim. No scope
expansion or `--skip-plan-check` escape is required.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Drift type | expected implementation drift | Live and template `taskset_dispatcher.py` changed after T0 |
| Scope impact | no expansion | Only start-status persistence, focused tests, template parity, host lock, and verification records changed |
| W4a | pass | Latest task and unit evidence each record 82 focused tests plus a current host lock |
| Independent W4b | APPROVE | `reviews/W4B-2026-07-22-TASK-AR-604.md` |
| High-risk skeptic | APPROVE | `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC.md` |
| Required action | pass | Re-record anchors, create an integration claim, and keep it active through PR merge and main CI |

## Accepted Implementation

- Localized start states use the existing record vocabulary and persist
  `진행 중`.
- English start states continue to persist `in_progress`.
- The emitted machine payload remains normalized as `in_progress`.
- Completed, blocked, hold, and review-family states remain no-write paths.
- Root and generated-host dispatcher copies are byte-identical and the host
  lock is current.

## Scope Boundary And Residual Intake

The skeptic review also confirmed a pre-existing eligibility defect:
`closed`/`released` and their Korean aliases are treated as startable. That
behavior predates TASK-AR-604 and is outside this unit's explicit boundary
against redesigning the global state machine. It is non-blocking for GitHub
#293, must not be folded into this integration, and requires a separate intake
record and worker-ready unit before implementation.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-22-task-ar-604-integration-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `scripts/taskset_dispatcher.py`
- `src/agent_runtime/templates/project/scripts/taskset_dispatcher.py`

## Integration Decision

Fast-forward the accepted implementation into the shared checkout, release
the implementation and generated review claims with their exact evidence,
record this T3 snapshot, and create an integration claim on the existing
branch/worktree. Push only the feature branch, merge through a pull request
that closes #293, verify the post-merge main workflow, then perform W5/W6.

