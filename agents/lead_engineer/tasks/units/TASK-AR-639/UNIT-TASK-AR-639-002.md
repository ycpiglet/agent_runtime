---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-639-002
work_uid: 3c232b37-d686-4861-b0be-7930a078b3df
kind: unit
parent_id: TASK-AR-639
unit_id: UNIT-TASK-AR-639-002
task_id: TASK-AR-639
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Block task-claim-projection split-brain and support explicit recovery
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The current checkout had an implementation commit and passed unit verification while task/unit/pointer/claim surfaces disagreed. Existing state_sync_gate passed because it did not correlate these sources.
inputs:
  - scripts/state_sync_gate.py
  - scripts/task_claim_dispatcher.py
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/lead_engineer/tasks/TASK-AR-631.md
target_files:
  - scripts/state_sync_gate.py
  - scripts/task_claim_dispatcher.py
  - tests/test_state_sync_gate.py
  - tests/test_task_claim_dispatcher.py
  - agents/project/WORK-SCHEMA.yml
scope: Correlate active/implemented work with task, unit, claim, verification, branch, and pointer state; define a loud recovery marker for pre-existing missing-claim history. Do not retroactively create claims.
acceptance:
  - The pre-fix TASK-AR-631 shape blocks.
  - A correctly claimed active task passes.
  - An explicitly recovered historical task passes with a visible watch signal.
  - Pointer and UI projections cannot claim no open work while a tracked implementation is in flight.
verification:
  - python -m pytest tests/test_state_sync_gate.py tests/test_task_claim_dispatcher.py -q
  - python scripts/state_sync_gate.py --check
handoff: Provide the contradiction matrix, recovery schema, and governance-chain result.
stop_condition: Stop before inventing a generic event-sourcing migration or mutating completed historical claims.
---

# UNIT-TASK-AR-639-002 - Block task-claim-projection split-brain and support explicit recovery

## Context

The current checkout had an implementation commit and passed unit verification while task/unit/pointer/claim surfaces disagreed. Existing state_sync_gate passed because it did not correlate these sources.

## Inputs

- scripts/state_sync_gate.py
- scripts/task_claim_dispatcher.py
- agents/project/NEXT-SESSION-POINTER.yml
- agents/lead_engineer/tasks/TASK-AR-631.md

## Target Files

- scripts/state_sync_gate.py
- scripts/task_claim_dispatcher.py
- tests/test_state_sync_gate.py
- tests/test_task_claim_dispatcher.py
- agents/project/WORK-SCHEMA.yml

## Scope

Correlate active/implemented work with task, unit, claim, verification, branch, and pointer state; define a loud recovery marker for pre-existing missing-claim history. Do not retroactively create claims.

## Steps

1. Add fixtures for the TASK-AR-631 contradiction.
2. Define blocking findings for impossible active and completed combinations.
3. Define an explicit recovered-without-claim record shape and reason.
4. Wire the reconciliation result into the governance chain.

## Acceptance Criteria

- The pre-fix TASK-AR-631 shape blocks.
- A correctly claimed active task passes.
- An explicitly recovered historical task passes with a visible watch signal.
- Pointer and UI projections cannot claim no open work while a tracked implementation is in flight.

## Verification

- `python -m pytest tests/test_state_sync_gate.py tests/test_task_claim_dispatcher.py -q`
- `python scripts/state_sync_gate.py --check`

## Handoff

Provide the contradiction matrix, recovery schema, and governance-chain result.

## Stop Boundary

Stop before inventing a generic event-sourcing migration or mutating completed historical claims.
