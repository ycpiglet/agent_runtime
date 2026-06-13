---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-374
work_uid: e08dd19a-3998-44ff-8b16-4a1eaa7c4ccf
kind: task
parent_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
origin_type: planning_proposal
origin_ref: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
created_by: planner
id: TASK-AR-374
display_id: TASK-AR-374
task_uid: e08dd19a-3998-44ff-8b16-4a1eaa7c4ccf
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
updated_at: 2026-06-12T08:17:54+09:00
title: Conflict-surface verification and closeout gate
status: planned
priority: P3
difficulty: S
est_hours: 8
est_tokens: 4000
owner: lead_engineer
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - verification
  - cross_cutting
tags:
  - verification
  - closeout
  - conflict
---

# TASK-AR-374 - Conflict-surface verification and closeout gate

## Goal

- Prove that the work hierarchy and registration conflict surfaces are actually closed before marking the taskset complete.

## Scope

- Add or update a named verification wrapper for `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE`.
- Run task identity, taskset work, backlog/board generation, owner-doc format, evidence index, and registration conflict gates.
- Record an Owner-facing closeout review that separates local verification from external publish/CI evidence.
- Confirm the next-session pointer either remains intentionally unchanged or is updated with a precise new ready lane.

## Out Of Scope

- Pushing commits, opening PRs, or publishing remote evidence.
- Closing unrelated tasksets.
- Claiming implementation success without running the final gates.

## Acceptance Criteria

- All `TASK-AR-369` through `TASK-AR-373` are complete or explicitly waived with owner-facing rationale.
- The named closeout command exits zero and records evidence.
- The final review states whether any shared-registration conflict surface remains.

## Verification

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE --require-complete --check`
- `python scripts/task_identity.py check --check`
- `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`
- `python scripts/evidence_index_generator.py --check`

## Handoff

- Report final gate output, changed files, remaining risks, and the exact prompt vocabulary Owner should use next.
