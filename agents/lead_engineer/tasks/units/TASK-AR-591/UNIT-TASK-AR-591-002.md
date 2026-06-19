---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-591-002
work_uid: 48ffb839-b468-414f-8bac-f4987284bc8c
kind: unit
parent_id: TASK-AR-591
unit_id: UNIT-TASK-AR-591-002
task_id: TASK-AR-591
task_set_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
initiative_id: INIT-AR-VISUAL-SYSTEM-INTEGRATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-20T05:18:36+09:00
updated_at: 2026-06-20T05:18:36+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-autonomous-loop
created_by: lead-engineer
summary: Boot-verify the served console
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Unit tests cover rendering logic; this confirms the whole thing actually boots and serves.
inputs:
  - src/agent_runtime/ui_console.py (server entrypoint)
  - ui_console_assets.py
  - ui_design_assets.py
target_files:
  - tests/test_ui_console_e2e.py
scope: Add/extend a boot smoke test: start the server on an ephemeral port, GET / and the served assets, assert 200 + the served JS passes a syntax check; tear down.
acceptance:
  - A boot smoke test proves the console serves / and assets with 200 and valid JS.
verification:
  - python -m pytest tests/test_ui_console_e2e.py -q
handoff: Console boot-verified.
stop_condition: If node is unavailable for the JS check, fall back to a Python-side bracket/quote balance check and note it.
---

# UNIT-TASK-AR-591-002 - Boot-verify the served console

## Context

Unit tests cover rendering logic; this confirms the whole thing actually boots and serves.

## Inputs

- src/agent_runtime/ui_console.py (server entrypoint)
- ui_console_assets.py
- ui_design_assets.py

## Target Files

- tests/test_ui_console_e2e.py

## Scope

Add/extend a boot smoke test: start the server on an ephemeral port, GET / and the served assets, assert 200 + the served JS passes a syntax check; tear down.

## Steps

1. Launch the stdlib server on a free port in-process or via subprocess.
2. Assert GET / and asset endpoints return 200 and non-empty.
3. Syntax-check the served JS (node --check or a JS parser).
4. Tear down cleanly.

## Acceptance Criteria

- A boot smoke test proves the console serves / and assets with 200 and valid JS.

## Verification

- `python -m pytest tests/test_ui_console_e2e.py -q`

## Handoff

Console boot-verified.

## Stop Boundary

If node is unavailable for the JS check, fall back to a Python-side bracket/quote balance check and note it.
