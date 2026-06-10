---
id: TASK-AR-296
display_id: TASK-AR-296
task_uid: eef9ec3b-5b4c-42b3-976a-5fa62bffb296
registered_at: 2026-06-11T02:30:00+09:00
created_at: 2026-06-11T02:30:00+09:00
started_at: ""
updated_at: 2026-06-11T02:30:00+09:00
completed_at: ""
title: Package session-closeout skill and verification closeout gate
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION
tags:
  - skill
  - closeout
  - verification
  - taskset
---

# TASK-AR-296 - Package session-closeout skill and verification closeout gate

## Goal

- Package the closeout workflow as a reusable skill and verify the full taskset through an explicit closeout command.

## Scope

- Add `skills/session-closeout/SKILL.md`.
- Add `scripts/verify_session_closeout_taskset.py`.
- Ensure the skill states the required final evidence: clean status, empty local stash, root-only worktree list, active branch scan, archive refs, issue pointers, and Owner governance result.
- Publish an Owner-facing closeout review after implementation.

## Acceptance Criteria

- The skill is invokable for "마무리", "정리", cleanup, closeout, branch/stash/worktree questions, and PR/merge completion.
- The verification wrapper runs the named taskset gate and Owner governance gate.
- The closeout review lists remaining archive refs as preserved evidence, not active residue.
- No completion claim is allowed from stale evidence.

## Evidence Targets

- `skills/session-closeout/SKILL.md`
- `scripts/verify_session_closeout_taskset.py`
- `reviews/REVIEW-2026-06-11-session-closeout-automation-closeout.md`

