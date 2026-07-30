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
updated_at: 2026-07-30T10:09:00+09:00
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
  - agents/lead_engineer/tasks/units/TASK-AR-654/UNIT-TASK-AR-654-001.md
  - agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.json
  - agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.handoff.md
  - agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.log.md
  - agents/runtime/pane_events/pane-events.jsonl
  - agents/runtime/a2a/messages.jsonl
  - reviews/INDEX.md
  - reviews/VERIFY-2026-07-30-unit-task-ar-654-001-*.json
  - reviews/W4B-2026-07-30-unit-task-ar-654-001-*.md
  - reviews/REVIEW-2026-07-30-task-ar-654-w4-evidence-footprint-amendment.md
  - BACKLOG-BOARD.md
  - agents/lead_engineer/tasks/TASK-AR-654.md
  - agents/project/initiatives/INIT-AR-PROJECT-MERGE-GOVERNANCE.md
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/TASK-ID-RESERVATIONS.json
  - agents/project/work-items/TASKSET-DEFINITIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - agents/runtime/instances/codex-root-task-ar-654.json
  - docs/superpowers/plans/2026-07-30-host-required-merge-gates.md
  - owner-docs.yml
  - reviews/REVIEW-2026-07-30-task-ar-654-host-lock-scope-amendment.md
  - reviews/REVIEW-2026-07-30-taskset-ar-host-required-merge-gates-registration.md
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
verified_at: 2026-07-30T10:06:25+09:00
verified_by: codex-root-task-ar-654
evidence_refs:
  - reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730094218.json
  - reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730095331.json
  - reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730100128.json
  - reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730100625.json
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
- agents/lead_engineer/tasks/units/TASK-AR-654/UNIT-TASK-AR-654-001.md
- agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.json
- agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.handoff.md
- agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.log.md
- agents/runtime/pane_events/pane-events.jsonl
- agents/runtime/a2a/messages.jsonl
- reviews/INDEX.md
- reviews/VERIFY-2026-07-30-unit-task-ar-654-001-*.json
- reviews/W4B-2026-07-30-unit-task-ar-654-001-*.md
- reviews/REVIEW-2026-07-30-task-ar-654-w4-evidence-footprint-amendment.md
- BACKLOG-BOARD.md
- agents/lead_engineer/tasks/TASK-AR-654.md
- agents/project/initiatives/INIT-AR-PROJECT-MERGE-GOVERNANCE.md
- agents/project/work-items/PLAN-ASSUMPTIONS.json
- agents/project/work-items/TASK-ID-RESERVATIONS.json
- agents/project/work-items/TASKSET-DEFINITIONS.json
- agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
- agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
- agents/runtime/instances/codex-root-task-ar-654.json
- docs/superpowers/plans/2026-07-30-host-required-merge-gates.md
- owner-docs.yml
- reviews/REVIEW-2026-07-30-task-ar-654-host-lock-scope-amendment.md
- reviews/REVIEW-2026-07-30-taskset-ar-host-required-merge-gates-registration.md

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
