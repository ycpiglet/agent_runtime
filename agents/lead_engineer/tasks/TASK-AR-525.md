---
id: TASK-AR-525
display_id: TASK-AR-525
task_uid: c3880949-2587-4c3d-83c3-8104d470aab0
registered_at: 2026-06-13T14:18:04+09:00
created_at: 2026-06-13T14:18:04+09:00
updated_at: 2026-06-13T14:18:04+09:00
started_at: 2026-06-13T14:21:50+09:00
completed_at: 2026-06-13T15:30:00+09:00
status: completed
priority: P2
difficulty: S
est_hours: 3
est_tokens: 3000
reservation_id: RES-20260613-141714-e6e6441b-01
task_set_id: TASKSET-AR-OPS-ERGONOMICS
tags:
  - allocator-created
---

# Runtime asset registry entries + ops command reference

## Goal
- Register the new dashboard hook + 5 skills + the standalone tools (wave_dispatcher/merge_queue/scm_steward/inflight_overlay) in agents/project/RUNTIME-ASSET-REGISTRY.json so runtime_asset_usage tracks them, and add a single OPS-COMMAND-REFERENCE doc mapping every new command/skill/gate to its purpose + invocation (the 'how do I use this' surface).

## Completion Evidence

- PR #87: 21 RUNTIME-ASSET-REGISTRY entries + OPS-COMMAND-REFERENCE.md.

## Verification Results

- W4b APPROVE; full suite green; see claim handoff closeout.
