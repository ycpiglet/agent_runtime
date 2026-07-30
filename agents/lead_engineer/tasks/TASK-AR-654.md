---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-654
display_id: TASK-AR-654
task_uid: 6472cbce-31a6-46a9-aad7-f374b7ddf1f3
work_id: TASK-AR-654
work_uid: 6472cbce-31a6-46a9-aad7-f374b7ddf1f3
kind: task
parent_id: TASKSET-AR-HOST-REQUIRED-MERGE-GATES
registered_at: 2026-07-30T09:20:00+09:00
created_at: 2026-07-30T09:20:00+09:00
updated_at: 2026-07-30T09:20:00+09:00
title: Enforce host-owned required gates in the merge queue
status: planned
priority: P1
difficulty: M
est_hours: 3
est_tokens: 9000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-PROJECT-MERGE-GOVERNANCE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-HOST-REQUIRED-MERGE-GATES
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-654/UNIT-TASK-AR-654-001.md
reservation_id: RES-20260730-092000-14f7e099-01
origin_type: owner_request
origin_ref: conversation:2026-07-30-design-gate-enforcement
created_by: codex-root
summary: Make host-required project gates non-optional and base-owned at W5.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
acceptance:
  - A host without agents/host/MERGE-GATES.json behaves exactly as before.
  - A valid policy is schema-checked, canonically hashed, and bound to every newly enqueued entry.
  - Required gates are appended after narrow verification and cannot be removed by --verify.
  - Policy deletion or mutation on a worker branch cannot bypass the base-owned policy.
  - Policy drift or a legacy unbound entry under a nonempty policy blocks before rebase or merge and instructs re-enqueue.
  - include_paths and exclude_paths select gates from the actual rebased diff deterministically.
  - Required-gate failures leave the integration branch unchanged and produce actionable feedback.
  - Root and packaged template implementations and merge-integrator skills remain byte-for-byte aligned.
verification:
  - python -m pytest tests/test_merge_queue.py -q
  - cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py
  - cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
  - python scripts/regen_host_lock_if_needed.py --check
---

# TASK-AR-654 - Enforce host-owned required gates in the merge queue

## Goal

- Prevent worker branches from bypassing project contract, ownership, and visual gates while retaining exact compatibility for hosts without a policy.

## Scope

- Add an optional host-owned merge-gate policy to merge_queue, bind policy identity at enqueue, revalidate it from the integration base before mutation, run path-applicable gates after rebase, and mirror the behavior into the packaged host template and skill documentation. Do not change config/adoption/sync files reserved by the active Bean pilot.

## Acceptance Criteria

- A host without agents/host/MERGE-GATES.json behaves exactly as before.
- A valid policy is schema-checked, canonically hashed, and bound to every newly enqueued entry.
- Required gates are appended after narrow verification and cannot be removed by --verify.
- Policy deletion or mutation on a worker branch cannot bypass the base-owned policy.
- Policy drift or a legacy unbound entry under a nonempty policy blocks before rebase or merge and instructs re-enqueue.
- include_paths and exclude_paths select gates from the actual rebased diff deterministically.
- Required-gate failures leave the integration branch unchanged and produce actionable feedback.
- Root and packaged template implementations and merge-integrator skills remain byte-for-byte aligned.

## Verification

- `python -m pytest tests/test_merge_queue.py -q`
- `cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py`
- `cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md`
- `python scripts/regen_host_lock_if_needed.py --check`
