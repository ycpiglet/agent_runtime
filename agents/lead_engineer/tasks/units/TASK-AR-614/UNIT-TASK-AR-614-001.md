---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-614-001
work_uid: 526126c3-48b7-4787-a0c7-1f8151a32f27
kind: unit
parent_id: TASK-AR-614
unit_id: UNIT-TASK-AR-614-001
task_id: TASK-AR-614
task_set_id: TASKSET-AR-SELF-EVAL-QUERY-INTEGRITY
initiative_id: INIT-AR-SELF-EVAL-QUERY-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead_engineer
created_at: 2026-07-23T02:23:56+09:00
updated_at: 2026-07-23T04:39:28+09:00
started_at: 2026-07-23T04:27:22+09:00
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-self-eval-query-integrity-plan.md
created_by: codex-root-planner
summary: Propagate shared Git query errors through self-eval
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - reliability
  - cross_cutting
  - data_integrity
context: TASK-AR-613 W4b independently reproduced a tagged self-eval window where rev-list exhausted rc 128 three times but the report remained pass with commit_count zero and no error evidence. GitHub issue 318 tracks the defect. The release-cadence unit explicitly forbids modifying unrelated status consumers, so this is a separate registered remediation.
inputs:
  - reviews/REVIEW-2026-07-23-self-eval-query-integrity-plan.md
  - reviews/W4B-2026-07-23-TASK-AR-613.md
  - reviews/ROLE-REVIEW-2026-07-23-TASK-AR-613-SKEPTIC.md
  - GitHub issue 318
  - scripts/self_eval_metrics.py
  - scripts/release_cadence_trigger.py
target_files:
  - scripts/self_eval_metrics.py
  - tests/test_self_eval_metrics.py
scope: Add failure-first coverage for every self-eval call into the shared cadence Git helper, isolate query-error state at report start, and return a loud non-mutating error report with sanitized structured evidence whenever any query exhausts retries.
acceptance:
  - Three failed attempts for any direct self-eval Git query yield status error/unevaluated and structured evidence.
  - No partial Git-derived metric is marked collected after a query error.
  - A successful tagged window and a genuine no-tag repository keep their existing results.
  - Release cadence behavior remains unchanged and all registered verification commands pass.
verification:
  - python -m pytest tests/test_self_eval_metrics.py tests/test_release_cadence_trigger.py tests/test_semver_bump_property.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/taskset_work_gate.py --check
handoff: Report failure-first evidence by query type, state isolation behavior, error schema and CLI output, successful/no-tag compatibility, cross-consumer regression results, and independent W4b.
stop_condition: Stop if truthful self-eval reporting requires changing cadence thresholds, version policy, or unrelated WORK-SCHEMA metric formulas.
verified_at: 2026-07-23T04:39:28+09:00
verified_by: codex-root-task-ar-614
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-614-001-20260723043928.json
---

# UNIT-TASK-AR-614-001 - Propagate shared Git query errors through self-eval

## Context

TASK-AR-613 W4b independently reproduced a tagged self-eval window where rev-list exhausted rc 128 three times but the report remained pass with commit_count zero and no error evidence. GitHub issue 318 tracks the defect. The release-cadence unit explicitly forbids modifying unrelated status consumers, so this is a separate registered remediation.

## Inputs

- reviews/REVIEW-2026-07-23-self-eval-query-integrity-plan.md
- reviews/W4B-2026-07-23-TASK-AR-613.md
- reviews/ROLE-REVIEW-2026-07-23-TASK-AR-613-SKEPTIC.md
- GitHub issue 318
- scripts/self_eval_metrics.py
- scripts/release_cadence_trigger.py

## Target Files

- scripts/self_eval_metrics.py
- tests/test_self_eval_metrics.py

## Scope

Add failure-first coverage for every self-eval call into the shared cadence Git helper, isolate query-error state at report start, and return a loud non-mutating error report with sanitized structured evidence whenever any query exhausts retries.

## Steps

1. Reproduce an exhausted baseline, subject, count, merge-count, tag-time, and ref-timestamp query while other fixture data remains valid.
2. Reset shared query-error state at self-eval report start and detect errors before returning any pass result.
3. Invalidate partial Git-derived metrics, preserve structured diagnostics, and add deterministic CLI output assertions.
4. Run focused and cross-consumer regressions, host-lock validation, and independent W4b.

## Acceptance Criteria

- Three failed attempts for any direct self-eval Git query yield status error/unevaluated and structured evidence.
- No partial Git-derived metric is marked collected after a query error.
- A successful tagged window and a genuine no-tag repository keep their existing results.
- Release cadence behavior remains unchanged and all registered verification commands pass.

## Verification

- `python -m pytest tests/test_self_eval_metrics.py tests/test_release_cadence_trigger.py tests/test_semver_bump_property.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/taskset_work_gate.py --check`

## Handoff

Report failure-first evidence by query type, state isolation behavior, error schema and CLI output, successful/no-tag compatibility, cross-consumer regression results, and independent W4b.

## Stop Boundary

Stop if truthful self-eval reporting requires changing cadence thresholds, version policy, or unrelated WORK-SCHEMA metric formulas.