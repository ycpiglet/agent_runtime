---
id: TASK-AR-520
display_id: TASK-AR-520
task_uid: bbb306dd-5fcd-4613-b128-4d49dd3b3318
registered_at: 2026-06-13T02:54:38+09:00
created_at: 2026-06-13T02:54:38+09:00
updated_at: 2026-06-13T02:54:38+09:00
status: planned
priority: P1
difficulty: S
est_hours: 3
est_tokens: 3000
reservation_id: RES-20260613-025300-45841900-01
task_set_id: TASKSET-AR-REPO-HYGIENE
tags:
  - allocator-created
---

# Backlog board freshness must ignore wall-clock derived fields

## Goal
- taskset_work_gate judges BACKLOG-BOARD.md stale within minutes because the generator embeds wall-clock WIP ages (oldest X.Xh); normalize time-derived fields in the freshness comparison so commits and stop-hook runs do not require a board regen within a 6-minute window. Fixes the recurring test_stop_hook_owner_governance_emits_stop_decision_json flake and the wave-1/2 worker commit friction (proven by stash-revert in TASK-AR-503/510/513/515 W4a reports).
