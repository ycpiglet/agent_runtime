---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-653
display_id: TASK-AR-653
task_uid: f7ef3b94-9c25-4e2c-b0a0-da98e1d67a6b
work_id: TASK-AR-653
work_uid: f7ef3b94-9c25-4e2c-b0a0-da98e1d67a6b
kind: task
parent_id: TASKSET-AR-MERGE-QUEUE-SAFETY
registered_at: 2026-07-30T07:45:00+09:00
created_at: 2026-07-30T07:45:00+09:00
updated_at: 2026-07-30T07:45:00+09:00
title: Harden merge queue concurrency and dependency ordering
status: planned
priority: P1
difficulty: M
est_hours: 1
est_tokens: 1000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-INTEGRATION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-MERGE-QUEUE-SAFETY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-653/UNIT-TASK-AR-653-001.md
reservation_id: RES-20260730-074500-b6288939-01
origin_type: owner_request
origin_ref: conversation:2026-07-30-parallel-union-harness
created_by: codex-root
summary: Serialize all queue mutations through a repository-common lock, persist queue state atomically, and fail closed when declared task dependencies are unknown, cyclic, or unmet.
planner_model_tier: planner_high
worker_model_tier: worker_low
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
acceptance:
  - Concurrent enqueue/remove/process invocations cannot lose queue entries or corrupt queue.json.
  - The lock is shared by every worktree through git rev-parse --git-common-dir.
  - Queue state replacement is atomic and leaves valid JSON after interrupted or competing writes.
  - Optional task dependencies produce deterministic topological processing order.
  - Unknown dependencies, cycles, and unmet predecessors block before a branch is merged.
  - Dry-run remains mutation-free and existing local and PR modes retain their safety boundaries.
  - Root and packaged project-template implementations and skill documentation remain byte-for-byte aligned where required.
verification:
  - python -m pytest tests/test_merge_queue.py
  - cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py
  - cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
---

# TASK-AR-653 - Harden merge queue concurrency and dependency ordering

## Goal

- Serialize all queue mutations through a repository-common lock, persist queue state atomically, and fail closed when declared task dependencies are unknown, cyclic, or unmet.

## Scope

- Serialize all queue mutations through a repository-common lock, persist queue state atomically, and fail closed when declared task dependencies are unknown, cyclic, or unmet.

## Acceptance Criteria

- Concurrent enqueue/remove/process invocations cannot lose queue entries or corrupt queue.json.
- The lock is shared by every worktree through git rev-parse --git-common-dir.
- Queue state replacement is atomic and leaves valid JSON after interrupted or competing writes.
- Optional task dependencies produce deterministic topological processing order.
- Unknown dependencies, cycles, and unmet predecessors block before a branch is merged.
- Dry-run remains mutation-free and existing local and PR modes retain their safety boundaries.
- Root and packaged project-template implementations and skill documentation remain byte-for-byte aligned where required.

## Verification

- `python -m pytest tests/test_merge_queue.py`
- `cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py`
- `cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md`
