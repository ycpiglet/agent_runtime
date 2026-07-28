---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-645-001
work_uid: a944e692-2bed-41b1-89e1-6c71ad35d770
kind: unit
parent_id: TASK-AR-645
unit_id: UNIT-TASK-AR-645-001
task_id: TASK-AR-645
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
summary: Introduce per-entry task-linked compound records and retrieval
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Current closure can be satisfied by any same-day compound/review/retro and the template ships a managed monolithic compound_log placeholder that collides with host data.
inputs:
  - scripts/closure_gate.py
  - scripts/compound_cadence_gate.py
  - src/agent_runtime/templates/project/scripts/kedb_search.py
target_files:
  - scripts/closure_gate.py
  - scripts/compound_cadence_gate.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/kedb_search.py
  - src/agent_runtime/templates/project/agents/project/knowledge
  - tests/test_closure_gate.py
  - tests/test_compound_cadence_gate.py
  - tests/test_compound_cadence_obligation.py
scope: Create and query individual compound records keyed by work ID and defect signature; generate indexes. Do not migrate every historical compound entry in this unit.
acceptance:
  - Unrelated same-day records do not satisfy closeout.
  - A matching signature is surfaced before implementation.
  - Concurrent compounds do not edit one shared data file.
verification:
  - python -m pytest tests/test_closure_gate.py tests/test_compound_cadence_gate.py tests/test_compound_cadence_obligation.py -q
handoff: Provide a repeat-defect fixture showing create, retrieve, and closeout enforcement.
stop_condition: Stop before bulk-rewriting historical compound logs.
---

# UNIT-TASK-AR-645-001 - Introduce per-entry task-linked compound records and retrieval

## Context

Current closure can be satisfied by any same-day compound/review/retro and the template ships a managed monolithic compound_log placeholder that collides with host data.

## Inputs

- scripts/closure_gate.py
- scripts/compound_cadence_gate.py
- src/agent_runtime/templates/project/scripts/kedb_search.py

## Target Files

- scripts/closure_gate.py
- scripts/compound_cadence_gate.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/kedb_search.py
- src/agent_runtime/templates/project/agents/project/knowledge
- tests/test_closure_gate.py
- tests/test_compound_cadence_gate.py
- tests/test_compound_cadence_obligation.py

## Scope

Create and query individual compound records keyed by work ID and defect signature; generate indexes. Do not migrate every historical compound entry in this unit.

## Steps

1. Define compound record schema and deterministic signature.
2. Add task-start and post-failure lookup.
3. Require linked evidence for repeat-defect closeout.
4. Generate a conflict-free index.

## Acceptance Criteria

- Unrelated same-day records do not satisfy closeout.
- A matching signature is surfaced before implementation.
- Concurrent compounds do not edit one shared data file.

## Verification

- `python -m pytest tests/test_closure_gate.py tests/test_compound_cadence_gate.py tests/test_compound_cadence_obligation.py -q`

## Handoff

Provide a repeat-defect fixture showing create, retrieve, and closeout enforcement.

## Stop Boundary

Stop before bulk-rewriting historical compound logs.
