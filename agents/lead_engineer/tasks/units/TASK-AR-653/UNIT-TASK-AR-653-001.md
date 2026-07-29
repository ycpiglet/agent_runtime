---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-653-001
work_uid: 6afd8902-c783-453f-8773-d69de83fdef0
kind: unit
parent_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
task_id: TASK-AR-653
task_set_id: TASKSET-AR-MERGE-QUEUE-SAFETY
initiative_id: INIT-AR-PARALLEL-INTEGRATION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-30T07:45:00+09:00
updated_at: 2026-07-30T08:05:09+09:00
origin_type: owner_request
origin_ref: conversation:2026-07-30-parallel-union-harness
created_by: codex-root
summary: Add repository-common lock, atomic state, and dependency-aware processing
horizon: unit
model_tier: worker_low
escalation_triggers:
context: The current JSON FIFO explicitly permits only one process by convention. Parallel sessions can race enqueue/remove/process and overwrite state, while FIFO order cannot express a branch that must wait for another task.
inputs:
  - scripts/merge_queue.py
  - src/agent_runtime/templates/project/scripts/merge_queue.py
  - tests/test_merge_queue.py
  - skills/merge-integrator/SKILL.md
  - src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
target_files:
  - scripts/merge_queue.py
  - src/agent_runtime/templates/project/scripts/merge_queue.py
  - tests/test_merge_queue.py
  - skills/merge-integrator/SKILL.md
  - src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
scope: Change only the merge queue implementation, its exact template mirror, its focused test module, and the root/template merge-integrator skill pair. Do not touch TASK-AR-648 dispatcher files, workflows, shared runtime registries outside normal lifecycle writes, or release/deploy gates.
acceptance:
  - Two concurrent enqueues are both retained.
  - A competing mutator receives a bounded, actionable lock failure rather than writing unlocked state.
  - Dependency failures leave main and branch state unchanged.
  - Existing merge, failure feedback, timeout, dry-run, PR handoff, duplicate, and remove tests continue to pass.
  - Root/template code and skill copies match.
verification:
  - python -m pytest tests/test_merge_queue.py
  - cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py
  - cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
handoff: Provide the claimed unit ID, implementation commit, focused test evidence, independent verifier result, and merge readiness without touching the reserved TASK-AR-648 or TASK-AR-652 scopes.
stop_condition: Stop if another active claim overlaps any of the five target files, if the Git common directory cannot be resolved safely, or if compatibility requires changing dispatcher/workflow files reserved by another session.
verified_at: 2026-07-30T08:05:09+09:00
verified_by: le-20260730-075500-kst-merge-queue-safety
evidence_refs:
  - reviews/VERIFY-2026-07-30-unit-task-ar-653-001-20260730080509.json
---

# UNIT-TASK-AR-653-001 - Add repository-common lock, atomic state, and dependency-aware processing

## Context

The current JSON FIFO explicitly permits only one process by convention. Parallel sessions can race enqueue/remove/process and overwrite state, while FIFO order cannot express a branch that must wait for another task.

## Inputs

- scripts/merge_queue.py
- src/agent_runtime/templates/project/scripts/merge_queue.py
- tests/test_merge_queue.py
- skills/merge-integrator/SKILL.md
- src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md

## Target Files

- scripts/merge_queue.py
- src/agent_runtime/templates/project/scripts/merge_queue.py
- tests/test_merge_queue.py
- skills/merge-integrator/SKILL.md
- src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md

## Scope

Change only the merge queue implementation, its exact template mirror, its focused test module, and the root/template merge-integrator skill pair. Do not touch TASK-AR-648 dispatcher files, workflows, shared runtime registries outside normal lifecycle writes, or release/deploy gates.

## Steps

1. Characterize the existing queue schema, command mutation boundaries, and local/PR processing invariants.
2. Add an exclusive lock located from the Git common directory and apply it to every state-mutating command.
3. Write queue JSON via a same-directory temporary file, flush it, and atomically replace the live state.
4. Add optional declared task dependencies and deterministic dependency validation/order before integration.
5. Add process-level concurrency, atomicity, unknown/cycle/unmet dependency, dry-run, and parity regressions.
6. Update both merge-integrator skill copies to document the enforced behavior and recovery path.

## Acceptance Criteria

- Two concurrent enqueues are both retained.
- A competing mutator receives a bounded, actionable lock failure rather than writing unlocked state.
- Dependency failures leave main and branch state unchanged.
- Existing merge, failure feedback, timeout, dry-run, PR handoff, duplicate, and remove tests continue to pass.
- Root/template code and skill copies match.

## Verification

- `python -m pytest tests/test_merge_queue.py`
- `cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py`
- `cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md`

## Handoff

Provide the claimed unit ID, implementation commit, focused test evidence, independent verifier result, and merge readiness without touching the reserved TASK-AR-648 or TASK-AR-652 scopes.

## Stop Boundary

Stop if another active claim overlaps any of the five target files, if the Git common directory cannot be resolved safely, or if compatibility requires changing dispatcher/workflow files reserved by another session.