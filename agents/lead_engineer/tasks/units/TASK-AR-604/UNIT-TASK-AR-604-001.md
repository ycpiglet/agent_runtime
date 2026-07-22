---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-604-001
work_uid: ffa6a7e1-b7cf-47db-8bd7-b5d9a4c08eeb
kind: unit
parent_id: TASK-AR-604
unit_id: UNIT-TASK-AR-604-001
task_id: TASK-AR-604
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T21:43:30+09:00
started_at: 2026-07-22T21:18:04+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Separate task status normalization from persistence
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - ambiguity
context: GitHub
inputs:
  - reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
  - scripts/taskset_dispatcher.py
target_files:
  - scripts/taskset_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
  - tests/test_taskset_dispatcher.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Change only taskset start status persistence and its regression coverage; do not redesign the global state machine.
acceptance:
  - Taskset start no longer writes the internal alias into localized canonical frontmatter.
  - Existing English-status tasks remain compatible.
verification:
  - python -m pytest tests/test_taskset_dispatcher.py -q
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report before/after frontmatter, normalized payload behavior, focused tests, and issue
stop_condition: Stop before changing unrelated status consumers or schema vocabulary.
verified_at: 2026-07-22T21:23:49+09:00
verified_by: codex-root-task-ar-604
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-604-001-20260722212349.json
resolution: done
completed_at: 2026-07-22T21:43:30+09:00
closed_by: codex-root
actual_hours: 0.4
actual_tokens: 30000
---

# UNIT-TASK-AR-604-001 - Separate task status normalization from persistence

## Context

GitHub #293 shows taskset start writes in_progress into a canonical record that uses localized workflow values. The dispatcher may normalize for comparisons but must preserve the canonical persistence vocabulary.

## Inputs

- reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
- scripts/taskset_dispatcher.py

## Target Files

- scripts/taskset_dispatcher.py
- src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
- tests/test_taskset_dispatcher.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Change only taskset start status persistence and its regression coverage; do not redesign the global state machine.

## Steps

1. Add a failure-first localized-status start test.
2. Persist the canonical start status while retaining normalized selection.
3. Run parity and lock checks.

## Acceptance Criteria

- Taskset start no longer writes the internal alias into localized canonical frontmatter.
- Existing English-status tasks remain compatible.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report before/after frontmatter, normalized payload behavior, focused tests, and issue #293 evidence.

## Stop Boundary

Stop before changing unrelated status consumers or schema vocabulary.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-22T21:43:30+09:00`
- Resolution: `done`
- Actual hours: `0.4`
- Actual tokens: `30000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-22-unit-task-ar-604-001-20260722212349.json`
<!-- work-close:end -->
