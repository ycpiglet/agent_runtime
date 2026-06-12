---
id: TASK-AR-522
display_id: TASK-AR-522
task_uid: d947e814-6aff-4954-9a01-5c428ada0c41
registered_at: 2026-06-13T02:54:38+09:00
created_at: 2026-06-13T02:54:38+09:00
updated_at: 2026-06-13T02:54:38+09:00
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
