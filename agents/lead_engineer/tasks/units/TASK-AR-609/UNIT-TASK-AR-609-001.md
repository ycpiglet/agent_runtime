---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-609-001
work_uid: 6a327608-a0ff-45ad-97be-6e3f8017a0e9
kind: unit
parent_id: TASK-AR-609
unit_id: UNIT-TASK-AR-609-001
task_id: TASK-AR-609
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-23T07:31:44+09:00
started_at: 2026-07-23T07:17:12+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Filter classifier initiative collection by record kind
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - cross_cutting
context: GitHub issue 300 shows _initiative_records reads mixed records from the initiatives directory without checking kind and falls back to a taskset filename stem, duplicating IDs across hierarchy levels while reporting pass.
inputs:
  - reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
  - scripts/work_item_classifier.py
target_files:
  - scripts/work_item_classifier.py
  - src/agent_runtime/templates/project/scripts/work_item_classifier.py
  - tests/test_work_item_classifier.py
  - tests/test_template_work_item_classifier.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Filter initiative collection by canonical kind/type and use id/work_id deterministically. Do not restructure storage directories or change task/taskset numbering.
acceptance:
  - Taskset records never appear as initiatives.
  - Legitimate initiative records retain stable IDs and titles.
  - Classifier and template tests pass with no semantic duplicates.
verification:
  - python -m pytest tests/test_work_item_classifier.py tests/test_template_work_item_classifier.py -q
  - python scripts/work_item_classifier.py --write --check
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report mixed-fixture counts, duplicate oracle, generated view impact, and GitHub issue 300 evidence.
stop_condition: Stop before moving canonical records or changing hierarchy semantics beyond the kind filter.
verified_at: 2026-07-23T07:31:44+09:00
verified_by: codex-root-task-ar-609
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723072326.json
  - reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723073123.json
  - reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723073144.json
---

# UNIT-TASK-AR-609-001 - Filter classifier initiative collection by record kind

## Context

GitHub #300 shows _initiative_records reads mixed records from the initiatives directory without checking kind and falls back to a taskset filename stem, duplicating IDs across hierarchy levels while reporting pass.

## Inputs

- reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
- scripts/work_item_classifier.py

## Target Files

- scripts/work_item_classifier.py
- src/agent_runtime/templates/project/scripts/work_item_classifier.py
- tests/test_work_item_classifier.py
- tests/test_template_work_item_classifier.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Filter initiative collection by canonical kind/type and use id/work_id deterministically. Do not restructure storage directories or change task/taskset numbering.

## Steps

1. Add a mixed-record failure-first fixture and duplicate oracle.
2. Implement kind-aware collection in the root/template pair.
3. Regenerate derived views and the host lock.

## Acceptance Criteria

- Taskset records never appear as initiatives.
- Legitimate initiative records retain stable IDs and titles.
- Classifier and template tests pass with no semantic duplicates.

## Verification

- `python -m pytest tests/test_work_item_classifier.py tests/test_template_work_item_classifier.py -q`
- `python scripts/work_item_classifier.py --write --check`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report mixed-fixture counts, duplicate oracle, generated view impact, and issue #300 evidence.

## Stop Boundary

Stop before moving canonical records or changing hierarchy semantics beyond the kind filter.