---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-007
work_uid: daccd193-167d-448f-9c1e-f1d5bc3a0cc3
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-007
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: planned
verification_status: pending
owner: lead-engineer
created_at: 2026-07-29T23:37:32+09:00
updated_at: 2026-07-29T23:37:32+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-blocked-unit-redispatch-p0-replan.md
created_by: codex-root-v080-planner
summary: Prevent canonical taskset planning from redispatching historical blocked units
horizon: unit
model_tier: worker_standard
claim_refs: []
escalation_triggers:
  - data_integrity
  - repeated_failure
context: The T2 pre-claim plan for the newly registered portable-continuity remediation selected historical UNIT-002 because the selector treated blocked units as open and fell back to the first one when the new unit was planned rather than ready. No claim was created. This unit repairs only deterministic runnable-unit selection before any continuity implementation or consumer replay.
inputs:
  - reviews/REVIEW-2026-07-29-task-ar-648-blocked-unit-redispatch-p0-replan.md
  - agents/project/knowledge/compounds/records/COMPOUND-20260729-233830-blocked-unit-history-must-never-be-a-dispatch-fa-7dbe38c3c152.json
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-002.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-008.md
  - agent-runtime@573b3cdfbcc5e7255bbb2a503b7568e723c946a6
target_files:
  - scripts/taskset_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
  - tests/test_taskset_dispatcher.py
  - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - src/agent_runtime/templates/project/docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-007.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-007.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-007.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: Define and enforce deterministic runnable-unit selection for taskset plan/start. Prefer the task's canonical runnable unit_spec, skip blocked and other non-runnable history, fail closed when no runnable unit exists, and preserve dependency/model-routing behavior. Do not edit continuity gates, consumer repositories, or release surfaces.
acceptance:
  - A RED fixture matching TASK-AR-648 history selects blocked UNIT-002 on the rejected product.
  - After repair the same fixture selects planned UNIT-007, never any blocked predecessor.
  - A canonical task.unit_spec pointing to a runnable unit is preferred over historical siblings.
  - Selection priority is deterministic across in_progress, worker_ready/ready, planned/assigned, completed, and blocked units.
  - A task whose units are all blocked, cancelled, rejected, failed, or completed emits no claim command and exits nonzero with a stable no-runnable-unit reason.
  - Unknown or malformed unit status fails closed.
  - Unit dependency gates and model escalation use only the selected runnable unit.
  - Root and packaged taskset dispatcher copies remain byte-identical.
  - Focused W4a, full suite, and independent W4b pass on one exact product SHA with no P0/P1.
verification:
  - python -m pytest tests/test_taskset_dispatcher.py -q
  - python -m pytest tests/test_task_claim_dispatcher.py tests/test_work_registration.py tests/test_task_unit_readiness_gate.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report the exact pre-fix plan output, runnable-status matrix, canonical unit_spec precedence, no-runnable failure, dependency/routing preservation, source-template hashes, exact product SHA, focused/full counts, Compound retrieval, W4a evidence, and independent W4b verdict.
stop_condition: Stop on any blocked or ambiguous unit selection, implicit resume, unknown-status acceptance, dependency bypass, source/template drift, new P0/P1, Bean or Allimbot mutation, consumer commit, release/version/tag/package action, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-007 - Blocked Unit Redispatch Guard

## Context

The required pre-claim planner selected a frozen blocked unit instead of the
new planned continuity remediation. The claim command was not executed.

## Steps

1. Encode the exact blocked-history plus new-planned-unit RED fixture.
2. Test status priority, canonical `unit_spec`, and no-runnable failure.
3. Implement the smallest deterministic selector in source and template.
4. Prove dependency and model-routing behavior remains attached to the chosen
   unit.
5. Run focused, governance, sanitizer, and full W4a.
6. Obtain independent W4b before claiming UNIT-008.

## Deliberate Exclusions

- No continuity gate implementation.
- No Bean or Allimbot work.
- No release or external effect.

## Stop Boundary

Any plan that can emit a claim command for blocked history is terminal.
