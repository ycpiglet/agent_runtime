---
id: TASK-AR-349
display_id: TASK-AR-349
task_uid: 7e8741f0-87de-4be0-8632-ee6bcd9fc90f
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
started_at: 2026-06-12T01:38:36+09:00
updated_at: 2026-06-12T01:38:36+09:00
completed_at: 2026-06-12T01:38:36+09:00
status: completed
priority: P1
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
horizon: medium
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
escalation_triggers: [ambiguity, repeated_failure]
tags:
  - project-management
  - template
  - host-project
---

# TASK-AR-349 - Template propagation

## Goal

- Mirror the PM hierarchy, unit templates, schemas, and gates into generated host projects.

## Scope

- Update template AGENTS and project docs with the decomposition contract.
- Mirror unit template and readiness gate into `src/agent_runtime/templates/project/`.
- Verify new host projects receive the same worker-ready rules.

## Acceptance Criteria

- Generated host projects can enforce unit readiness without copying root-only files manually.
- Template smoke tests cover the new files.
- Host-specific details remain in `agents/project/`, not reusable role skills.

## Evidence Targets

- `src/agent_runtime/templates/project/AGENTS.md`
- template project files
- `tests/test_template_smoke.py`

