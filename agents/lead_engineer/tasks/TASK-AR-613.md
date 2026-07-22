---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-613
display_id: TASK-AR-613
task_uid: 26230ebe-4bff-43d5-8ef4-57749db3ec33
work_id: TASK-AR-613
work_uid: 26230ebe-4bff-43d5-8ef4-57749db3ec33
kind: task
parent_id: TASKSET-AR-RELEASE-CADENCE-QUERY-RECOVERY
registered_at: 2026-07-23T01:16:34+09:00
created_at: 2026-07-23T01:16:34+09:00
updated_at: 2026-07-23T03:13:02+09:00
started_at: 2026-07-23T01:25:41+09:00
title: Recover transient non-zero cadence queries without false not-triggered
status: completed
priority: P0
difficulty: M
est_hours: 2
est_tokens: 8000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-RELEASE-CADENCE-QUERY-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-RELEASE-CADENCE-QUERY-RECOVERY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-613/UNIT-TASK-AR-613-001.md
reservation_id: RES-20260723-011634-32012327-01
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-cadence-query-recovery-plan.md
created_by: codex-root-planner
summary: Close GitHub issue 316 by distinguishing legitimate no-tag responses from transient non-zero Git query failures.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/taskset_work_gate.py --check
tags:
  - github-316
  - ci-flake
  - release-cadence
  - release-auto
verification_status: passed
verified_at: 2026-07-23T02:26:08+09:00
verified_by: codex-root-task-ar-613
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-613-20260723014533.json
  - reviews/VERIFY-2026-07-23-task-ar-613-20260723022608.json
resolution: done
completed_at: 2026-07-23T03:13:02+09:00
closed_by: codex-root-task-ar-613
actual_hours: 2.0
actual_tokens: 100000
---

# TASK-AR-613 - Recover transient non-zero cadence queries without false not-triggered

## Goal

- Close GitHub issue 316 by preventing a valid tagged cadence from collapsing into release-auto not-triggered after a transient non-zero Git query result.

## Scope

- Change only release-cadence Git query classification/retry behavior, its generated-host mirror, focused release cadence and release-auto regressions, and the host lock. Preserve cadence thresholds, bump policy, and the legitimate no-tag quiet path.

## Acceptance Criteria

- One transient unexpected non-zero Git query result is retried and a subsequent valid cadence answer triggers normally.
- Exhausted unexpected non-zero Git query results produce git-query-error diagnostics and release-auto trigger-error rather than not-triggered.
- A repository with no tags remains a deterministic quiet pass.
- Cadence thresholds, bump semantics, root/template parity, and the generated-host lock remain correct.

## Verification

- `python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/taskset_work_gate.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T03:13:02+09:00`
- Resolution: `done`
- Actual hours: `2.0`
- Actual tokens: `100000`
- Closed by: `codex-root-task-ar-613`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-613-20260723014533.json`
  - `reviews/VERIFY-2026-07-23-task-ar-613-20260723022608.json`
<!-- work-close:end -->
