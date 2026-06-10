---
id: TASK-AR-294
display_id: TASK-AR-294
task_uid: 21597a69-4e08-419f-a6b1-4bd271c39c39
registered_at: 2026-06-11T02:30:00+09:00
created_at: 2026-06-11T02:30:00+09:00
started_at: ""
updated_at: 2026-06-11T02:30:00+09:00
completed_at: ""
title: Implement dirty intake classifier and archive plan
status: planned
priority: P0
difficulty: M
est_hours: 3
est_tokens: 1100
owner: lead_engineer
task_set_id: TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION
tags:
  - closeout
  - dirty-intake
  - archive
  - issue
---

# TASK-AR-294 - Implement dirty intake classifier and archive plan

## Goal

- Classify late dirty work and produce a safe route before any stash drop, branch delete, worktree removal, archive push, or issue creation.

## Scope

- Add `scripts/dirty_intake.py`.
- Compare current git state against a session baseline.
- Classify state as clean, in-scope, log-only, archive-required, branch-residue, worktree-residue, stash-residue, or blocker.
- Print a machine-readable archive plan without executing external side effects by default.
- Add an explicit `--apply-archive` path only if policy config allows it.

## Acceptance Criteria

- Unknown dirty work routes to preservation before deletion.
- Log-only hook diagnostics can be identified separately from real task/doc/test work.
- Active branch and worktree residues are reported with recommended action and preservation status.
- Issue creation is represented as a planned side effect with target issue number or creation route.

## Evidence Targets

- `scripts/dirty_intake.py`
- `tests/test_dirty_intake.py`
- `reviews/REVIEW-2026-06-11-session-closeout-automation-closeout.md`

