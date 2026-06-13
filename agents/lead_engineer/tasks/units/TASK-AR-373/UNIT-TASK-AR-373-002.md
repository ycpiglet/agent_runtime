---
unit_id: UNIT-TASK-AR-373-002
task_id: TASK-AR-373
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: worker_ready
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity]
depends_on:
  - UNIT-TASK-AR-373-001
context: "Once the classifier exists, surface the migration queue as an owner-doc and guard low-tier dispatch."
inputs:
  - scripts/unit_readiness_report.py
target_files:
  - reviews/UNIT-READINESS-MIGRATION-REPORT.md
  - scripts/task_claim_dispatcher.py
scope: "Generate the owner-facing report and add a dispatcher readiness guard. Depends on UNIT-001."
acceptance:
  - "Report lists planner_refine_required tasks with next-action links."
verification:
  - "python scripts/owner_doc_format_gate.py --manifest owner-docs.yml"
handoff: "Report migration queue size and dispatcher guard behavior."
stop_condition: "Stop after this unit."
---

# UNIT-TASK-AR-373-002 — migration report + dispatcher readiness guard

## Context
- The classifier output must reach owners and prevent low-tier dispatch to unready tasks.

## Inputs
- scripts/unit_readiness_report.py (from UNIT-001)
- agents/project/WORK-MODEL-2.0.md

## Target Files
- reviews/UNIT-READINESS-MIGRATION-REPORT.md
- scripts/task_claim_dispatcher.py

## Scope
- Generate the owner-doc migration report from the UNIT-001 classifier; add a dispatcher guard that warns (not blocks historical) when a worker_low claim targets a planner_refine_required task.

## Steps
- Wire unit_readiness_report --write to emit the owner-doc; add the low-tier guard in the claim create path; register the report in owner-docs.

## Acceptance Criteria
- reviews/UNIT-READINESS-MIGRATION-REPORT.md lists planner_refine_required tasks with next-action links.
- Dispatcher warns on low-tier claim against an unready task; completed/historical tasks unaffected.

## Verification
- `python scripts/unit_readiness_report.py --write reviews/UNIT-READINESS-MIGRATION-REPORT.md`
- `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`

## Handoff
- Report the migration queue size and the dispatcher guard behavior.

## Stop Boundary
- Stop after this unit; do not begin migrating individual tasks.
