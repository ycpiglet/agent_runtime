---
type: review
id: REVIEW-2026-06-10-agent-runtime-task-ar-216-duplicate-claim-release
audience: owner
status: pass
signal: pass
score: 95
priority: High
tags: [release-steward, task-ar-216, dispatcher, duplicate-claim]
updated_at: 2026-06-10T23:02:00+09:00
---

# REVIEW: TASK-AR-216 Duplicate Claim Release

## Bottom Line

The dispatcher created a second claim for already-completed `TASK-AR-216` before the dispatcher skip-completed regression was fixed. The duplicate claim is released without reopening the task.

## Signal

- Duplicate claim: `CLAIM-20260610-225929-task-ar-216-de2d`
- Root cause: dispatcher selected completed tasks when no non-Done lane was found.
- Fix: `scripts/taskset_dispatcher.py` now skips `completed`/`done` tasks and errors when a task set has no open tasks.
- Regression proof: `pytest tests/test_taskset_dispatcher.py -q` -> `6 passed`.

## Decision

- Release duplicate claim.
- Preserve completed `TASK-AR-216` task state.
- Continue Release Steward through the fixed dispatcher path.

## Action Board

| Status | Action | Owner | Evidence |
| --- | --- | --- | --- |
| Done | Fix dispatcher skip-completed behavior | lead-engineer | `scripts/taskset_dispatcher.py` |
| Done | Add regression tests | lead-engineer | `tests/test_taskset_dispatcher.py` |
| Done | Release duplicate claim | lead-engineer | `CLAIM-20260610-225929-task-ar-216-de2d.json` |

## Next

Run the fixed dispatcher to select the next open Release Steward task.
