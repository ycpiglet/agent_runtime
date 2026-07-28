---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-647
display_id: TASK-AR-647
task_uid: e331d145-b696-4e1f-8c82-e2aa5267df0b
work_id: TASK-AR-647
work_uid: e331d145-b696-4e1f-8c82-e2aa5267df0b
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Adopt native Allimbot events and security-service guardrails
status: planned
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: risk-and-safety
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-647/UNIT-TASK-AR-647-001.md
reservation_id: RES-20260728-163601-b8c2a87a-09
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Use current durable, allowlisted Allimbot delivery and add reusable security/external-effect controls for service hosts.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-647 - Adopt native Allimbot events and security-service guardrails

## Goal

- Use current durable, allowlisted Allimbot delivery and add reusable security/external-effect controls for service hosts.

## Scope

- Replace the legacy runtime notifier with ProjectEmitter-compatible events, add the security-service profile, and preserve fail-open delivery without secret leakage.

## Acceptance Criteria

- Runtime emits only allowlisted current Allimbot events.
- Delivery uses v1/events and durable spool behavior.
- Allimbot unavailability never blocks local work.
- Security-service profile covers secrets, auth, migration, and production external effects.

## Verification

- `python -m pytest tests/test_allimbot.py tests/test_notify_routing.py tests/test_owner_governance_consumer_host.py tests/test_doctor.py -q`
