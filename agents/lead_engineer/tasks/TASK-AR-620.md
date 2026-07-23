---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-620
display_id: TASK-AR-620
task_uid: 69b08f2f-a8bd-4e56-9e4a-2b97fd134a4e
work_id: TASK-AR-620
work_uid: 69b08f2f-a8bd-4e56-9e4a-2b97fd134a4e
kind: task
parent_id: TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
registered_at: 2026-07-23T11:20:00+09:00
created_at: 2026-07-23T11:20:00+09:00
updated_at: 2026-07-23T11:38:03+09:00
started_at: 2026-07-23T11:20:20+09:00
title: Synchronize cadence isolation tasksets in the exact backlog expectation
status: completed
priority: P0
difficulty: S
est_hours: 0.5
est_tokens: 2500
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-620/UNIT-TASK-AR-620-001.md
reservation_id: RES-20260723-112000-715eb478-01
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-cadence-isolation-backlog-expectation-recovery-plan.md
created_by: codex-root-planner
summary: Add the two newly registered taskset IDs to the exact real-backlog expectation.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python scripts/taskset_work_gate.py --check
tags:
  - ci-recovery
  - backlog
  - taskset-classification
  - task-ar-619
verification_status: passed
verified_at: 2026-07-23T11:23:05+09:00
verified_by: codex-root-task-ar-620
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-620-20260723112305.json
resolution: done
completed_at: 2026-07-23T11:38:03+09:00
closed_by: /root/task-ar-620
actual_hours: 0.35
actual_tokens: 3500
---

# TASK-AR-620 - Synchronize cadence isolation tasksets in the exact backlog expectation

## Goal

- Restore PR #336 package tests without weakening the real-backlog exact-set contract.

## Scope

- Change only the expected taskset set in tests/test_backlog_board_tasksets.py and lifecycle evidence. Add the cadence injection and this recovery taskset IDs; preserve exact equality and production behavior.

## Acceptance Criteria

- The exact expected set includes TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION.
- The exact expected set includes TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY.
- No existing expected taskset ID or exact-equality assertion is removed or weakened.
- Focused backlog tests and the supported Python CI matrix pass.

## Verification

- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T11:38:03+09:00`
- Resolution: `done`
- Actual hours: `0.35`
- Actual tokens: `3500`
- Closed by: `/root/task-ar-620`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-620-20260723112305.json`
<!-- work-close:end -->
