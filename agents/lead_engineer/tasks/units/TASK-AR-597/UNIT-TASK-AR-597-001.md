---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-597-001
work_uid: 7c9a5e1d-abc0-424a-b19d-73b7c7d41480
kind: unit
parent_id: TASK-AR-597
unit_id: UNIT-TASK-AR-597-001
task_id: TASK-AR-597
task_set_id: TASKSET-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION
initiative_id: INIT-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-06-21T19:25:00+09:00
updated_at: 2026-06-21T19:25:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Draft sales revenue readiness packet
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: This unit publishes a standardized sales-readiness packet under Sales-Revenue in WORK-LANE-PLAYBOOKS.
inputs:
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
target_files:
  - agents/project/WORK-LANE-PLAYBOOKS.md
scope: Docs only: sales readiness draft packet and approval boundaries.
acceptance:
  - Sales lane packet is present and explicitly marked draft-only.
  - Scope-out includes no CRM/proposal commitment actions.
  - Task and unit evidence commands are deterministic and measurable.
verification:
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION --check
  - python scripts/task_identity.py check --check
handoff: Report sales packet location, ownership, and verified evidence.
stop_condition: Stop after sales packet draft and closeout evidence links are ready for owner review.
---

# UNIT-TASK-AR-597-001 - Draft sales revenue readiness packet

## Context

This unit publishes a standardized sales-readiness packet under Sales-Revenue in WORK-LANE-PLAYBOOKS.

## Inputs

- agents/project/WORK-LANE-PLAYBOOKS.md
- agents/project/BUSINESS-OPERATING-SYSTEM.md

## Target Files

- agents/project/WORK-LANE-PLAYBOOKS.md

## Scope

Docs only: sales readiness draft packet and approval boundaries.

## Steps

1. Draft sales readiness packet with scope/out of scope and draft-only ownership.
2. Add ICP and qualification schema plus lead-handoff checklist fields.
3. Define decision trigger for outbound/proposal/partnership escalation.

## Acceptance Criteria

- Sales lane packet is present and explicitly marked draft-only.
- Scope-out includes no CRM/proposal commitment actions.
- Task and unit evidence commands are deterministic and measurable.

## Verification

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION --check`
- `python scripts/task_identity.py check --check`

## Handoff

Report sales packet location, ownership, and verified evidence.

## Stop Boundary

Stop after sales packet draft and closeout evidence links are ready for owner review.
