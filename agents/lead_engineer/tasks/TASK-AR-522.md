---
id: TASK-AR-522
display_id: TASK-AR-522
task_uid: d947e814-6aff-4954-9a01-5c428ada0c41
registered_at: 2026-06-13T02:54:38+09:00
created_at: 2026-06-13T02:54:38+09:00
updated_at: 2026-06-13T13:50:00+09:00
started_at: 2026-06-13T10:33:54+09:00
completed_at: 2026-06-13T13:50:00+09:00
status: planned
priority: P2
difficulty: S
est_hours: 4
est_tokens: 4000
reservation_id: RES-20260613-025301-47d6de56-01
task_set_id: TASKSET-AR-REPO-HYGIENE
tags:
  - allocator-created
---

# Gate/generator consistency fixes from wave-1/2 W4b notes

## Goal
- Bundle of independently-verified small fixes: (1) work.py emits verification_status pending which is outside WORK-SCHEMA allowed_values passed/failed/blocked/stale (W4b TASK-AR-515 finding); (2) worktree_lifecycle_gate --clean treats _is_dirty None as clean in the re-check path - should skip like evaluate_worktree (W4b TASK-AR-505 note); (3) update_notify uses setdefault for GIT_TERMINAL_PROMPT instead of forcing 0 (W4b TASK-AR-509 note).

## Scope Additions (routed from W4b reviews 2026-06-13)

- merge_queue.py: add subprocess timeouts (fail entry as timed-out) and a pr-mode terminal status label; document single-integrator concurrency boundary (W4b AR-502).
- work.py stats: lead_time vs cycle_time naming (started_at preference), unknown --filter key diagnostics, CSV formula-character escaping, stdout CSV UTF-8 wrapping on cp949 consoles (W4b AR-517).
- attribution/release gates: case-fold instance-id comparison hardening (W4b AR-507/518).

## Completion Evidence

- PR #76: 5-fix consistency bundle (schema pending enum, lifecycle dirty-recheck, update_notify env force, merge_queue timeout/pr-handoff, work.py stats csv/filter/utf8). Case-fold deferred.

## Verification Results

- 88 focused passed across 5 module suites
- work_schema_gate --items --check -> pass
- owner_governance_gate -> exit 0
- W4b inst-w4b-ar522-verifier -> APPROVE
