---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-576
display_id: TASK-AR-576
task_uid: 04c1bf81-a8f7-48bd-b32f-161027937891
work_id: TASK-AR-576
work_uid: 04c1bf81-a8f7-48bd-b32f-161027937891
kind: task
parent_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
registered_at: 2026-06-17T17:15:00+09:00
created_at: 2026-06-17T17:15:00+09:00
updated_at: 2026-06-17T17:15:00+09:00
title: Publish remediation delta report
status: planned
priority: P1
difficulty: S
est_hours: 1
est_tokens: 1500
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-576/UNIT-TASK-AR-576-001.md
reservation_id: RES-20260617-171500-692625db-04
origin_type: owner_request
origin_ref: reviews/REPORT-2026-06-17-self-improvement-maturity.md
created_by: codex-planner
summary: Re-run the self-improvement report after role and asset remediation and state whether the persistent goal is mature, improving, or still active.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-576 - Publish remediation delta report

## Goal

- Re-run the self-improvement report after role and asset remediation and state whether the persistent goal is mature, improving, or still active.

## Scope

- Report the measured delta only after the remediation tasks land. Do not claim maturity unless gates pass.

## Acceptance Criteria

- The report compares baseline 32/6/17 with current score, role_gaps, and asset_gaps.
- The next-session pointer and status reflect the true persistent goal state.
- If score remains below 65, another concrete remediation cycle is registered or explicitly queued.

## Verification

- `python scripts/self_improvement_cycle.py report --dry-run --json`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE --check`
- `python scripts/evidence_index_generator.py --check`
