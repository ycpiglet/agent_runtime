---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-646
display_id: TASK-AR-646
task_uid: 81681d8c-8cc3-48e9-a5fd-b030e01f4f08
work_id: TASK-AR-646
work_uid: 81681d8c-8cc3-48e9-a5fd-b030e01f4f08
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Make model routing economically effective and auditable
status: planned
priority: P0
difficulty: L
est_hours: 10
est_tokens: 24000
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-646/UNIT-TASK-AR-646-001.md
reservation_id: RES-20260728-163601-b8c2a87a-08
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Use lower-cost native subagents by default where appropriate and prove when escalation actually changed the invoked model.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-646 - Make model routing economically effective and auditable

## Goal

- Use lower-cost native subagents by default where appropriate and prove when escalation actually changed the invoked model.

## Scope

- Detect provider capabilities, distinguish advisory from enforced routing, record dispatch justification and actual usage, and block false cost-saving claims.

## Acceptance Criteria

- Equivalent tier mappings are reported as ineffective.
- Every subagent dispatch records reason, requested tier, resolved model, escalation signal, and actual usage when available.
- Deterministic tools run before model delegation.
- Runtime uses native provider agents rather than rebuilding an executor.

## Verification

- `python -m pytest tests/test_model_routing.py tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_provider_import_contract.py -q`
