---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-610-001
work_uid: c1624cb5-b955-471e-bcc7-27c0ea598a84
kind: unit
parent_id: TASK-AR-610
unit_id: UNIT-TASK-AR-610-001
task_id: TASK-AR-610
task_set_id: TASKSET-AR-PR303-CI-SCHEMA-RECOVERY
initiative_id: INIT-AR-PR303-CI-SCHEMA-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead-engineer
created_at: 2026-07-22T18:26:18+09:00
updated_at: 2026-07-22T18:35:57+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
created_by: codex-root-planner
summary: Normalize legacy closeout evidence metadata
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - ci
context: PR
inputs:
  - reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
  - agents/lead_engineer/tasks/TASK-AR-594.md
target_files:
  - agents/lead_engineer/tasks/TASK-AR-594.md
  - agents/lead_engineer/tasks/TASK-AR-595.md
  - agents/lead_engineer/tasks/TASK-AR-596.md
  - agents/lead_engineer/tasks/TASK-AR-597.md
  - agents/lead_engineer/tasks/TASK-AR-598.md
  - agents/lead_engineer/tasks/TASK-AR-601.md
  - agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md
  - agents/lead_engineer/tasks/units/TASK-AR-597/UNIT-TASK-AR-597-001.md
  - agents/lead_engineer/tasks/units/TASK-AR-598/UNIT-TASK-AR-598-001.md
scope: Normalize only legacy closeout evidence metadata in the declared records. Do not modify implementation, verification payloads, referenced evidence, or the global schema.
acceptance:
  - The canonical record links all three TASK-AR-594 verification evidence files.
  - All review evidence paths and closeout commit/status values remain discoverable.
  - No unknown frontmatter field remains in the declared records.
  - The CI failure is locally unreproducible after the change.
verification:
  - python scripts/taskset_work_gate.py --check
  - python scripts/rbac_write_gate.py --check
  - python scripts/owner_governance_gate.py --allow-empty-owner-docs
handoff: Report the original CI finding, preserved failed evidence path, local gate results, and PR rerun outcome.
stop_condition: Stop before changing the global work-item schema or deleting any verification evidence.
verified_at: 2026-07-22T18:35:57+09:00
verified_by: codex-root-task-ar-610
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-610-001-20260722183557.json
---

# UNIT-TASK-AR-610-001 - Normalize legacy closeout evidence metadata

## Context

PR #303 CI reproduced the same unknown-field failure on Python 3.10, 3.11, and 3.12. The referenced failed verification JSON must remain discoverable.

## Inputs

- reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
- agents/lead_engineer/tasks/TASK-AR-594.md

## Target Files

- agents/lead_engineer/tasks/TASK-AR-594.md
- agents/lead_engineer/tasks/TASK-AR-595.md
- agents/lead_engineer/tasks/TASK-AR-596.md
- agents/lead_engineer/tasks/TASK-AR-597.md
- agents/lead_engineer/tasks/TASK-AR-598.md
- agents/lead_engineer/tasks/TASK-AR-601.md
- agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md
- agents/lead_engineer/tasks/units/TASK-AR-597/UNIT-TASK-AR-597-001.md
- agents/lead_engineer/tasks/units/TASK-AR-598/UNIT-TASK-AR-598-001.md

## Scope

Normalize only legacy closeout evidence metadata in the declared records. Do not modify implementation, verification payloads, referenced evidence, or the global schema.

## Steps

1. Confirm the unknown-field failure against the PR head.
2. Move review evidence into canonical evidence_refs and preserve commit/status values in Markdown.
3. Run taskset work, RBAC write, and Owner governance gates.

## Acceptance Criteria

- The canonical record links all three TASK-AR-594 verification evidence files.
- All review evidence paths and closeout commit/status values remain discoverable.
- No unknown frontmatter field remains in the declared records.
- The CI failure is locally unreproducible after the change.

## Verification

- `python scripts/taskset_work_gate.py --check`
- `python scripts/rbac_write_gate.py --check`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`

## Handoff

Report the original CI finding, preserved failed evidence path, local gate results, and PR rerun outcome.

## Stop Boundary

Stop before changing the global work-item schema or deleting any verification evidence.