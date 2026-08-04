---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-658-001
work_uid: 766de15b-419f-491f-b605-2e72ace4a32c
kind: unit
parent_id: TASK-AR-658
unit_id: UNIT-TASK-AR-658-001
task_id: TASK-AR-658
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: uiux
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Build the secret-free Runtime health resource and console surface
horizon: unit
model_tier: worker_standard
escalation_triggers:
depends_on:
  - TASK-AR-652
  - TASK-AR-653
  - TASK-AR-654
  - TASK-AR-655
  - TASK-AR-656
context: The current UI exposes task model tiers and generic ops metrics but not actual routing receipts, Scribe source debt, Compound recurrence, task-claim expiry, hook duplicates, or exact pilot contracts in one owner-facing surface.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console_assets.py
target_files:
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console.py
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - tests/test_ui_console_e2e.py
scope: Read and summarize stabilized local receipts only. Keep all actions proposal-only or absent.
acceptance:
  - The Owner can see why a tier did or did not save resources.
  - Projection freshness is visually distinct from Scribe debt clearance.
  - Expired claims and missing Compound coverage are actionable.
  - The UI cannot execute external or release actions.
verification:
  - python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_console_e2e.py -q
handoff: Attach resource schema, redaction negatives, empty/error states, accessibility evidence, browser screenshots, and independent W4b.
stop_condition: Stop before adding provider credentials, raw prompt content, writable migration controls, deploy, or release actions to the UI.
---

# UNIT-TASK-AR-658-001 - Build the secret-free Runtime health resource and console surface

## Context

The current UI exposes task model tiers and generic ops metrics but not actual routing receipts, Scribe source debt, Compound recurrence, task-claim expiry, hook duplicates, or exact pilot contracts in one owner-facing surface.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console_assets.py

## Target Files

- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console.py
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_state.py
- tests/test_ui_console.py
- tests/test_ui_console_e2e.py

## Scope

Read and summarize stabilized local receipts only. Keep all actions proposal-only or absent.

## Steps

1. Define the secret-free runtime_health resource contract.
2. Add unavailable, blocked, warning, and healthy fixtures.
3. Render the owner summary and drill-down evidence refs.
4. Run accessibility, escape, responsive, and browser smoke.

## Acceptance Criteria

- The Owner can see why a tier did or did not save resources.
- Projection freshness is visually distinct from Scribe debt clearance.
- Expired claims and missing Compound coverage are actionable.
- The UI cannot execute external or release actions.

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_console_e2e.py -q`

## Handoff

Attach resource schema, redaction negatives, empty/error states, accessibility evidence, browser screenshots, and independent W4b.

## Stop Boundary

Stop before adding provider credentials, raw prompt content, writable migration controls, deploy, or release actions to the UI.
