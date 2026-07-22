---
type: plan-revalidation
title: Post-Merge Plan Revalidation
date: 2026-07-22
project_id: PROJECT-AGENT-RUNTIME
task_set_ids:
  - TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
  - TASKSET-AR-AUTO-MERGE-INTEGRITY
status: approved
owner: lead-engineer
signal: pass
score: 97
---

# Post-merge plan revalidation

## Bottom Line

Both active tasksets remain valid after the remote merge, provided their
assumptions are refreshed against the merged dispatch contracts before the
next claim is created.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Identity collision | pass | published `TASK-AR-600`; local release `TASK-AR-602` |
| Dispatch compatibility | pass | strict frontmatter plus legacy body fallback |
| Focused regression suite | pass | 161 tests passed |

## Trigger

Merging `origin/main` introduced the auto-merge integrity taskset and changed
the shared claim and taskset dispatch contracts. The T2 assumption gate then
reported hash drift for both active tasksets. The merge also exposed a human
task-ID collision, which was resolved by preserving the published remote
`TASK-AR-600` record and renaming the unstarted release record to
`TASK-AR-602`.

## Revalidation decision

- Keep the July intake task order and scope unchanged, with `TASK-AR-599`
  followed by release task `TASK-AR-602`.
- Keep the remote auto-merge integrity task as `TASK-AR-600`; its execution
  remains independent and must satisfy its recorded read-back acceptance
  criteria before release readiness can be claimed.
- Accept the merged taskset dispatcher contract: explicit frontmatter `tasks:`
  is strict and canonical; legacy body-only task order remains advisory and
  backward compatible.
- Re-anchor both tasksets against the merged dispatch implementation and their
  applicable design records before creating another claim.

## Decision

Approve the merged plan and task ordering without scope expansion. A successful
T2 check is mandatory for every subsequent claim.

## Action Board

| Taskset | Required action | Status |
| --- | --- | --- |
| `TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT` | refresh dispatch anchors | approved |
| `TASKSET-AR-AUTO-MERGE-INTEGRITY` | refresh dispatch and target-file anchors | approved |
| Both | rerun T2 before claim creation | required |

## Evidence reviewed

- `reviews/REVIEW-2026-07-22-remote-main-integration-id-collision.md`
- `reviews/REVIEW-2026-07-19-taskset-ar-july-upstream-intake-closeout-registration.md`
- `reviews/REVIEW-2026-07-19-auto-merge-execution-readback.md`
- `scripts/task_claim_dispatcher.py`
- `scripts/taskset_dispatcher.py`
- `scripts/work.py`
- Focused merge verification: 161 tests passed.

## Scope boundary

This review revalidates dispatch assumptions only. It does not close either
taskset, implement `TASK-AR-599` or `TASK-AR-600`, or declare v0.7.0 ready.

## Risks / Blockers

- Any new anchor drift blocks dispatch and requires another recorded replan.
- The absent regression target for `TASK-AR-600` is intentionally anchored as
  absent until its claimed unit creates it.

## Next

- Refresh both assumption sets after this document is finalized.
- Commit and push the reconciled baseline before starting another claim.
