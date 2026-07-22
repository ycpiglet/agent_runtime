---
title: TASK-AR-605 Integration T3 Replan
date: 2026-07-22
signal: pass
score: 98
task_id: TASK-AR-605
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-605, github-294, integration]
---

# TASK-AR-605 Integration T3 Replan

## Bottom Line

TASK-AR-605 changed the declared session-dashboard anchors as expected. The
first implementation passed W4a and independent W4b, then the required
skeptic review found three malformed-state escape paths. Failure-first rework
closed those paths, refreshed task and unit W4a, and received independent and
skeptic APPROVE at exact HEAD
`44caea91dd6178adff057aa9b269d9dadbb847d6`. Re-anchor the accepted
implementation before creating a narrow integration claim.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Drift type | expected implementation drift | Live and template `session_dashboard.py` changed after T0 |
| Scope impact | no expansion | Dashboard pair, focused tests, host lock, task metadata, and verification records only |
| W4a | pass | Latest task and unit evidence each record 25 focused tests plus a current host lock |
| Independent W4b | APPROVE | `reviews/W4B-2026-07-22-TASK-AR-605-REWORK.md` |
| High-risk skeptic | APPROVE | `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-605-SKEPTIC-REWORK.md` |
| Required action | pass | Re-record anchors, create an integration claim, and keep it active through PR merge and main CI |

## Accepted Implementation

- Generated hosts without repository-only `work.py` obtain structured W0
  claim, worktree, and in-flight data from bounded read-only operations.
- The repository checkout retains the richer `work.status_work` path.
- Invalid UTF-8 claims, malformed count values, timeouts, process failures,
  and unexpected helper exceptions degrade to explicit notes and exit zero.
- The live and template dashboard copies are byte-identical and the host lock
  is current.

## Risk

The initial skeptic REJECT at `c9e07d4` remains preserved as historical
evidence. The rework added clean-host and injected-exception regressions for
each rejected boundary. No unresolved correctness or read-only blocker remains
at the accepted HEAD. The five-second hook slack above the 30-second serial
budget remains a documented non-blocking operational margin.

## Scope Boundary

During W4a, the existing quote-unaware frontmatter parser truncated `#294`
inside quoted metadata. That behavior is already registered as TASK-AR-608 /
GitHub issue 298 and must not be fixed under TASK-AR-605. This task uses the
equivalent `GitHub issue 294` text until TASK-AR-608 repairs the parser.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-22-task-ar-605-integration-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `scripts/session_dashboard.py`
- `src/agent_runtime/templates/project/scripts/session_dashboard.py`

## Action

Re-record the five anchors, commit the implementation/review claim transition,
and keep the integration claim active until pull-request and main CI evidence
are both green.

## Decision

Fast-forward the accepted implementation into the shared checkout, release
the implementation and generated review claims with their exact evidence,
record this T3 snapshot, and create an integration claim on the existing
branch/worktree. Push only the feature branch, merge through a pull request
that closes GitHub issue 294, verify the post-merge main workflow, then perform
W5/W6.

## Next

Create the integration claim, commit the transition metadata, fast-forward the
feature branch to that metadata commit, and open the pull request.
