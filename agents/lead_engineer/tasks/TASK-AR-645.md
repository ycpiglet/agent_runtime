---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-645
display_id: TASK-AR-645
task_uid: 597a2696-5178-4273-ba48-be16e0f632be
work_id: TASK-AR-645
work_uid: 597a2696-5178-4273-ba48-be16e0f632be
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T06:03:29+09:00
started_at: 2026-07-29T03:43:12+09:00
title: Make compound and scribe task-linked and host-configurable
status: completed
priority: P0
difficulty: L
est_hours: 12
est_tokens: 26000
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-645/UNIT-TASK-AR-645-002.md
reservation_id: RES-20260728-163601-b8c2a87a-07
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Prevent repeated mistakes and accumulated context without forcing every host into one monolithic status format.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.json
  - agents/runtime/task_claims/CLAIM-20260729-045949-task-ar-645-645002.json
verification_status: passed
verified_at: 2026-07-29T05:46:20+09:00
verified_by: codex-root-v080-orchestrator
evidence_refs:
  - reviews/VERIFY-2026-07-29-task-ar-645-20260729054620.json
review_refs:
  - reviews/W4B-2026-07-29-unit-task-ar-645-001.md
  - reviews/W4B-2026-07-29-unit-task-ar-645-002.md
  - reviews/RETRO-2026-07-29-task-ar-645-compound-scribe.md
compound_refs:
  - agents/project/knowledge/compounds/records/COMPOUND-20260729-054610-source-layout-cli-verification-must-declare-pyth-b7ebc6c5875c.json
resolution: done
completed_at: 2026-07-29T06:03:29+09:00
closed_by: codex-root-v080-orchestrator
measurement_unavailable_reason: Exact per-task hours and tokens were not captured by the current runtime telemetry.
---

# TASK-AR-645 - Make compound and scribe task-linked and host-configurable

## Goal

- Prevent repeated mistakes and accumulated context without forcing every host into one monolithic status format.

## Scope

- Introduce per-entry compound records, task/signature linkage, start/failure lookup, and configurable scribe state adapters with generated summaries.

## Acceptance Criteria

- A repeated defect produces a task-linked compound record and a later matching task surfaces it.
- Closure accepts only compound/review evidence linked to the current task or defect signature.
- Scribe reads host-configured status sources and emits generated projections.
- Live host data is seed_once or host_owned, never permanently managed.

## Verification

- `python -m pytest tests/test_compound_records.py tests/test_task_claim_dispatcher.py tests/test_closure_gate.py tests/test_compound_cadence_gate.py tests/test_compound_cadence_obligation.py tests/test_scribe_due.py tests/test_config_v2.py tests/test_doctor.py tests/test_session_continuity_hooks.py tests/test_inventory_sync_sanitize.py tests/test_adoption.py tests/test_work_schema_gate.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`
- `PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check`
- `python -m pytest -q`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-29T06:03:29+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Exact per-task hours and tokens were not captured by the current runtime telemetry.
- Closed by: `codex-root-v080-orchestrator`
- Verification evidence:
  - `reviews/VERIFY-2026-07-29-task-ar-645-20260729054620.json`
- Reviews:
  - `reviews/W4B-2026-07-29-unit-task-ar-645-001.md`
  - `reviews/W4B-2026-07-29-unit-task-ar-645-002.md`
  - `reviews/RETRO-2026-07-29-task-ar-645-compound-scribe.md`
- Compounds:
  - `agents/project/knowledge/compounds/records/COMPOUND-20260729-054610-source-layout-cli-verification-must-declare-pyth-b7ebc6c5875c.json`
<!-- work-close:end -->