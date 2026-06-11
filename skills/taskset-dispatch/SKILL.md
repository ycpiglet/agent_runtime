---
name: taskset-dispatch
version: 1.0.0
description: Use when the user asks to work on a taskset lane, TASKSET-AR-* workflow, or parallel pane/task-set lane.
triggers:
  - taskset
  - TASKSET-AR
  - 진행
dependencies:
  - scripts/taskset_dispatcher.py
  - scripts/taskset_work_gate.py
  - scripts/parallel_worktree_gate.py
registry_id: taskset-dispatch
template_path: src/agent_runtime/templates/project/skills/taskset-dispatch/SKILL.md
---

# Task Set Dispatch

Use this skill when the user asks to work on a `taskset-*`, `TASKSET-AR-*`, or
parallel pane/task-set lane.

## Workflow

1. Plan the lane before editing:

   ```powershell
   python scripts/taskset_dispatcher.py plan <taskset-alias> --json
   ```

2. Claim the lane before editing:

   ```powershell
   python scripts/taskset_dispatcher.py start <taskset-alias> --json
   ```

3. Work only in the returned `worktree_path` and `branch`.

4. Keep `agents/project/NEXT-SESSION-POINTER.yml` and the active claim updated
   with:

   - `task_set_id`
   - `phase`
   - `progress_pct`
   - `step_index`
   - `step_total`
   - `status_text`

5. Before handoff, run:

   ```powershell
   python scripts/taskset_work_gate.py --check
   python scripts/parallel_worktree_gate.py --check
   ```

## Rules

- One task set has one active claim by default.
- Use human-friendly display names in reports, such as `Quality Sentinel`,
  `Progress Scout`, `Console Operator`, and `Repo Custodian`.
- System identity stays in machine fields: `task_set_id`, `task_id`,
  `claim_id`, `agent_instance_id`, `pane_id`, `worktree_path`, and `branch`.
- If parallel work inside one task set is truly needed, record
  `allow_parallel_task_set: true` and the reason in the claim/handoff.
