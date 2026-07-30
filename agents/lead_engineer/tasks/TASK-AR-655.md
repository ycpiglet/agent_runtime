---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-655
display_id: TASK-AR-655
task_uid: 897757d6-f0a3-4328-a8d3-f38d3ec2ceb2
work_id: TASK-AR-655
work_uid: 897757d6-f0a3-4328-a8d3-f38d3ec2ceb2
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Freeze goal-run scope and require attested transitions
status: planned
priority: P0
difficulty: L
est_hours: 16
est_tokens: 34000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-655/UNIT-TASK-AR-655-001.md
reservation_id: RES-20260730-112517-91ed5cf4-01
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Turn a conversational goal into an immutable execution contract whose exact taskset, task, and unit membership cannot grow during the run.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - Starting a goal seals exact taskset, task, and unit IDs plus relevant hashes and base SHA.
  - Work registered after sealing is reported as discovered-after-scope and is never executable in the current run.
  - Scope amendment requires an approval reference, records old and new digests, and increments a monotonic revision.
  - The completion predicate is evaluated only against frozen membership.
  - The registration path can express dependencies between locally created tasks without guessing future task IDs.
  - A newly registered dynamic taskset is immediately resolvable by taskset and wave dispatch.
verification:
  - python -m pytest -q tests/test_execution_scope.py tests/test_work_registration.py tests/test_taskset_dispatcher.py
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/work_schema_gate.py --items --check
---

# TASK-AR-655 - Freeze goal-run scope and require attested transitions

## Goal

- Turn a conversational goal into an immutable execution contract whose exact taskset, task, and unit membership cannot grow during the run.

## Scope

- Add the GoalRun and ScopeChangeRequest model on the canonical runtime-state store, deterministic membership hashing, and planner-facing start/status/amend/close commands. Preserve existing work records and provide an explicit compatibility path for raw goal text.

## Acceptance Criteria

- Starting a goal seals exact taskset, task, and unit IDs plus relevant hashes and base SHA.
- Work registered after sealing is reported as discovered-after-scope and is never executable in the current run.
- Scope amendment requires an approval reference, records old and new digests, and increments a monotonic revision.
- The completion predicate is evaluated only against frozen membership.
- The registration path can express dependencies between locally created tasks without guessing future task IDs.
- A newly registered dynamic taskset is immediately resolvable by taskset and wave dispatch.

## Verification

- `python -m pytest -q tests/test_execution_scope.py tests/test_work_registration.py tests/test_taskset_dispatcher.py`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/work_schema_gate.py --items --check`
