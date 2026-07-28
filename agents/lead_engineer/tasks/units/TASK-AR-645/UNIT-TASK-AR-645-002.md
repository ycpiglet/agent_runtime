---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-645-002
work_uid: 59b89d59-21b0-43ba-b82f-0604e2543614
kind: unit
parent_id: TASK-AR-645
unit_id: UNIT-TASK-AR-645-002
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
summary: Add configurable scribe state adapters and generated projections
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: scribe_due assumes a lead-engineer STATUS file and one Korean heading, so Bean Wiki BACKLOG and Allimbot PROJECT_STATUS cannot participate reliably.
inputs:
  - scripts/scribe_due.py
  - src/agent_runtime/templates/project/scripts/scribe_due.py
  - Bean Wiki BACKLOG and Allimbot PROJECT_STATUS conventions
target_files:
  - scripts/scribe_due.py
  - src/agent_runtime/templates/project/scripts/scribe_due.py
  - src/agent_runtime/config.py
  - tests/test_doc_steward_due.py
  - tests/test_doctor.py
scope: Read configured host state sources, compute scribe due status, and emit generated summaries without taking ownership of host canonical files.
acceptance:
  - No exact Korean heading is required.
  - Missing optional host status degrades visibly.
  - Substantial closeout can enforce overdue scribe while mini tasks remain lightweight.
verification:
  - python -m pytest tests/test_doc_steward_due.py tests/test_doctor.py -q
handoff: Provide adapter examples for runtime, Bean Wiki, Allimbot, and Autofolio.
stop_condition: Stop before changing host status files during read-only doctor or session start.
---

# UNIT-TASK-AR-645-002 - Add configurable scribe state adapters and generated projections

## Context

scribe_due assumes a lead-engineer STATUS file and one Korean heading, so Bean Wiki BACKLOG and Allimbot PROJECT_STATUS cannot participate reliably.

## Inputs

- scripts/scribe_due.py
- src/agent_runtime/templates/project/scripts/scribe_due.py
- Bean Wiki BACKLOG and Allimbot PROJECT_STATUS conventions

## Target Files

- scripts/scribe_due.py
- src/agent_runtime/templates/project/scripts/scribe_due.py
- src/agent_runtime/config.py
- tests/test_doc_steward_due.py
- tests/test_doctor.py

## Scope

Read configured host state sources, compute scribe due status, and emit generated summaries without taking ownership of host canonical files.

## Steps

1. Define state source and projection config.
2. Support structured and markdown adapters.
3. Report due/block policy by work size.
4. Test Bean Wiki and Allimbot fixture layouts.

## Acceptance Criteria

- No exact Korean heading is required.
- Missing optional host status degrades visibly.
- Substantial closeout can enforce overdue scribe while mini tasks remain lightweight.

## Verification

- `python -m pytest tests/test_doc_steward_due.py tests/test_doctor.py -q`

## Handoff

Provide adapter examples for runtime, Bean Wiki, Allimbot, and Autofolio.

## Stop Boundary

Stop before changing host status files during read-only doctor or session start.
