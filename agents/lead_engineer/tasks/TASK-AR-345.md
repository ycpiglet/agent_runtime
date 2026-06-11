---
id: TASK-AR-345
display_id: TASK-AR-345
task_uid: ece0f0d8-c214-418f-b119-e3163ce2b891
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
started_at: 2026-06-12T01:38:36+09:00
updated_at: 2026-06-12T01:38:36+09:00
completed_at: 2026-06-12T01:38:36+09:00
status: completed
priority: P0
difficulty: M
est_hours: 4
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
horizon: short
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
escalation_triggers: [ambiguity, high_risk, security, cross_cutting, external_effect, repeated_failure]
tags:
  - project-management
  - model-routing
  - cost-control
---

# TASK-AR-345 - Model-tier routing metadata

## Goal

- Add planner/worker/reviewer tier metadata and escalation triggers to task and unit records.

## Scope

- Define allowed tier values such as `planner_high`, `worker_low`, `worker_standard`, `reviewer_standard`, and `reviewer_high`.
- Add escalation triggers for ambiguity, high risk, security, cross-cutting changes, external effects, and repeated failure.
- Keep concrete provider/model names outside canonical task records unless Owner explicitly requires them.

## Acceptance Criteria

- Task/unit records can explain why a low-cost worker is acceptable or why escalation is required.
- Routing tests cover default low-tier implementation and high-tier escalation cases.
- Existing tasks without model-tier fields are treated as migration watch, not silent pass.

## Evidence Targets

- `scripts/model_routing.py` or equivalent existing routing surface
- `tests/test_model_routing.py`
- task/unit fixture records

