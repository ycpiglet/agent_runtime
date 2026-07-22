---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-599-001
work_uid: 8f90ac7c-452f-4486-a6e2-4ae89b2af7c0
kind: unit
parent_id: TASK-AR-599
unit_id: UNIT-TASK-AR-599-001
task_id: TASK-AR-599
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-22T17:13:57+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Wire optional allimbot notifications end to end
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - external_effect
  - security
  - cross_cutting
context: GitHub
inputs:
  - https://github.com/ycpiglet/allimbot/blob/main/clients/allimbot.py
  - https://github.com/ycpiglet/allimbot/blob/main/docs/INTEGRATION.md
  - https://github.com/ycpiglet/agent_runtime/issues/279
target_files:
  - new:src/agent_runtime/allimbot.py
  - src/agent_runtime/update_notify.py
  - new:src/agent_runtime/templates/project/scripts/allimbot.py
  - new:src/agent_runtime/templates/project/scripts/allimbot_stop_hook.cmd
  - src/agent_runtime/templates/project/scripts/agent_orchestrator.py
  - src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - src/agent_runtime/templates/project/.codex/hooks.json
  - new:src/agent_runtime/templates/project/.env.example
  - scripts/owner_governance_gate.py
  - .github/workflows/test.yml
  - pyproject.toml
  - new:docs/ALLIMBOT-INTEGRATION.md
  - new:tests/test_allimbot.py
  - tests/test_update_notify.py
  - tests/test_orchestrator_atomic_writes.py
  - tests/test_owner_governance_chain_parity.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Implement the optional client, connect task completion/governance block/session stop/update notice/CI failure, document blank configuration, and test silent no-op, timeout/error swallowing, payloads, hook wiring, and secret hygiene.
acceptance:
  - No configuration produces no network request and no output/error from runtime paths.
  - Configured local dashboard is attempted before ntfy and all exceptions are swallowed.
  - All requested lifecycle points have deterministic tests or workflow assertions.
  - Secret scanning and host fixture lock checks pass.
verification:
  - python -m pytest tests/test_allimbot.py tests/test_update_notify.py tests/test_orchestrator_atomic_writes.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/verify_wheel_dotfiles.py --check
  - python scripts/owner_governance_gate.py
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report each wired event, no-op/error behavior, configuration documentation, tests, and secret-gate output.
stop_condition: Stop before sending a real notification or committing any secret; verify only with mocks or local test servers.
verified_at: 2026-07-22T17:13:57+09:00
verified_by: codex-root-task-ar-599
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-599-001-20260722171357.json
---

# UNIT-TASK-AR-599-001 - Wire optional allimbot notifications end to end

## Context

GitHub #279 proposes the host-proven ycpiglet/allimbot standard-library client with local /trigger and ntfy fallback, never-block semantics, and four primary runtime/CI integration points.

## Inputs

- https://github.com/ycpiglet/allimbot/blob/main/clients/allimbot.py
- https://github.com/ycpiglet/allimbot/blob/main/docs/INTEGRATION.md
- https://github.com/ycpiglet/agent_runtime/issues/279

## Target Files

- new:src/agent_runtime/allimbot.py
- src/agent_runtime/update_notify.py
- new:src/agent_runtime/templates/project/scripts/allimbot.py
- new:src/agent_runtime/templates/project/scripts/allimbot_stop_hook.cmd
- src/agent_runtime/templates/project/scripts/agent_orchestrator.py
- src/agent_runtime/templates/project/scripts/owner_governance_gate.py
- src/agent_runtime/templates/project/.codex/hooks.json
- new:src/agent_runtime/templates/project/.env.example
- scripts/owner_governance_gate.py
- .github/workflows/test.yml
- pyproject.toml
- new:docs/ALLIMBOT-INTEGRATION.md
- new:tests/test_allimbot.py
- tests/test_update_notify.py
- tests/test_orchestrator_atomic_writes.py
- tests/test_owner_governance_chain_parity.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Implement the optional client, connect task completion/governance block/session stop/update notice/CI failure, document blank configuration, and test silent no-op, timeout/error swallowing, payloads, hook wiring, and secret hygiene.

## Steps

1. Vendor and adapt the official allimbot client into package and host-template surfaces with a three-second default timeout.
2. Add never-block calls at task completion, governance failure, update notice, and session Stop; add optional CI failure delivery.
3. Document environment variables with blank examples, add focused tests, refresh the host lock, and run secret/gate checks.

## Acceptance Criteria

- No configuration produces no network request and no output/error from runtime paths.
- Configured local dashboard is attempted before ntfy and all exceptions are swallowed.
- All requested lifecycle points have deterministic tests or workflow assertions.
- Secret scanning and host fixture lock checks pass.

## Verification

- `python -m pytest tests/test_allimbot.py tests/test_update_notify.py tests/test_orchestrator_atomic_writes.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/verify_wheel_dotfiles.py --check`
- `python scripts/owner_governance_gate.py`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report each wired event, no-op/error behavior, configuration documentation, tests, and secret-gate output.

## Stop Boundary

Stop before sending a real notification or committing any secret; verify only with mocks or local test servers.