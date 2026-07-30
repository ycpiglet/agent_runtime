---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-656-001
work_uid: bf9fa0b4-47c3-4b70-be49-a6be339c62a2
kind: unit
parent_id: TASK-AR-656
unit_id: UNIT-TASK-AR-656-001
task_id: TASK-AR-656
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Implement a managed Runtime hook core with host extension registry
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: Autofolio needed its Owner-authority hook plus canonical Runtime hooks, but two legacy taskset/stop commands remain duplicated because the tracked hooks file is seed_once and has no typed extension boundary.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - src/agent_runtime/hook_runtime.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/templates/project/.codex/hooks.json
target_files:
  - src/agent_runtime/hook_runtime.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/sync.py
  - src/agent_runtime/templates/project/.codex/hooks.json
  - src/agent_runtime/templates/project/scripts/install_hooks.py
  - tests/test_hook_runtime.py
  - tests/test_install_hooks.py
  - tests/test_doctor.py
  - tests/test_inventory_sync_sanitize.py
scope: Compose tracked local hooks only. Do not enable machine-local trust settings or execute host side effects.
acceptance:
  - Host authority remains intact.
  - Legacy duplicates disappear after migration.
  - Canonical Runtime hooks remain updateable.
  - No hook is enabled without the existing trust boundary.
verification:
  - python -m pytest tests/test_doctor.py tests/test_hook_runtime.py tests/test_install_hooks.py tests/test_inventory_sync_sanitize.py -q
handoff: Attach the merge schema, duplicate migration fixture, host-order proof, cross-platform tests, and independent W4b.
stop_condition: Stop before editing user-global settings, enabling trust, running external hooks, or weakening a host Owner-authority command.
---

# UNIT-TASK-AR-656-001 - Implement a managed Runtime hook core with host extension registry

## Context

Autofolio needed its Owner-authority hook plus canonical Runtime hooks, but two legacy taskset/stop commands remain duplicated because the tracked hooks file is seed_once and has no typed extension boundary.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- src/agent_runtime/hook_runtime.py
- src/agent_runtime/doctor.py
- src/agent_runtime/templates/project/.codex/hooks.json

## Target Files

- src/agent_runtime/hook_runtime.py
- src/agent_runtime/doctor.py
- src/agent_runtime/sync.py
- src/agent_runtime/templates/project/.codex/hooks.json
- src/agent_runtime/templates/project/scripts/install_hooks.py
- tests/test_hook_runtime.py
- tests/test_install_hooks.py
- tests/test_doctor.py
- tests/test_inventory_sync_sanitize.py

## Scope

Compose tracked local hooks only. Do not enable machine-local trust settings or execute host side effects.

## Steps

1. Define typed host extension entries and canonical ordering.
2. Add semantic identity and duplicate migration tests.
3. Merge Runtime and host hooks deterministically.
4. Verify POSIX/Windows commands, timeouts, and failure semantics.
5. Prove repeated sync is byte-identical.

## Acceptance Criteria

- Host authority remains intact.
- Legacy duplicates disappear after migration.
- Canonical Runtime hooks remain updateable.
- No hook is enabled without the existing trust boundary.

## Verification

- `python -m pytest tests/test_doctor.py tests/test_hook_runtime.py tests/test_install_hooks.py tests/test_inventory_sync_sanitize.py -q`

## Handoff

Attach the merge schema, duplicate migration fixture, host-order proof, cross-platform tests, and independent W4b.

## Stop Boundary

Stop before editing user-global settings, enabling trust, running external hooks, or weakening a host Owner-authority command.
