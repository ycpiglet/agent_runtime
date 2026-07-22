---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-607-001
work_uid: 841e0604-2f79-4fca-b114-8dd927a8779c
kind: unit
parent_id: TASK-AR-607
unit_id: UNIT-TASK-AR-607-001
task_id: TASK-AR-607
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-23T01:01:00+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Isolate transient-spawn recovery state
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - repeated_failure
  - ci
  - ambiguity
context: GitHub issue 297 records intermittent CI failure in a recovery regression. Reproduce with repeated and ordered runs, identify global/module/monkeypatch leakage, and make the test deterministic without weakening its oracle.
inputs:
  - reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
  - tests/test_release_cadence_trigger.py
  - scripts/release_cadence_trigger.py
target_files:
  - tests/test_release_cadence_trigger.py
  - scripts/release_cadence_trigger.py
scope: Fix deterministic test isolation and only the minimal product seam if the failure-first probe proves it necessary. Do not relax thresholds or delete the retry assertion.
acceptance:
  - One transient spawn failure is observed and recovery metrics meet the unchanged threshold.
  - At least 100 repeated executions pass without rerun-only recovery.
verification:
  - python -m pytest tests/test_release_cadence_trigger.py -q
handoff: Report the reproduced interaction, preserved oracle, repeat count, and GitHub issue 297 evidence.
stop_condition: Stop if reproduction requires changing release thresholds or masking a production error.
verified_at: 2026-07-23T00:37:50+09:00
verified_by: codex-root-task-ar-607
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-607-001-20260723003750.json
resolution: done
completed_at: 2026-07-23T01:01:00+09:00
closed_by: codex-root
actual_hours: 0.7
actual_tokens: 50000
---

# UNIT-TASK-AR-607-001 - Isolate transient-spawn recovery state

## Context

GitHub #297 records intermittent CI failure in a recovery regression. Reproduce with repeated and ordered runs, identify global/module/monkeypatch leakage, and make the test deterministic without weakening its oracle.

## Inputs

- reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
- tests/test_release_cadence_trigger.py
- scripts/release_cadence_trigger.py

## Target Files

- tests/test_release_cadence_trigger.py
- scripts/release_cadence_trigger.py

## Scope

Fix deterministic test isolation and only the minimal product seam if the failure-first probe proves it necessary. Do not relax thresholds or delete the retry assertion.

## Steps

1. Run repeated and collection-order probes with metric capture.
2. Remove shared state or module-loading leakage at the narrowest seam.
3. Run a high-count deterministic regression.

## Acceptance Criteria

- One transient spawn failure is observed and recovery metrics meet the unchanged threshold.
- At least 100 repeated executions pass without rerun-only recovery.

## Verification

- `python -m pytest tests/test_release_cadence_trigger.py -q`

## Handoff

Report the reproduced interaction, preserved oracle, repeat count, and issue #297 evidence.

## Stop Boundary

Stop if reproduction requires changing release thresholds or masking a production error.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T01:01:00+09:00`
- Resolution: `done`
- Actual hours: `0.7`
- Actual tokens: `50000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-23-unit-task-ar-607-001-20260723003750.json`
<!-- work-close:end -->
