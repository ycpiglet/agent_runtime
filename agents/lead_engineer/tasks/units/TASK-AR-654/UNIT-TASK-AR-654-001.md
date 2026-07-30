---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-654-001
work_uid: fa554245-7e63-45e4-aa4b-c58cf38364c8
kind: unit
parent_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
task_id: TASK-AR-654
task_set_id: TASKSET-AR-HOST-REQUIRED-MERGE-GATES
initiative_id: INIT-AR-PROJECT-MERGE-GOVERNANCE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-30T09:20:00+09:00
updated_at: 2026-07-30T09:42:18+09:00
origin_type: owner_request
origin_ref: conversation:2026-07-30-design-gate-enforcement
created_by: codex-root
summary: Bind and execute host-required merge gates
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: work.py verify executes task-authored commands, but W5 merge_queue only runs optional enqueue-time --verify commands or the owner default. A worker can therefore omit product-level design, ownership, and rendered-output checks. The policy must be owned by the integration base, not by the worker branch being tested.
inputs:
  - scripts/merge_queue.py
  - tests/test_merge_queue.py
  - skills/merge-integrator/SKILL.md
  - reviews/RETRO-2026-07-30-task-ar-653-merge-queue-safety.md
target_files:
  - scripts/merge_queue.py
  - src/agent_runtime/templates/project/scripts/merge_queue.py
  - tests/test_merge_queue.py
  - skills/merge-integrator/SKILL.md
  - src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
  - reviews/PLAN-2026-07-30-host-required-merge-gates.md
  - tests/fixtures/host/agent_runtime.lock.json
scope: Implement optional agents/host/MERGE-GATES.json loading, canonical digest binding, base-owned revalidation, path selection, safe placeholder substitution, required execution, feedback, dry-run visibility, focused tests, and exact template/skill parity. Do not touch src/agent_runtime/config.py, adoption/sync/doctor/CLI files, TASK-AR-648 pilot files, or GitHub workflow/release surfaces.
acceptance:
  - Absent policy produces the existing queue schema and behavior.
  - Invalid and duplicate policies fail without queue mutation.
  - Commands are parsed without a shell and only declared placeholders are substituted.
  - Worker policy changes do not alter the effective required gates.
  - A failed required gate never reaches merge or PR handoff.
  - Focused regressions and root/template parity pass.
verification:
  - python -m pytest tests/test_merge_queue.py -q
  - cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py
  - cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report task/unit IDs, policy schema, compatibility behavior, failure-first tests, exact implementation commit, independent verification, and how Bean Wiki CI mirrors the same required commands.
stop_condition: Stop if implementation must modify TASK-AR-648 target files, make policy mandatory for legacy hosts, execute commands through a shell, trust policy content from the worker branch, or weaken existing queue safety.
verified_at: 2026-07-30T09:42:18+09:00
verified_by: codex-root-task-ar-654
evidence_refs:
  - reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730094218.json
---

# UNIT-TASK-AR-654-001 - Bind and execute host-required merge gates

## Context

work.py verify executes task-authored commands, but W5 merge_queue only runs optional enqueue-time --verify commands or the owner default. A worker can therefore omit product-level design, ownership, and rendered-output checks. The policy must be owned by the integration base, not by the worker branch being tested.

## Inputs

- scripts/merge_queue.py
- tests/test_merge_queue.py
- skills/merge-integrator/SKILL.md
- reviews/RETRO-2026-07-30-task-ar-653-merge-queue-safety.md

## Target Files

- scripts/merge_queue.py
- src/agent_runtime/templates/project/scripts/merge_queue.py
- tests/test_merge_queue.py
- skills/merge-integrator/SKILL.md
- src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
- reviews/PLAN-2026-07-30-host-required-merge-gates.md
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Implement optional agents/host/MERGE-GATES.json loading, canonical digest binding, base-owned revalidation, path selection, safe placeholder substitution, required execution, feedback, dry-run visibility, focused tests, and exact template/skill parity. Do not touch src/agent_runtime/config.py, adoption/sync/doctor/CLI files, TASK-AR-648 pilot files, or GitHub workflow/release surfaces.

## Steps

1. Record the compatibility and threat model in the plan review.
2. Add failure-first tests for policy validation, mandatory append, path selection, digest drift, base ownership, failure cleanup, linked worktree state, and dry-run.
3. Implement canonical policy loading and queue-entry binding from the primary checkout.
4. Revalidate policy before process mutation and run applicable required gates after rebase against the actual diff.
5. Update feedback and merge-integrator guidance, mirror root/template files, and run focused plus governance verification.

## Acceptance Criteria

- Absent policy produces the existing queue schema and behavior.
- Invalid and duplicate policies fail without queue mutation.
- Commands are parsed without a shell and only declared placeholders are substituted.
- Worker policy changes do not alter the effective required gates.
- A failed required gate never reaches merge or PR handoff.
- Focused regressions and root/template parity pass.

## Verification

- `python -m pytest tests/test_merge_queue.py -q`
- `cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py`
- `cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report task/unit IDs, policy schema, compatibility behavior, failure-first tests, exact implementation commit, independent verification, and how Bean Wiki CI mirrors the same required commands.

## Stop Boundary

Stop if implementation must modify TASK-AR-648 target files, make policy mandatory for legacy hosts, execute commands through a shell, trust policy content from the worker branch, or weaken existing queue safety.
