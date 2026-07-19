---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-595-001
work_uid: 685fb785-0a94-4160-88d1-fa00a76b86c7
kind: unit
parent_id: TASK-AR-595
unit_id: UNIT-TASK-AR-595-001
task_id: TASK-AR-595
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T10:28:06+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:#274,#279,#280,#285,#287,#289,#290; pr:#277
created_by: codex-root-planner
summary: Repair updater build isolation
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: GitHub #287 reports Ubuntu system setuptools 59.6 producing UNKNOWN-0.0.0 because host_update explicitly passes --no-build-isolation even though pyproject requires setuptools>=68.
inputs:
  - https://github.com/ycpiglet/agent_runtime/issues/287
  - src/agent_runtime/host_update.py
  - pyproject.toml
target_files:
  - src/agent_runtime/host_update.py
  - tests/test_inventory_sync_sanitize.py
scope: Use pip's isolated build environment for updater installs, align rendered commands and execution steps, and pin the contract in focused tests.
acceptance:
  - Neither generated updater commands nor install-upstream args contain --no-build-isolation.
  - All host update tests pass without weakening existing checks.
verification:
  - python -m pytest tests/test_inventory_sync_sanitize.py -q
handoff: Report the exact command delta and focused test result.
stop_condition: Stop if removing the override makes offline or pinned-source installation impossible under the documented updater contract; capture the failing command and environment.
---

# UNIT-TASK-AR-595-001 - Repair updater build isolation

## Context

GitHub #287 reports Ubuntu system setuptools 59.6 producing UNKNOWN-0.0.0 because host_update explicitly passes --no-build-isolation even though pyproject requires setuptools>=68.

## Inputs

- https://github.com/ycpiglet/agent_runtime/issues/287
- src/agent_runtime/host_update.py
- pyproject.toml

## Target Files

- src/agent_runtime/host_update.py
- tests/test_inventory_sync_sanitize.py

## Scope

Use pip's isolated build environment for updater installs, align rendered commands and execution steps, and pin the contract in focused tests.

## Steps

1. Remove the updater-only no-build-isolation override from plan and execution construction.
2. Add assertions that declared build requirements are not bypassed.
3. Run the complete host update test module.

## Acceptance Criteria

- Neither generated updater commands nor install-upstream args contain --no-build-isolation.
- All host update tests pass without weakening existing checks.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py -q`

## Handoff

Report the exact command delta and focused test result.

## Stop Boundary

Stop if removing the override makes offline or pinned-source installation impossible under the documented updater contract; capture the failing command and environment.
