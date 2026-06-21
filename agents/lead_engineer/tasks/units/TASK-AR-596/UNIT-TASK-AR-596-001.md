---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-596-001
work_uid: 09ea6273-0872-405b-93e8-460909ff1c87
kind: unit
parent_id: TASK-AR-596
unit_id: UNIT-TASK-AR-596-001
task_id: TASK-AR-596
task_set_id: TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
initiative_id: INIT-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-21T19:00:00+09:00
updated_at: 2026-06-21T18:50:46+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Draft marketing growth campaign-readiness packet
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: This unit publishes a markdown packet in WORK-LANE-PLAYBOOKS that standardizes campaign-readiness structure and marketing decision gates.
inputs:
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
target_files:
  - agents/project/WORK-LANE-PLAYBOOKS.md
scope: Docs only: marketing campaign-readiness packet draft and approval boundaries.
acceptance:
  - Marketing growth packet is present and explicitly marked draft-only.
  - Scope-out boundaries include external campaign execution restrictions.
  - Task and unit evidence commands are deterministic and measurable.
verification:
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION --check
  - python scripts/task_identity.py check --check
handoff: Report marketing readiness draft packet location, approval triggers, and verified evidence.
stop_condition: Stop after marketing packet draft and closeout evidence links are ready for owner review.
verified_at: 2026-06-21T18:50:33+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-06-21-unit-task-ar-596-001-20260621184917.json
  - reviews/VERIFY-2026-06-21-unit-task-ar-596-001-20260621185033.json
  - reviews/VERIFY-2026-06-21-unit-task-ar-596-001-20260621185033.json
resolution: done
completed_at: 2026-06-21T18:50:46+09:00
closed_by: work.py close
actual_hours: 2
actual_tokens: 3200
---

# UNIT-TASK-AR-596-001 - Draft marketing growth campaign-readiness packet

## Context

This unit publishes a markdown packet in WORK-LANE-PLAYBOOKS that standardizes campaign-readiness structure and marketing decision gates.

## Inputs

- agents/project/WORK-LANE-PLAYBOOKS.md
- agents/project/BUSINESS-OPERATING-SYSTEM.md

## Target Files

- agents/project/WORK-LANE-PLAYBOOKS.md

## Scope

Docs only: marketing campaign-readiness packet draft and approval boundaries.

## Steps

1. Draft a marketing evidence packet section under Marketing-Growth with packet schema and draft-only fields.
2. Add explicit constraints for channel activity, messaging hygiene, and approval owner.
3. Define decision triggers for campaign execution and external partner/channel escalation.
4. Record W4 verification commands and evidence references.

## Acceptance Criteria

- Marketing growth packet is present and explicitly marked draft-only.
- Scope-out boundaries include external campaign execution restrictions.
- Task and unit evidence commands are deterministic and measurable.

## Verification

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION --check`
- `python scripts/task_identity.py check --check`

## Handoff

Report marketing readiness draft packet location, approval triggers, and verified evidence.

## Stop Boundary

Stop after marketing packet draft and closeout evidence links are ready for owner review.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-21T18:50:46+09:00`
- Resolution: `done`
- Actual hours: `2`
- Actual tokens: `3200`
- Closed by: `work.py close`
- Evidence:
  - `reviews/VERIFY-2026-06-21-unit-task-ar-596-001-20260621184917.json`
  - `reviews/VERIFY-2026-06-21-unit-task-ar-596-001-20260621185033.json`
  - `reviews/VERIFY-2026-06-21-unit-task-ar-596-001-20260621185033.json`
<!-- work-close:end -->
