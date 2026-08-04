---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-651-001
work_uid: 1cb9de8c-8f98-401a-876a-a92d85d2a100
kind: unit
parent_id: TASK-AR-651
unit_id: UNIT-TASK-AR-651-001
task_id: TASK-AR-651
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-30T11:25:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Assemble and verify the v0.8.0-rc.1 release candidate
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The current package reports v0.7.0 while README examples still pin v0.1.8, and local tag discovery can use stale refs. The open v0.8 release issue predates the adoption/enforcement pilot evidence. Autofolio attempt 3 passed the migration contract but exposed six release-critical operability gaps tracked by TASK-AR-652 through TASK-AR-657.
inputs:
  - pyproject.toml
  - src/agent_runtime/__init__.py
  - README.md
  - README.ko.md
  - release and pilot evidence
target_files:
  - pyproject.toml
  - src/agent_runtime/__init__.py
  - README.md
  - README.ko.md
  - CHANGELOG.md
  - agents/lead_engineer/tasks/TASK-AR-652.md
  - agents/lead_engineer/tasks/TASK-AR-653.md
  - agents/lead_engineer/tasks/TASK-AR-654.md
  - agents/lead_engineer/tasks/TASK-AR-655.md
  - agents/lead_engineer/tasks/TASK-AR-656.md
  - agents/lead_engineer/tasks/TASK-AR-657.md
  - scripts/release_cadence_trigger.py
  - scripts/release_version_cascade.py
  - tests/test_release_cadence_trigger.py
  - tests/test_release_version_cascade.py
  - reviews/RELEASE-READINESS-v0.8.0-rc.1.md
scope: Prepare and verify an RC commit and release plan. Final tag push and GitHub Release remain Owner-gated.
acceptance:
  - No stale version or tag reference remains.
  - All mandatory release evidence is exact-SHA linked, including closed TASK-AR-652 through TASK-AR-657.
  - Skipped browser exploration is not accepted for RC.
  - No final release is published without explicit Owner approval.
verification:
  - python -m pytest tests -q
  - RUN_BETA_EXPLORATION=1 python -m pytest tests/test_ui_console_beta_exploration.py -q
  - python scripts/release_execution_gate.py --check
handoff: Provide the exact candidate SHA, install commands, evidence matrix, rollback plan, and remaining Owner decision.
stop_condition: Stop before final tag push, GitHub Release publication, or closing the release approval issue.
---

# UNIT-TASK-AR-651-001 - Assemble and verify the v0.8.0-rc.1 release candidate

## Context

The current package reports v0.7.0 while README examples still pin v0.1.8, and local tag discovery can use stale refs. The open v0.8 release issue predates the adoption/enforcement pilot evidence. Autofolio attempt 3 passed the migration contract but exposed six release-critical operability gaps tracked by TASK-AR-652 through TASK-AR-657.

## Inputs

- pyproject.toml
- src/agent_runtime/__init__.py
- README.md
- README.ko.md
- release and pilot evidence

## Target Files

- pyproject.toml
- src/agent_runtime/__init__.py
- README.md
- README.ko.md
- CHANGELOG.md
- agents/lead_engineer/tasks/TASK-AR-652.md
- agents/lead_engineer/tasks/TASK-AR-653.md
- agents/lead_engineer/tasks/TASK-AR-654.md
- agents/lead_engineer/tasks/TASK-AR-655.md
- agents/lead_engineer/tasks/TASK-AR-656.md
- agents/lead_engineer/tasks/TASK-AR-657.md
- scripts/release_cadence_trigger.py
- scripts/release_version_cascade.py
- tests/test_release_cadence_trigger.py
- tests/test_release_version_cascade.py
- reviews/RELEASE-READINESS-v0.8.0-rc.1.md

## Scope

Prepare and verify an RC commit and release plan only after TASK-AR-652 through TASK-AR-657 close. Final tag push and GitHub Release remain Owner-gated.

## Steps

1. Verify TASK-AR-652 through TASK-AR-657 are closed with exact evidence and independent review.
2. Require fresh remote tag discovery.
3. Run the version and documentation cascade.
4. Build and install the exact candidate in clean environments.
5. Run full, browser, pilot, migration, and release gates.
6. Produce the Owner approval packet.

## Acceptance Criteria

- No stale version or tag reference remains.
- All mandatory release evidence is exact-SHA linked, including closed TASK-AR-652 through TASK-AR-657.
- Skipped browser exploration is not accepted for RC.
- No final release is published without explicit Owner approval.

## Verification

- `python -m pytest tests -q`
- `RUN_BETA_EXPLORATION=1 python -m pytest tests/test_ui_console_beta_exploration.py -q`
- `python scripts/release_execution_gate.py --check`

## Handoff

Provide the exact candidate SHA, install commands, evidence matrix, rollback plan, and remaining Owner decision.

## Stop Boundary

Stop before final tag push, GitHub Release publication, or closing the release approval issue.
