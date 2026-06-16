---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-572
display_id: TASK-AR-572
task_uid: d5f5d125-a5e9-4565-b027-d2b89f0c00be
work_id: TASK-AR-572
work_uid: d5f5d125-a5e9-4565-b027-d2b89f0c00be
kind: task
parent_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
registered_at: 2026-06-17T08:31:23+09:00
created_at: 2026-06-17T08:31:23+09:00
updated_at: 2026-06-17T08:31:23+09:00
title: Publish maturity thresholds and improvement report
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 2000
owner: lead_engineer
initiative_id: INIT-AR-SELF-IMPROVEMENT-CADENCE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-572/UNIT-TASK-AR-572-001.md
reservation_id: RES-20260617-083123-3d6cedc9-03
origin_type: owner_request
origin_ref: owner-request:low-frequency-agent-skill-self-improvement-cycle
created_by: codex-planner
summary: Define measurable maturity criteria for low-frequency agent/skill self-improvement and integrate the report with governance closeout surfaces.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-572 - Publish maturity thresholds and improvement report

## Goal

- Define measurable maturity criteria for low-frequency agent/skill self-improvement and integrate the report with governance closeout surfaces.

## Scope

- Define measurable maturity criteria for low-frequency agent/skill self-improvement and integrate the report with governance closeout surfaces.

## Acceptance Criteria

- The report defines numeric score inputs and maturity thresholds for immature, improving, and mature cycles.
- The next-session pointer and board make the remaining cycle work discoverable.
- Verification evidence proves whether the objective is complete or still active.

## Verification

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-SELF-IMPROVEMENT-CADENCE --check`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/owner_governance_gate.py`
