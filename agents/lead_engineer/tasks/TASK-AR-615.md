---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-615
display_id: TASK-AR-615
task_uid: dcbfa286-be09-470e-ac3f-85ac4649f049
work_id: TASK-AR-615
work_uid: dcbfa286-be09-470e-ac3f-85ac4649f049
kind: task
parent_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
registered_at: 2026-07-23T03:09:36+09:00
created_at: 2026-07-23T03:09:36+09:00
updated_at: 2026-07-23T04:15:10+09:00
title: Retry recognized pre-commit HEAD parse transients in release-auto fixtures
status: completed
priority: P0
difficulty: S
est_hours: 1
est_tokens: 4500
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-615/UNIT-TASK-AR-615-001.md
reservation_id: RES-20260723-030936-5a67a518-01
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-auto-fixture-head-recovery-plan.md
created_by: codex-root-planner
summary: Bound retry recovery to the observed `fatal: could not parse HEAD` fixture commit failure.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python scripts/taskset_work_gate.py --check
tags:
  - github-320
  - ci-flake
  - release-auto
  - test-fixture
verification_status: passed
verified_at: 2026-07-23T03:37:58+09:00
verified_by: codex-root-task-ar-615
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-615-20260723033758.json
resolution: done
completed_at: 2026-07-23T04:15:10+09:00
closed_by: codex-root-task-ar-615
actual_hours: 1.1
actual_tokens: 30000
---

# TASK-AR-615 - Retry recognized pre-commit HEAD parse transients in release-auto fixtures

## Goal

- Close GitHub issue 320 by making the release-auto fixture recover from the observed transient Git commit failure while preserving immediate failure for unknown errors.

## Scope

- Change only tests/test_release_auto_noncritical.py fixture helper retry classification and focused regressions. Do not change production code or broad CI policy.

## Acceptance Criteria

- A recognized could-not-parse-HEAD failure followed by success recovers after exactly one retry.
- Repeated recognized failures exhaust at the configured bound with sanitized evidence.
- Unknown Git failures are not retried and still fail immediately with sanitized diagnostics.
- Full release-auto/cadence regressions and the taskset gate pass.

## Verification

- `python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q`
- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T04:15:10+09:00`
- Resolution: `done`
- Actual hours: `1.1`
- Actual tokens: `30000`
- Closed by: `codex-root-task-ar-615`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-615-20260723033758.json`
<!-- work-close:end -->
