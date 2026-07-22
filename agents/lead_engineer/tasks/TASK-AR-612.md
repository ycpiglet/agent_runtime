---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-612
display_id: TASK-AR-612
task_uid: a6489013-6f3e-4efa-b26f-a95d24266c88
work_id: TASK-AR-612
work_uid: a6489013-6f3e-4efa-b26f-a95d24266c88
kind: task
parent_id: TASKSET-AR-TERMINAL-STATUS-START-GUARD
registered_at: 2026-07-22T21:43:00+09:00
created_at: 2026-07-22T21:43:00+09:00
updated_at: 2026-07-22T21:43:00+09:00
title: Block taskset restart of closed and released records
status: planned
priority: P1
difficulty: S
est_hours: 1.0
est_tokens: 5000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-TERMINAL-STATUS-START-GUARD
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TERMINAL-STATUS-START-GUARD
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-612/UNIT-TASK-AR-612-001.md
reservation_id: RES-20260722-214300-77bc3d99-01
origin_type: review_finding
origin_ref: reviews/ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC.md
created_by: codex-root-planner
summary: Make closed/released tasks and their registered Korean aliases terminal in taskset selection and start persistence.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-612 - Block taskset restart of closed and released records

## Goal

- Make closed/released tasks and their registered Korean aliases terminal in taskset selection and start persistence.

## Scope

- Change only taskset_dispatcher terminal-status membership and start-target behavior, its generated-host mirror, focused regressions, and the host lock. Do not redesign the shared status schema or change unrelated status consumers.

## Acceptance Criteria

- Taskset planning does not select closed, released, 종결, 종료, 릴리스됨, or 배포됨 task records as actionable work.
- The start-target helper returns no transition for every closed/released canonical value and registered alias.
- Existing planned/active/localized start behavior and completed/done terminal behavior remain unchanged.
- Root/template parity and the generated-host lock remain current.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/taskset_work_gate.py --check`
