---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-603-001
work_uid: d4c27f22-67ad-4be8-a69c-49d50048546a
kind: unit
parent_id: TASK-AR-603
unit_id: UNIT-TASK-AR-603-001
task_id: TASK-AR-603
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T17:45:00+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Adopt a shared canonical task-ID contract
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - cross_cutting
  - data_integrity
  - repeated_failure
context: GitHub #299 proves that task_identity emits lowercase UUID hex, taskset_dispatcher accepts a different class, and conversation_work_audit recognizes only one case. The generated ID must travel through allocation, taskset planning, readiness, and audit without rekeying.
inputs:
  - reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
  - scripts/task_identity.py
  - scripts/taskset_dispatcher.py
  - scripts/conversation_work_audit.py
target_files:
  - new:scripts/task_id_contract.py
  - new:src/agent_runtime/templates/project/scripts/task_id_contract.py
  - scripts/task_identity.py
  - src/agent_runtime/templates/project/scripts/task_identity.py
  - scripts/taskset_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
  - scripts/conversation_work_audit.py
  - src/agent_runtime/templates/project/scripts/conversation_work_audit.py
  - tests/test_task_identity.py
  - tests/test_taskset_dispatcher.py
  - tests/test_conversation_work_audit.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Introduce one shared parser/pattern for numeric and timestamp TASK-AR identifiers and migrate the named producer/consumers. Do not change human display numbering or unrelated entity IDs.
acceptance:
  - Allocator output with a-f suffix characters passes taskset planning and conversation audit.
  - Existing numeric IDs retain their behavior.
  - Root and template implementations remain equivalent.
verification:
  - python -m pytest tests/test_task_identity.py tests/test_taskset_dispatcher.py tests/test_conversation_work_audit.py -q
  - python scripts/root_template_parity_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report the accepted ID grammar, migrated consumers, regression matrix, parity result, and exact issue #299 evidence.
stop_condition: Stop if a required consumer lies outside the declared footprint; register the expansion before editing it.
---

# UNIT-TASK-AR-603-001 - Adopt a shared canonical task-ID contract

## Context

GitHub #299 proves that task_identity emits lowercase UUID hex, taskset_dispatcher accepts a different class, and conversation_work_audit recognizes only one case. The generated ID must travel through allocation, taskset planning, readiness, and audit without rekeying.

## Inputs

- reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
- scripts/task_identity.py
- scripts/taskset_dispatcher.py
- scripts/conversation_work_audit.py

## Target Files

- new:scripts/task_id_contract.py
- new:src/agent_runtime/templates/project/scripts/task_id_contract.py
- scripts/task_identity.py
- src/agent_runtime/templates/project/scripts/task_identity.py
- scripts/taskset_dispatcher.py
- src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
- scripts/conversation_work_audit.py
- src/agent_runtime/templates/project/scripts/conversation_work_audit.py
- tests/test_task_identity.py
- tests/test_taskset_dispatcher.py
- tests/test_conversation_work_audit.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Introduce one shared parser/pattern for numeric and timestamp TASK-AR identifiers and migrate the named producer/consumers. Do not change human display numbering or unrelated entity IDs.

## Steps

1. Add failure-first mixed-case allocator-to-dispatch tests.
2. Implement the shared root/template contract and migrate the named consumers.
3. Regenerate the host lock and run focused parity checks.

## Acceptance Criteria

- Allocator output with a-f suffix characters passes taskset planning and conversation audit.
- Existing numeric IDs retain their behavior.
- Root and template implementations remain equivalent.

## Verification

- `python -m pytest tests/test_task_identity.py tests/test_taskset_dispatcher.py tests/test_conversation_work_audit.py -q`
- `python scripts/root_template_parity_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report the accepted ID grammar, migrated consumers, regression matrix, parity result, and exact issue #299 evidence.

## Stop Boundary

Stop if a required consumer lies outside the declared footprint; register the expansion before editing it.
