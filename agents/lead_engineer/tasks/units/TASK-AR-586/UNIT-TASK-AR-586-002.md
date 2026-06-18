---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-586-002
work_uid: 0e6437c8-a49a-41a1-9aa7-3fe8f8e839d0
kind: unit
parent_id: TASK-AR-586
unit_id: UNIT-TASK-AR-586-002
task_id: TASK-AR-586
task_set_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
initiative_id: INIT-AR-RELEASE-AUTOMATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-06-18T22:26:32+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Schedule + Owner notification wiring
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: test.yml already has a weekly cron (0 2 * * 1). Auto-release should run at that cadence on green main only, with head-SHA pinning like auto-merge.yml.
inputs:
  - .github/workflows/test.yml
  - .github/workflows/auto-merge.yml (safety pattern: head-SHA equality)
  - scripts/release_auto_noncritical.py
target_files:
  - .github/workflows/release-auto.yml
scope: Workflow wiring + notification only. Trigger on the cadence boundary (weekly cron / W6) gated on green main CI; never on untested SHAs.
acceptance:
  - Workflow only fires at the cadence boundary on green main and only for noncritical bumps.
verification:
  - python -c "import yaml; yaml.safe_load(open('.github/workflows/release-auto.yml'))"
handoff: Auto-release live for noncritical; major/breaking still Owner-gated.
stop_condition: Do not enable scheduled tag/push without the Owner-notification path in place.
---

# UNIT-TASK-AR-586-002 - Schedule + Owner notification wiring

## Context

test.yml already has a weekly cron (0 2 * * 1). Auto-release should run at that cadence on green main only, with head-SHA pinning like auto-merge.yml.

## Inputs

- .github/workflows/test.yml
- .github/workflows/auto-merge.yml (safety pattern: head-SHA equality)
- scripts/release_auto_noncritical.py

## Target Files

- .github/workflows/release-auto.yml

## Scope

Workflow wiring + notification only. Trigger on the cadence boundary (weekly cron / W6) gated on green main CI; never on untested SHAs.

## Steps

1. Add a scheduled workflow that runs release_auto_noncritical.py on green main.
2. Pin to the validated head SHA so an untested push is never released.
3. Send an Owner notification on execution.
4. Document the trigger + safety in the workflow header.

## Acceptance Criteria

- Workflow only fires at the cadence boundary on green main and only for noncritical bumps.

## Verification

- `python -c "import yaml; yaml.safe_load(open('.github/workflows/release-auto.yml'))"`

## Handoff

Auto-release live for noncritical; major/breaking still Owner-gated.

## Stop Boundary

Do not enable scheduled tag/push without the Owner-notification path in place.
