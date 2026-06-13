---
id: TASK-AR-523
display_id: TASK-AR-523
task_uid: 61af969f-9b57-483b-b29b-a33bf5dc03df
registered_at: 2026-06-13T14:18:04+09:00
created_at: 2026-06-13T14:18:04+09:00
updated_at: 2026-06-13T14:18:04+09:00
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 5000
reservation_id: RES-20260613-141710-61981fe0-01
task_set_id: TASKSET-AR-OPS-ERGONOMICS
tags:
  - allocator-created
---

# Session-start W0 dashboard hook (auto-surface 500-series observability)

## Goal
- Nothing surfaces the 500-series observability at session start. Add scripts/session_dashboard.py aggregating work.py status (active claims+worktrees), inflight_overlay --summary, update-notify, and scm_steward report (read-only, ASCII, always exit 0, fast/cached) into one panel; wire it into .codex/hooks.json SessionStart (+ template). One hook call so session start stays fast.
