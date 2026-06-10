---
id: TASK-AR-259
display_id: TASK-AR-259
task_uid: 59a01025-c27c-4c08-875a-e450451d4dfd
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
title: Lifecycle drift cleanup and claim normalization
status: completed
priority: P0
importance: High
difficulty: M
est_hours: 4
est_tokens: 1400
task_set_id: TASKSET-AR-GOVERNANCE-OPS
team: release-integrity
owner: release-integrity
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:55:00+09:00
completed_at: 2026-06-10T23:55:00+09:00
tags: [lifecycle, task-claims, heartbeat, worktree, governance]
audit_log: [agents/runtime/task_claims, scripts/collaboration_governance_gate.py]
---

## Goal

Normalize lifecycle evidence so released claims, heartbeats, active worktrees, and task statuses agree.

## Completion Criteria

- Future heartbeat watch findings are resolved or documented with corrected timestamps.
- Released claims use the expected completion phase and progress metadata only when backed by task evidence.
- Active claims with missing worktrees are released, corrected, or recreated through dispatcher-owned worktrees.
- A review artifact records the before/after lifecycle watch count.
- `python scripts/collaboration_governance_gate.py --root . --check` passes with reduced lifecycle watch findings.

## Execution Notes

- Do not rewrite task history without evidence.
- Do not delete claims; normalize status and append handoff/log notes.

## Result

- Current `collaboration_governance_gate.py --check` output has no lifecycle findings.
- Current `state_sync_gate.py --check` output has `findings=0`.
- Added `reviews/REVIEW-2026-06-10-agent-runtime-lifecycle-drift-cleanup.md`.
