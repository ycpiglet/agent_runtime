---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-639-002
work_uid: 3c232b37-d686-4861-b0be-7930a078b3df
kind: unit
parent_id: TASK-AR-639
unit_id: UNIT-TASK-AR-639-002
task_id: TASK-AR-639
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T19:08:33+09:00
started_at: 2026-07-28T17:55:15+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Block task-claim-projection split-brain and support explicit recovery
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The current checkout had an implementation commit and passed unit verification while task/unit/pointer/claim surfaces disagreed. Existing state_sync_gate passed because it did not correlate these sources.
inputs:
  - scripts/state_sync_gate.py
  - scripts/task_claim_dispatcher.py
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/lead_engineer/tasks/TASK-AR-631.md
  - reviews/REVIEW-2026-07-28-task-ar-639-unit-002-t3-replan.md
target_files:
  - scripts/state_sync_gate.py
  - scripts/task_claim_dispatcher.py
  - scripts/work_schema_gate.py
  - tests/test_state_sync_gate.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_work_schema_gate.py
  - agents/project/WORK-SCHEMA.yml
  - src/agent_runtime/templates/project/scripts/state_sync_gate.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/work_schema_gate.py
  - src/agent_runtime/templates/project/agents/project/WORK-SCHEMA.yml
  - agents/lead_engineer/tasks/TASK-AR-631.md
  - agents/lead_engineer/tasks/units/TASK-AR-631/UNIT-TASK-AR-631-001.md
scope: Correlate active/implemented work with task, unit, claim, verification, branch, worktree, pointer, and generated state; define and exercise a loud recovery marker for pre-existing missing-claim history; catalog recovery and unavailable-measurement provenance in root and consumer schemas. Do not retroactively create claims or close TASK-AR-631 before the new recovery contract is independently verified.
acceptance:
  - The pre-fix TASK-AR-631 shape blocks.
  - A correctly claimed active task passes.
  - An explicitly recovered historical task passes with a visible watch signal.
  - Pointer and UI projections cannot claim no open work while a tracked implementation is in flight.
  - Worker claims missing task/unit, branch/worktree, pointer, or verification correlation block while explicit overlay claims do not inherit worker-only requirements.
  - TASK-AR-631 carries recovery reason and independent evidence without a fabricated claim.
  - Recovery and measurement-unavailable fields are cataloged without unknown-field warnings in root and consumer schema gates.
verification:
  - python -m pytest tests/test_state_sync_gate.py tests/test_task_claim_dispatcher.py tests/test_work_schema_gate.py -q
  - python scripts/state_sync_gate.py --check
  - python scripts/work_schema_gate.py --items --check
handoff: Provide the contradiction matrix, recovery schema, and governance-chain result.
stop_condition: Stop before inventing a generic event-sourcing migration or mutating completed historical claims.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-175515-task-ar-639-639002.json
verified_at: 2026-07-28T18:46:25+09:00
verified_by: le-20260728-task-ar-639-002-terra
evidence_refs:
  - reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728181538.json
  - reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728183121.json
  - reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728183401.json
  - reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728184625.json
  - reviews/W4B-2026-07-28-unit-task-ar-639-002-recheck-2.md
resolution: done
completed_at: 2026-07-28T19:08:33+09:00
closed_by: codex-root-v080-w6
measurement_unavailable_reason: Work spanned repeated adversarial W4b repairs, CI, claim release, and manual lifecycle projection before reliable per-unit time and token metering was available.
---

# UNIT-TASK-AR-639-002 - Block task-claim-projection split-brain and support explicit recovery

## Context

The current checkout had an implementation commit and passed unit verification while task/unit/pointer/claim surfaces disagreed. Existing state_sync_gate passed because it did not correlate these sources.

## Inputs

- scripts/state_sync_gate.py
- scripts/task_claim_dispatcher.py
- agents/project/NEXT-SESSION-POINTER.yml
- agents/lead_engineer/tasks/TASK-AR-631.md
- reviews/REVIEW-2026-07-28-task-ar-639-unit-002-t3-replan.md

## Target Files

- scripts/state_sync_gate.py
- scripts/task_claim_dispatcher.py
- scripts/work_schema_gate.py
- tests/test_state_sync_gate.py
- tests/test_task_claim_dispatcher.py
- tests/test_work_schema_gate.py
- agents/project/WORK-SCHEMA.yml
- src/agent_runtime/templates/project/scripts/state_sync_gate.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/work_schema_gate.py
- src/agent_runtime/templates/project/agents/project/WORK-SCHEMA.yml
- agents/lead_engineer/tasks/TASK-AR-631.md
- agents/lead_engineer/tasks/units/TASK-AR-631/UNIT-TASK-AR-631-001.md

## Scope

Correlate active/implemented work with task, unit, claim, verification, branch,
worktree, pointer, and generated state; define and exercise a loud recovery
marker for pre-existing missing-claim history; catalog recovery and
unavailable-measurement provenance in root and consumer schemas. Do not
retroactively create claims or close TASK-AR-631 before the new recovery
contract is independently verified.

## Steps

1. Add fixtures for the TASK-AR-631 contradiction.
2. Define blocking findings for impossible active and completed combinations.
3. Define an explicit recovered-without-claim record shape and reason.
4. Distinguish worker claims from explicit overlay claims.
5. Register recovery and measurement-unavailable fields in root and consumer schemas.
6. Apply the recovery marker to TASK-AR-631 from its durable W4a/W4b evidence.
7. Wire the reconciliation result into the governance chain.

## Acceptance Criteria

- The pre-fix TASK-AR-631 shape blocks.
- A correctly claimed active task passes.
- An explicitly recovered historical task passes with a visible watch signal.
- Pointer and UI projections cannot claim no open work while a tracked implementation is in flight.
- Worker claims missing task/unit, branch/worktree, pointer, or verification correlation block while explicit overlay claims do not inherit worker-only requirements.
- TASK-AR-631 carries recovery reason and independent evidence without a fabricated claim.
- Recovery and measurement-unavailable fields are cataloged without unknown-field warnings in root and consumer schema gates.

## Verification

- `python -m pytest tests/test_state_sync_gate.py tests/test_task_claim_dispatcher.py tests/test_work_schema_gate.py -q`
- `python scripts/state_sync_gate.py --check`
- `python scripts/work_schema_gate.py --items --check`

## Handoff

Provide the contradiction matrix, recovery schema, and governance-chain result.

## Stop Boundary

Stop before inventing a generic event-sourcing migration or mutating completed historical claims.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-28T19:08:33+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Work spanned repeated adversarial W4b repairs, CI, claim release, and manual lifecycle projection before reliable per-unit time and token metering was available.
- Closed by: `codex-root-v080-w6`
- Evidence:
  - `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728181538.json`
  - `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728183121.json`
  - `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728183401.json`
  - `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728184625.json`
  - `reviews/W4B-2026-07-28-unit-task-ar-639-002-recheck-2.md`
<!-- work-close:end -->
