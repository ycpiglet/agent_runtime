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
verification_status: pending
owner: lead-engineer
created_at: 2026-07-22T18:26:18+09:00
updated_at: 2026-07-22T18:26:18+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
created_by: codex-root-planner
summary: Fold the legacy failure link into canonical evidence refs
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - ci
context: PR #303 CI reproduced the same unknown-field failure on Python 3.10, 3.11, and 3.12. The referenced failed verification JSON must remain discoverable.
inputs:
  - reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
  - agents/lead_engineer/tasks/TASK-AR-594.md
target_files:
  - agents/lead_engineer/tasks/TASK-AR-594.md
scope: Normalize only the legacy evidence-reference field. Do not modify TASK-AR-594 implementation, verification payloads, or the global schema.
acceptance:
  - The canonical record links all three TASK-AR-594 verification evidence files.
  - No unknown frontmatter field remains.
  - The CI failure is locally unreproducible after the change.
verification:
  - python scripts/taskset_work_gate.py --check
  - python scripts/owner_governance_gate.py --allow-empty-owner-docs
handoff: Report the original CI finding, preserved failed evidence path, local gate results, and PR rerun outcome.
stop_condition: Stop before changing the global work-item schema or deleting any verification evidence.
---

# UNIT-TASK-AR-610-001 - Fold the legacy failure link into canonical evidence refs

## Context

PR #303 CI reproduced the same unknown-field failure on Python 3.10, 3.11, and 3.12. The referenced failed verification JSON must remain discoverable.

## Inputs

- reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
- agents/lead_engineer/tasks/TASK-AR-594.md

## Target Files

- agents/lead_engineer/tasks/TASK-AR-594.md

## Scope

Normalize only the legacy evidence-reference field. Do not modify TASK-AR-594 implementation, verification payloads, or the global schema.

## Steps

1. Confirm the unknown-field failure against the PR head.
2. Move the failed verification path into canonical evidence_refs without deleting the evidence file.
3. Run taskset work and Owner governance gates.

## Acceptance Criteria

- The canonical record links all three TASK-AR-594 verification evidence files.
- No unknown frontmatter field remains.
- The CI failure is locally unreproducible after the change.

## Verification

- `python scripts/taskset_work_gate.py --check`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`

## Handoff

Report the original CI finding, preserved failed evidence path, local gate results, and PR rerun outcome.

## Stop Boundary

Stop before changing the global work-item schema or deleting any verification evidence.
