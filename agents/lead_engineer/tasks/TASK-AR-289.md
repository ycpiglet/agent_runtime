---
id: TASK-AR-289
display_id: TASK-AR-289
task_uid: 382b4490-69e8-40e1-b036-bcbf5f69268d
registered_at: 2026-06-11T01:45:00+09:00
created_at: 2026-06-11T01:45:00+09:00
started_at: 2026-06-11T11:53:49+09:00
updated_at: 2026-06-11T11:53:49+09:00
completed_at: 2026-06-11T11:53:49+09:00
title: Normalize timeline claim and worktree drift
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 1100
owner: lead_engineer
task_set_id: TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE
tags:
  - multi-pane
  - lifecycle
  - drift
  - worktree
---

# TASK-AR-289 - Normalize timeline claim and worktree drift

## Goal

- Resolve or explain future heartbeat values, released-claim phase/progress drift, and stale worktree references.

## Scope

- Add a drift normalizer/report that classifies claim timestamps, phase/progress consistency, active worktree existence, and released-claim handoff state.
- Avoid destructive worktree cleanup unless Owner-approved.
- Generate a review report for drift decisions.
- Feed findings into Owner governance and UI health.

## Acceptance Criteria

- Future heartbeat timestamps are flagged with claim id and observed reference time.
- Released claims with non-terminal progress or phase are flagged.
- Worktrees without active claims are classified as stale candidates, not automatically deleted.
- Missing active worktree paths produce block or watch according to policy.

## Evidence Targets

- `scripts/multipane_drift_gate.py`
- `tests/test_multipane_drift_gate.py`
- `reviews/REVIEW-2026-06-10-agent-runtime-parallel-collaboration-audit.md`
