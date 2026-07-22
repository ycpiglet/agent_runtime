---
title: TASK-AR-603 Unicode Token Boundary T3 Replan
date: 2026-07-22
signal: pass
score: 95
task_id: TASK-AR-603
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-603, github-299, unicode-boundary]
---

# TASK-AR-603 Unicode Token Boundary T3 Replan

## Bottom Line

The first TASK-AR-603 implementation unified the producer and consumers and
passed W4a plus independent W4b, but the required high-risk skeptic review
found that the ASCII-only token boundary still extracts canonical-looking IDs
from inside Unicode words such as `작업TASK-AR-1` and `αTASK-1β`. This is a
blocking false-positive path for conversation audit and taskset parsing.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Drift type | expected implementation plus review-driven rework | Shared producer/consumer scripts changed after T0 |
| Blocking evidence | confirmed | `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-603-SKEPTIC-BLOCK.md` |
| Scope impact | no expansion | Shared contract, mirrored template, focused tests, host lock, and verification evidence remain the boundary |
| Compatibility requirement | unchanged | Preserve numeric `TASK-N`, numeric `TASK-AR-N`, timestamp `TASK-AR-*`, and suffix case |
| Required action | pass | Re-anchor at T3, reopen the claim, add Unicode boundary regressions, then repeat W4a/W4b and skeptic review |

## Decision

Reopen TASK-AR-603 without `--skip-plan-check`. Replace the ASCII adjacency
class with a Unicode-aware word boundary that also continues to reject hyphen
adjacency. Add regression coverage for accented Latin, Korean, and Greek word
characters on both sides of IDs. Do not change the accepted value grammar or
expand into unrelated task parsing behavior.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-22-task-ar-603-unicode-boundary-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `scripts/task_id_contract.py`
- `scripts/task_identity.py`
- `scripts/taskset_dispatcher.py`
- `scripts/conversation_work_audit.py`
- `src/agent_runtime/templates/project/scripts/task_id_contract.py`
- `src/agent_runtime/templates/project/scripts/task_identity.py`
- `src/agent_runtime/templates/project/scripts/taskset_dispatcher.py`
- `src/agent_runtime/templates/project/scripts/conversation_work_audit.py`

## Acceptance And Verification

- The extractor returns no task ID for `éTASK-AR-1`, `TASK-AR-1é`,
  `작업TASK-AR-1`, `TASK-AR-1작업`, or `αTASK-1β`.
- Existing accepted values and lowercase/uppercase timestamp suffixes are
  unchanged.
- Root and generated-host template contract copies remain identical.
- The declared focused suite, host-lock check, W4a, independent W4b, and
  skeptic review all pass again on the final exact HEAD.

## Next

- Record this T3 snapshot and confirm `plan_assumption_gate --check` passes.
- Create a new TASK-AR-603 rework claim pointing at the existing worktree and
  branch.
- Implement only the Unicode token-boundary correction and its regressions.

## Integration Re-anchor

The Unicode correction subsequently passed refreshed W4a, independent W4b,
and skeptic recheck at the final evidence HEAD. Re-record the same declared
anchors at that accepted state and keep a narrow integration-phase claim on
the existing worktree until the PR merges and main CI succeeds. This preserves
claim-first worktree continuity without expanding implementation scope or
using `--skip-plan-check`.
