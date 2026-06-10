---
id: TASK-AR-292
display_id: TASK-AR-292
task_uid: 76c8c0f6-2f02-4d6c-9d09-7f3e8e0f2921
registered_at: 2026-06-11T02:30:00+09:00
created_at: 2026-06-11T02:30:00+09:00
started_at: ""
updated_at: 2026-06-11T02:30:00+09:00
completed_at: ""
title: Define session closeout contract and baseline schema
status: planned
priority: P0
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION
tags:
  - closeout
  - baseline
  - governance
---

# TASK-AR-292 - Define session closeout contract and baseline schema

## Goal

- Define the canonical contract for session closeout, including how to separate baseline state, current declared work, late dirty work, stash/archive refs, branches, worktrees, and issue handoffs.

## Scope

- Create `agents/project/SESSION-CLOSEOUT-CONTRACT.md`.
- Create `schemas/session-baseline.schema.json`.
- Extend lifecycle/state documentation if a new closeout state is needed.
- Keep side-effect policy explicit: classify first, preserve before drop, and require policy for external archive/issue actions.

## Acceptance Criteria

- The contract defines the Owner meaning of "마무리/정리".
- The baseline schema includes `head`, branch, status fingerprint, stash count, worktrees, active `codex/*` branches, and timestamp.
- The contract states that completion claims require fresh evidence, not archived assumptions.
- The schema has a focused test.

## Evidence Targets

- `agents/project/SESSION-CLOSEOUT-CONTRACT.md`
- `schemas/session-baseline.schema.json`
- `tests/test_session_baseline.py`

