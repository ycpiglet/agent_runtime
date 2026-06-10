# Task Identity Completion Plan

## Bottom Line

- Objective: prevent task ID collisions during concurrent pane registration and expose lifecycle metadata in UI/backlog surfaces.
- Scope: local repository task files, task registration helper, governance gate, UI state adapter, and generated backlog board.
- Boundary: existing human-readable `TASK-AR-NNN` IDs remain stable; new absolute identity is `task_uid`.

## Requirements

- Add a collision-proof `task_uid` UUIDv4 to every task file.
- Keep `id` and `display_id` available for human-readable routing.
- Add lifecycle metadata: `registered_at`, `created_at`, `started_at`, `updated_at`, `completed_at` where applicable.
- Add an allocator path for new tasks so panes stop guessing the next numeric ID.
- Add a governance gate that blocks missing/duplicate `task_uid`, duplicate `id`, and missing required lifecycle timestamps.
- Expose identity/lifecycle metadata through UI state.
- Restore visibility for completed tasks through an archived task-file section in `BACKLOG-BOARD.md`.

## Task Set

- Task set: `TASKSET-AR-TASK-IDENTITY`.
- Owner: `Identity Steward`.
- Status: local implementation and verification complete after gate/test pass.

## Verification Plan

- `python scripts/task_identity.py --root . check --check`
- `$env:PYTHONPATH='src'; pytest tests/test_task_identity.py tests/test_ui_state.py tests/test_backlog_board_tasksets.py tests/test_taskset_work_gate.py -q`
- `python scripts/owner_governance_gate.py`
