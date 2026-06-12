---
id: TASK-AR-372
display_id: TASK-AR-372
task_uid: 42f1d67e-cc39-4d0e-ad0c-bf1c16961faa
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
title: Registration CLI/API for initiative, taskset, task, and unit records
started_at: 2026-06-12T11:58:44+09:00
updated_at: 2026-06-12T12:45:18+09:00
status: in_progress
priority: P1
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
  - data_integrity
  - repeated_failure
tags:
  - cli
  - registration
  - automation
---

# TASK-AR-372 - Registration CLI/API for initiative, taskset, task, and unit records

## Goal

- Provide one structured registration command path so planners stop hand-editing board definitions, backlog sections, task files, owner-doc manifests, evidence pointers, and human-facing ordinal numbers independently.

## Scope

- Add a planner-facing command or API that can create/update initiative, taskset plan, task records, and optional worker-ready unit specs from a structured input file.
- The command should create stable records first; `scripts/work_item_classifier.py` assigns readable hierarchy numbers afterward.
- Integrate the task ID reservation allocator from `TASK-AR-370`.
- Update board taskset definitions and generated backlog surfaces consistently.
- Emit a registration review/evidence record and update the owner-doc manifest when the output is Owner-facing.
- Refuse unsafe partial writes when required fields or reservations are missing.

## Out Of Scope

- Auto-approving external, destructive, or production-impacting work.
- Replacing planner judgment with fully automatic task decomposition.
- Bulk migrating every old task in the same change.

## Acceptance Criteria

- A sample structured input creates an initiative, taskset plan, two task files, and a registration review in one repeatable command.
- The structured input can optionally create worker-ready unit specs that pass the readiness gate.
- The command is idempotent or reports exact existing-record conflicts.
- Tests cover missing required fields, duplicate display IDs, and partial failure cleanup.

## Verification

- Focused unit tests for the registration command.
- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --write`
- `python scripts/work_item_classifier.py --check`
- `python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --require-ready --check`
- `python scripts/backlog_board.py --write`
- `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`

## Handoff

- Report command syntax, input schema, generated files, and any intentional manual steps that remain.

## Units

- `UNIT-TASK-AR-372-001` completed: Established `WORK-SCHEMA.yml` as the field dictionary SSoT and added a deterministic schema gate before full registration CLI/API work.
- `UNIT-TASK-AR-372-002` completed: Added `scripts/work.py new --input <json>` for deterministic initiative/taskset/task/review registration using the reservation ledger.
- `UNIT-TASK-AR-372-003` completed: Extended `scripts/work.py new --input <json>` to create optional worker-ready unit specs from `tasks[].units[]` input and verify them with the readiness gate.
- Remaining: add `work close` and `work verify`, then B-mode proposal-gated AI split/criteria/assign behavior.

