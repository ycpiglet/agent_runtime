---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-594-001
work_uid: f3f8e419-9f07-48fc-8153-bf1612ebd30a
kind: unit
parent_id: TASK-AR-594
unit_id: UNIT-TASK-AR-594-001
task_id: TASK-AR-594
task_set_id: TASKSET-AR-BUSINESS-LANE-PLAYBOOKS
initiative_id: INIT-AR-BUSINESS-LANES
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-21T17:45:39+09:00
updated_at: 2026-06-21T18:21:50+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Draft and mirror business lane playbook packet
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The objective is to move from team registration to repeatable, execution-ready lane playbooks. This unit creates the packet, lane-specific operating docs, and review-compatibility links used by planning/strategy, ops/support, finance, marketing, and sales teams.
inputs:
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - src/agent_runtime/templates/project/agents/project/BUSINESS-OPERATING-SYSTEM.md
  - src/agent_runtime/templates/project/agents/project/WORK-LANE-PLAYBOOKS.md
  - agents/project/ORG.md
  - agents/project/TEAMS.md
  - agents/project/PROJECT-CONTEXT.yml
target_files:
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - src/agent_runtime/templates/project/agents/project/BUSINESS-OPERATING-SYSTEM.md
  - src/agent_runtime/templates/project/agents/project/WORK-LANE-PLAYBOOKS.md
scope: Docs only: operational playbook content and template mirrors. No external system writes.
acceptance:
  - work lane playbook includes 5 business lanes with explicit roles, outputs, and safety constraints.
  - BUSINESS-OPERATING-SYSTEM.md (live and template) links the new lane packet.
  - taskset evidence path remains valid after verification and release records are written.
verification:
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANE-PLAYBOOKS --check
  - python scripts/task_identity.py check --check
handoff: Provide links to lane playbook packet, boundary controls, and verification evidence for this unit.
stop_condition: Stop when lane playbooks and mirror packet are complete, cycle-artifact links are present, and no safety boundary is broadened.
verified_at: 2026-06-21T18:20:53+09:00
verified_by: independent-verifier-biz
resolution: done
closed_by: lead-engineer-business-lanes
evidence_refs:
  - reviews/VERIFY-2026-06-21-unit-task-ar-594-001-20260621182053.json
completed_at: 2026-06-21T18:21:50+09:00
actual_hours: 1.9
actual_tokens: 4700
actual_difficulty: M
---

# UNIT-TASK-AR-594-001 - Draft and mirror business lane playbook packet

## Context

The objective is to move from team registration to repeatable, execution-ready lane playbooks. This unit creates the packet, lane-specific operating docs, and review-compatibility links used by planning/strategy, ops/support, finance, marketing, and sales teams.

## Inputs

- agents/project/BUSINESS-OPERATING-SYSTEM.md
- agents/project/WORK-LANE-PLAYBOOKS.md
- src/agent_runtime/templates/project/agents/project/BUSINESS-OPERATING-SYSTEM.md
- src/agent_runtime/templates/project/agents/project/WORK-LANE-PLAYBOOKS.md
- agents/project/ORG.md
- agents/project/TEAMS.md
- agents/project/PROJECT-CONTEXT.yml

## Target Files

- agents/project/BUSINESS-OPERATING-SYSTEM.md
- agents/project/WORK-LANE-PLAYBOOKS.md
- src/agent_runtime/templates/project/agents/project/BUSINESS-OPERATING-SYSTEM.md
- src/agent_runtime/templates/project/agents/project/WORK-LANE-PLAYBOOKS.md

## Scope

Docs only: operational playbook content and template mirrors. No external system writes.

## Steps

1. Add `agents/project/WORK-LANE-PLAYBOOKS.md` with concrete operating templates for finance-accounting, marketing-growth, sales-revenue, operations-support, and planning-strategy.
2. Add lane execution contracts: inputs, outputs, cadence, artifact set, and decision triggers.
3. Update BUSINESS-OPERATING-SYSTEM.md and template mirror to link the new lane playbook packet.
4. Update target files to keep lane packet as SSoT evidence before release and closeout evidence collection.
5. Run taskset_work_gate and task_identity as verification evidence.

## Acceptance Criteria

- work lane playbook includes 5 business lanes with explicit roles, outputs, and safety constraints.
- BUSINESS-OPERATING-SYSTEM.md (live and template) links the new lane packet.
- taskset evidence path remains valid after verification and release records are written.

## Verification

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-LANE-PLAYBOOKS --check`
- `python scripts/task_identity.py check --check`

## Handoff

Provide links to lane playbook packet, boundary controls, and verification evidence for this unit.

## Stop Boundary

Stop when lane playbooks and mirror packet are complete, cycle-artifact links are present, and no safety boundary is broadened.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-21T18:21:50+09:00`
- Resolution: `done`
- Actual hours: `1.9`
- Actual tokens: `4700`
- Closed by: `lead-engineer-business-lanes`
- Evidence:
  - `reviews/VERIFY-2026-06-21-unit-task-ar-594-001-20260621182053.json`
<!-- work-close:end -->
