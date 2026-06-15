---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-372
work_uid: 42f1d67e-cc39-4d0e-ad0c-bf1c16961faa
kind: task
parent_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
origin_type: planning_proposal
origin_ref: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
created_by: planner
id: TASK-AR-372
display_id: TASK-AR-372
task_uid: 42f1d67e-cc39-4d0e-ad0c-bf1c16961faa
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
title: Registration CLI/API for initiative, taskset, task, and unit records
started_at: 2026-06-12T11:58:44+09:00
updated_at: 2026-06-15T12:01:39+09:00
status: completed
resolution: done
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
completed_at: 2026-06-15T12:01:39+09:00
verification_status: passed
review_refs:
  - reviews/W4B-2026-06-15-TASK-AR-371-374.md
  - reviews/REVIEW-2026-06-15-work-hierarchy-conflict-closure-closeout.md
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
- Timestamp metadata can be produced from a single canonical root script and the Work CLI surface.
- Verification commands can be executed through the Work CLI and recorded as evidence.
- The command is idempotent or reports exact existing-record conflicts.
- Tests cover missing required fields, duplicate display IDs, and partial failure cleanup.

## Verification

- Focused unit tests for the registration command.
- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --write`
- `python scripts/work_item_classifier.py --check`
- `python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --require-ready --check`
- `python scripts/now.py --utc`
- `python scripts/work.py now --utc`
- `python scripts/work.py verify UNIT-TASK-AR-372-005 --json`
- `python scripts/work.py verify UNIT-TASK-AR-372-006 --json`
- `python scripts/work.py close UNIT-TASK-AR-372-006 --actual-hours <hours> --actual-tokens <tokens> --json`
- `python scripts/work.py criteria UNIT-TASK-AR-372-007 --json`
- `python scripts/work.py verify UNIT-TASK-AR-372-007 --json`
- `python scripts/work.py close UNIT-TASK-AR-372-007 --actual-hours <hours> --actual-tokens <tokens> --json`
- `python scripts/work.py assign UNIT-TASK-AR-372-008 --json`
- `python scripts/work.py verify UNIT-TASK-AR-372-008 --json`
- `python scripts/work.py close UNIT-TASK-AR-372-008 --actual-hours <hours> --actual-tokens <tokens> --json`
- `python scripts/work.py split TASK-AR-372 --json`
- `python scripts/work.py verify UNIT-TASK-AR-372-009 --json`
- `python scripts/work.py close UNIT-TASK-AR-372-009 --actual-hours <hours> --actual-tokens <tokens> --json`
- `python scripts/backlog_board.py --write`
- `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`

## Handoff

- Report command syntax, input schema, generated files, and any intentional manual steps that remain.

## Units

- `UNIT-TASK-AR-372-001` completed: Established `WORK-SCHEMA.yml` as the field dictionary SSoT and added a deterministic schema gate before full registration CLI/API work.
- `UNIT-TASK-AR-372-002` completed: Added `scripts/work.py new --input <json>` for deterministic initiative/taskset/task/review registration using the reservation ledger.
- `UNIT-TASK-AR-372-003` completed: Extended `scripts/work.py new --input <json>` to create optional worker-ready unit specs from `tasks[].units[]` input and verify them with the readiness gate.
- `UNIT-TASK-AR-372-004` completed: Restored root `scripts/now.py` and added `scripts/work.py now` as the canonical timestamp surface for generated metadata.
- `UNIT-TASK-AR-372-005` completed: Added `scripts/work.py verify <id>` to execute declared verification commands, write JSON evidence, update verification metadata, and refresh the evidence index.
- `UNIT-TASK-AR-372-006` completed: Added `scripts/work.py close <id>` to require passed evidence, record actuals/resolution metadata, generate a closeout block, and refresh generated views.
- `UNIT-TASK-AR-372-007` completed: Added `scripts/work.py criteria <id>` to evaluate acceptance-to-verification coverage and write B-mode proposal records for gaps without mutating source work items.
- `UNIT-TASK-AR-372-008` completed: Added `scripts/work.py assign <id>` to recommend team/owner metadata and write B-mode proposal records for assignment gaps without mutating source work items or creating claims.
- `UNIT-TASK-AR-372-009` completed: Added `scripts/work.py split <task>` to propose worker-ready unit specs for unsplit tasks without creating canonical unit files or reserving IDs.
- Remaining: approved apply behavior, automatic dispatch, and Work Explorer UI belong in separate records.

