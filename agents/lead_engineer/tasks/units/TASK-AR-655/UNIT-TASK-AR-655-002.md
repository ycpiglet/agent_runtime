---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-655-002
work_uid: 2868c04b-2c60-4654-8589-f14128740c4e
kind: unit
parent_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-002
task_id: TASK-AR-655
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Add explicit scope amendment and registration dependency aliases
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-655-001
escalation_triggers:
context: Conversation follow-ups must remain flexible without silently becoming execution authority. The current registration path also cannot reference another task created in the same input without guessing its future numeric ID.
inputs:
  - new:scripts/execution_scope.py
  - scripts/work.py
  - scripts/taskset_dispatcher.py
  - tests/test_work_registration.py
  - agents/planning/outbox
target_files:
  - scripts/work.py
  - scripts/taskset_dispatcher.py
  - new:tests/test_execution_scope_cli.py
  - tests/test_work_registration.py
  - tests/test_taskset_dispatcher.py
  - new:docs/goal-scope-contract.md
  - src/agent_runtime/templates/project/scripts/work.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
scope: Add start/status/amend/close command surfaces, proposal-only discovery intake, approval attestations, and registration-local dependency aliases. Do not authorize automatic scope growth.
acceptance:
  - A newly discovered task becomes a planning proposal, not runnable work.
  - A boolean approval flag without attestation cannot amend scope.
  - Old scope revisions remain immutable and auditable.
  - A single registration file can declare an internal unit dependency DAG without preselected task IDs.
  - wave_dispatcher --taskset resolves a newly registered dynamic taskset without a static code entry.
verification:
  - python -m pytest -q tests/test_execution_scope_cli.py tests/test_work_registration.py tests/test_taskset_dispatcher.py
  - python scripts/regen_host_lock_if_needed.py --check
  - python -m pytest -q tests/test_template_smoke.py
handoff: Demonstrate rejected implicit expansion, approved revision creation, and stable dependency alias resolution.
stop_condition: Stop before modifying wave dispatch or claim validation.
---

# UNIT-TASK-AR-655-002 - Add explicit scope amendment and registration dependency aliases

## Context

Conversation follow-ups must remain flexible without silently becoming execution authority. The current registration path also cannot reference another task created in the same input without guessing its future numeric ID.

## Inputs

- new:scripts/execution_scope.py
- scripts/work.py
- scripts/taskset_dispatcher.py
- tests/test_work_registration.py
- agents/planning/outbox

## Target Files

- scripts/work.py
- scripts/taskset_dispatcher.py
- new:tests/test_execution_scope_cli.py
- tests/test_work_registration.py
- tests/test_taskset_dispatcher.py
- new:docs/goal-scope-contract.md
- src/agent_runtime/templates/project/scripts/work.py
- src/agent_runtime/templates/project/scripts/taskset_dispatcher.py

## Scope

Add start/status/amend/close command surfaces, proposal-only discovery intake, approval attestations, and registration-local dependency aliases. Do not authorize automatic scope growth.

## Steps

1. Classify follow-ups as context, constraint, scope expansion, replacement, or separate goal.
2. Write a pending ScopeChangeRequest for membership changes.
3. Require an owner approval reference before creating the next revision.
4. Resolve registration-local task aliases after numeric IDs are reserved.
5. Make a work.py-registered taskset immediately resolvable through the dynamic taskset registry.
6. Add CLI and template parity tests.

## Acceptance Criteria

- A newly discovered task becomes a planning proposal, not runnable work.
- A boolean approval flag without attestation cannot amend scope.
- Old scope revisions remain immutable and auditable.
- A single registration file can declare an internal unit dependency DAG without preselected task IDs.
- wave_dispatcher --taskset resolves a newly registered dynamic taskset without a static code entry.

## Verification

- `python -m pytest -q tests/test_execution_scope_cli.py tests/test_work_registration.py tests/test_taskset_dispatcher.py`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python -m pytest -q tests/test_template_smoke.py`

## Handoff

Demonstrate rejected implicit expansion, approved revision creation, and stable dependency alias resolution.

## Stop Boundary

Stop before modifying wave dispatch or claim validation.
