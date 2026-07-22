---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-612-001
work_uid: 0e074bb2-034e-486c-b483-51d5e5b4b866
kind: unit
parent_id: TASK-AR-612
unit_id: UNIT-TASK-AR-612-001
task_id: TASK-AR-612
task_set_id: TASKSET-AR-TERMINAL-STATUS-START-GUARD
initiative_id: INIT-AR-TERMINAL-STATUS-START-GUARD
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-22T21:43:00+09:00
updated_at: 2026-07-23T08:28:14+09:00
started_at: 2026-07-23T08:02:09+09:00
origin_type: review_finding
origin_ref: reviews/ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC.md
created_by: codex-root-planner
summary: Treat closed and released task statuses as terminal
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - ambiguity
context: TASK-AR-604 skeptic verification found a pre-existing counterexample: _target_status_for_work_start maps closed/released and the aliases 종결/종료/릴리스됨/배포됨 back to in_progress. The same dispatcher-local DONE_STATUSES set omits these terminal values, so selection can also treat them as actionable.
inputs:
  - reviews/ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC.md
  - scripts/status_alias.py
  - scripts/taskset_dispatcher.py
target_files:
  - scripts/taskset_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
  - tests/test_taskset_dispatcher.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Add failure-first selection and transition coverage, then make only the dispatcher-local terminal checks recognize closed/released and their aliases. Preserve the shared status schema and other consumers.
acceptance:
  - All six canonical/alias terminal cases are no-select and no-transition paths.
  - No global status vocabulary or unrelated consumer changes are included.
verification:
  - python -m pytest tests/test_taskset_dispatcher.py -q
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report failure-first evidence, terminal selection/start matrix, focused tests, template parity, host lock, and independent review.
stop_condition: Stop if the fix requires changing the shared schema or any status consumer outside taskset_dispatcher.
verified_at: 2026-07-23T08:07:40+09:00
verified_by: codex-root-task-ar-612
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-612-001-20260723080740.json
resolution: done
completed_at: 2026-07-23T08:28:14+09:00
closed_by: work.py close
actual_hours: 0.5
actual_tokens: 18000
---

# UNIT-TASK-AR-612-001 - Treat closed and released task statuses as terminal

## Context

TASK-AR-604 skeptic verification found a pre-existing counterexample: _target_status_for_work_start maps closed/released and the aliases 종결/종료/릴리스됨/배포됨 back to in_progress. The same dispatcher-local DONE_STATUSES set omits these terminal values, so selection can also treat them as actionable.

## Inputs

- reviews/ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC.md
- scripts/status_alias.py
- scripts/taskset_dispatcher.py

## Target Files

- scripts/taskset_dispatcher.py
- src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
- tests/test_taskset_dispatcher.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Add failure-first selection and transition coverage, then make only the dispatcher-local terminal checks recognize closed/released and their aliases. Preserve the shared status schema and other consumers.

## Steps

1. Reproduce terminal records being selected or mapped to an in-progress start target.
2. Align dispatcher-local terminal membership and start-target behavior with normalized closed/released values.
3. Mirror the runtime implementation and regenerate the host lock.
4. Run focused tests, parity, lock, taskset gates, W4a, independent W4b, and skeptic review.

## Acceptance Criteria

- All six canonical/alias terminal cases are no-select and no-transition paths.
- No global status vocabulary or unrelated consumer changes are included.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report failure-first evidence, terminal selection/start matrix, focused tests, template parity, host lock, and independent review.

## Stop Boundary

Stop if the fix requires changing the shared schema or any status consumer outside taskset_dispatcher.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T08:28:14+09:00`
- Resolution: `done`
- Actual hours: `0.5`
- Actual tokens: `18000`
- Closed by: `work.py close`
- Evidence:
  - `reviews/VERIFY-2026-07-23-unit-task-ar-612-001-20260723080740.json`
<!-- work-close:end -->
