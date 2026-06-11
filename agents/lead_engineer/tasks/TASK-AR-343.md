---
id: TASK-AR-343
display_id: TASK-AR-343
task_uid: 8fa333a3-3287-4d74-a30b-634023c0842a
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
started_at: 2026-06-12T01:38:36+09:00
updated_at: 2026-06-12T01:38:36+09:00
completed_at: 2026-06-12T01:38:36+09:00
status: completed
priority: P0
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
horizon: short
planner_model_tier: planner_high
worker_model_tier: worker_low
reviewer_model_tier: reviewer_standard
escalation_triggers: [ambiguity, repeated_failure]
tags:
  - project-management
  - unit-spec
  - worker-ready
---

# TASK-AR-343 - Unit spec template and worker-ready definition

## Goal

- Create the detailed unit document shape that lower-cost implementation models can execute safely.

## Scope

- Add `agents/lead_engineer/tasks/units/README.md` with the required unit fields.
- Add at least one example unit spec showing context, inputs, target files, scope, acceptance, verification, and handoff.
- Define `planner_refine_required` when a unit lacks enough detail.

## Acceptance Criteria

- A worker can understand what to do from the unit spec alone.
- Unit specs include explicit stop boundaries so workers do not plan adjacent work.
- The template is reusable in host projects.

## Evidence Targets

- `agents/lead_engineer/tasks/units/README.md`
- template mirror under `src/agent_runtime/templates/project/`

