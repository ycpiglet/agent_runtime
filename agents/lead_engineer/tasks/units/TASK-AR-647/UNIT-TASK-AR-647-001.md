---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-647-001
work_uid: af1cf17b-4cb9-4686-9d2f-9fd0e3238a13
kind: unit
parent_id: TASK-AR-647
unit_id: UNIT-TASK-AR-647-001
task_id: TASK-AR-647
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Replace legacy notifier with optional native ProjectEmitter adapter
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The template still targets 127.0.0.1:8787/trigger and can post directly to ntfy, while current Allimbot uses allowlisted project recipes, ALLIMBOT_ENDPOINT, project tokens, v1/events, and a durable spool.
inputs:
  - src/agent_runtime/templates/project/scripts/allimbot.py
  - ../allimbot/src/allimbot/integrations.py
  - ../allimbot/integrations/projects/agent-runtime.json
target_files:
  - src/agent_runtime/allimbot.py
  - src/agent_runtime/templates/project/scripts/allimbot.py
  - src/agent_runtime/templates/project/scripts/allimbot_stop_hook.py
  - src/agent_runtime/config.py
  - tests/test_allimbot.py
  - tests/test_notify_routing.py
  - docs/allimbot-integration.md
scope: Use Allimbot as an optional dependency or compatible adapter, enforce recipe allowlists, and add security profile mappings. Do not introduce a mandatory circular dependency.
acceptance:
  - Legacy /trigger is absent from standard mode.
  - Unknown event types and metadata are rejected locally.
  - No token, prompt, or secret enters event data.
  - Offline events remain recoverable.
verification:
  - python -m pytest tests/test_allimbot.py tests/test_notify_routing.py tests/test_doctor.py -q
handoff: Provide event compatibility and security matrices against the current Allimbot recipe.
stop_condition: Stop before changing Allimbot production credentials or sending live external notifications.
---

# UNIT-TASK-AR-647-001 - Replace legacy notifier with optional native ProjectEmitter adapter

## Context

The template still targets 127.0.0.1:8787/trigger and can post directly to ntfy, while current Allimbot uses allowlisted project recipes, ALLIMBOT_ENDPOINT, project tokens, v1/events, and a durable spool.

## Inputs

- src/agent_runtime/templates/project/scripts/allimbot.py
- ../allimbot/src/allimbot/integrations.py
- ../allimbot/integrations/projects/agent-runtime.json

## Target Files

- src/agent_runtime/allimbot.py
- src/agent_runtime/templates/project/scripts/allimbot.py
- src/agent_runtime/templates/project/scripts/allimbot_stop_hook.py
- src/agent_runtime/config.py
- tests/test_allimbot.py
- tests/test_notify_routing.py
- docs/allimbot-integration.md

## Scope

Use Allimbot as an optional dependency or compatible adapter, enforce recipe allowlists, and add security profile mappings. Do not introduce a mandatory circular dependency.

## Steps

1. Define the runtime event boundary.
2. Use ProjectEmitter when installed and a compatible local spool adapter otherwise.
3. Remove implicit direct-ntfy delivery from standard mode.
4. Add redaction, allowlist, and fail-open tests.

## Acceptance Criteria

- Legacy /trigger is absent from standard mode.
- Unknown event types and metadata are rejected locally.
- No token, prompt, or secret enters event data.
- Offline events remain recoverable.

## Verification

- `python -m pytest tests/test_allimbot.py tests/test_notify_routing.py tests/test_doctor.py -q`

## Handoff

Provide event compatibility and security matrices against the current Allimbot recipe.

## Stop Boundary

Stop before changing Allimbot production credentials or sending live external notifications.
