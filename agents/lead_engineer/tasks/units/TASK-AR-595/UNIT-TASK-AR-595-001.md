---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-595-001
work_uid: 541ce623-97f5-4f99-80f9-b50882fd57ca
kind: unit
parent_id: TASK-AR-595
unit_id: UNIT-TASK-AR-595-001
task_id: TASK-AR-595
task_set_id: TASKSET-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION
initiative_id: INIT-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-21T18:30:00+09:00
updated_at: 2026-06-21T18:44:36+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Draft finance policy evidence packet
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: This unit creates draft finance-accounting evidence artifacts from the lane playbook: pricing assumptions, cost evidence draft, and decision trigger matrix.
inputs:
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
target_files:
  - agents/project/WORK-LANE-PLAYBOOKS.md
scope: Docs only: finance evidence packet draft and boundary controls.
acceptance:
  - Finance lane draft packet is present and explicitly marked draft-only.
  - Boundary constraints and approval triggers are explicit.
  - Task and unit evidence requirements are measurable via executable commands.
verification:
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION --check
  - python scripts/task_identity.py check --check
handoff: Report finance draft packet location, approval triggers, and verified evidence.
stop_condition: Stop after finance evidence packet draft and closeout evidence links are ready for owner review.
verified_at: 2026-06-21T18:44:22+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-06-21-unit-task-ar-595-001-20260621183536.json
  - reviews/VERIFY-2026-06-21-unit-task-ar-595-001-20260621184040.json
  - reviews/VERIFY-2026-06-21-unit-task-ar-595-001-20260621184422.json
resolution: done
completed_at: 2026-06-21T18:44:36+09:00
closed_by: work.py close
actual_hours: 1.8
actual_tokens: 6800
---

# UNIT-TASK-AR-595-001 - Draft finance policy evidence packet

## Context

This unit creates draft finance-accounting evidence artifacts from the lane playbook: pricing assumptions, cost evidence draft, and decision trigger matrix.

## Inputs

- agents/project/WORK-LANE-PLAYBOOKS.md
- agents/project/BUSINESS-OPERATING-SYSTEM.md

## Target Files

- agents/project/WORK-LANE-PLAYBOOKS.md

## Scope

Docs only: finance evidence packet draft and boundary controls.

## Steps

1. Draft the finance policy evidence artifacts in `agents/project/WORK-LANE-PLAYBOOKS.md` under a finance lane subsection.
2. Add explicit draft/verified fields for pricing assumption, margin guardrails, and cost capture scope.
3. List required owner approvals and external-effect boundaries for pricing/cost changes.
4. Add taskset closeout evidence commands and generate verification records.

## Acceptance Criteria

- Finance lane draft packet is present and explicitly marked draft-only.
- Boundary constraints and approval triggers are explicit.
- Task and unit evidence requirements are measurable via executable commands.

## Verification

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION --check`
- `python scripts/task_identity.py check --check`

## Handoff

Report finance draft packet location, approval triggers, and verified evidence.

## Stop Boundary

Stop after finance evidence packet draft and closeout evidence links are ready for owner review.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-21T18:44:36+09:00`
- Resolution: `done`
- Actual hours: `1.8`
- Actual tokens: `6800`
- Closed by: `work.py close`
- Evidence:
  - `reviews/VERIFY-2026-06-21-unit-task-ar-595-001-20260621183536.json`
  - `reviews/VERIFY-2026-06-21-unit-task-ar-595-001-20260621184040.json`
  - `reviews/VERIFY-2026-06-21-unit-task-ar-595-001-20260621184422.json`
<!-- work-close:end -->