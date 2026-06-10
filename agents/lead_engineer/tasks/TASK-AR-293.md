---
id: TASK-AR-293
display_id: TASK-AR-293
task_uid: 5dd9af8e-fbb8-4f23-aee3-8c6e567f75a3
registered_at: 2026-06-11T02:30:00+09:00
created_at: 2026-06-11T02:30:00+09:00
started_at: ""
updated_at: 2026-06-11T02:30:00+09:00
completed_at: ""
title: Implement SessionStart baseline capture
status: planned
priority: P0
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION
tags:
  - closeout
  - session-start
  - snapshot
---

# TASK-AR-293 - Implement SessionStart baseline capture

## Goal

- Capture a compact baseline at session start so closeout can distinguish pre-existing state from work created during the session.

## Scope

- Add `scripts/session_baseline.py`.
- Write baseline JSON under `agents/runtime/session_baselines/`.
- Capture git head, current branch, dirty fingerprint, stash count, worktree list, active `codex/*` branches, and capture timestamp.
- Use the verified Windows Python path in hook wiring later, but keep this task focused on the script and tests.

## Acceptance Criteria

- The script can run read-only from the repo root.
- Output is deterministic enough for comparison while still carrying timestamp metadata.
- Tests cover status fingerprinting, stash count, active branch parsing, and worktree capture.
- The script does not mutate git state.

## Evidence Targets

- `scripts/session_baseline.py`
- `tests/test_session_baseline.py`
- `agents/runtime/session_baselines/`

