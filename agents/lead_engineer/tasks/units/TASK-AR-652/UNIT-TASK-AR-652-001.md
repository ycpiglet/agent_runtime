---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-652-001
work_uid: 25d312f9-f462-4d50-a2c1-15370681d564
kind: unit
parent_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_id: TASK-AR-652
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T15:52:47+09:00
started_at: 2026-07-30T12:36:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Implement role-aware economic routing receipts and budget enforcement
horizon: unit
model_tier: worker_standard
escalation_triggers:
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-123600-task-ar-652-ar652001.json
context: Autofolio doctor reported six tier-equivalence warnings; codex-agent collapses all five tiers, native Codex groups worker and strong tiers, and Scribe/doc/research roles fall back to worker_standard. Pilot evidence therefore could not substantiate any savings.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - reviews/W4B-2026-07-30-unit-task-ar-652-001-final-recheck.md
  - reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-scope-amendment.md
  - scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/auto_dispatch.py
  - agents/project/ORG-MODEL.yml
target_files:
  - scripts/model_routing.py
  - src/agent_runtime/templates/project/scripts/model_routing.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/auto_dispatch.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/subagent_dispatch.py
  - src/agent_runtime/templates/project/scripts/agent_worker.py
  - src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py
  - src/agent_runtime/templates/project/scripts/eval_harness.py
  - src/agent_runtime/templates/project/scripts/verify_sdk_backend.py
  - src/agent_runtime/doctor.py
  - tests/test_model_routing.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_doctor.py
  - src/agent_runtime/templates/project/scripts/test_model_routing.py
  - src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py
  - src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py
  - src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py
  - src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
  - src/agent_runtime/templates/project/scripts/test_eval_harness.py
  - src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py
  - scripts/taskset_work_gate.py
  - src/agent_runtime/templates/project/scripts/taskset_work_gate.py
  - tests/test_taskset_work_gate.py
  - BACKLOG-BOARD.md
  - tests/fixtures/host/agent_runtime.lock.json
scope: Enforce routing and accounting truth without making a live provider call or changing provider credentials.
acceptance:
  - Cheap roles select the configured low-cost lane.
  - High tier requires a registered escalation reason.
  - Actual usage cannot be inferred from request configuration.
  - Budget enforcement survives a process restart.
verification:
  - python -m pytest tests/test_model_routing.py tests/test_task_claim_dispatcher.py tests/test_doctor.py -q
  - python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q
  - python -m pytest src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q
handoff: Attach the role matrix, execution-receipt schema, false-savings negatives, persistent-budget restart proof, template parity, and independent W4b.
stop_condition: Stop before live provider calls, credential reads, account changes, package install, or claims of economic savings without observed usage.
verified_at: 2026-07-30T15:52:47+09:00
verified_by: le-20260730-123600-kst-ar652001
evidence_refs:
  - reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730130910.json
  - reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730141633.json
  - reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730150652.json
  - reviews/W4A-2026-07-30-unit-task-ar-652-001-recheck-followup.md
  - reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730155247.json
  - reviews/W4B-2026-07-30-unit-task-ar-652-001-final-recheck.md
  - reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-scope-amendment.md
  - reviews/W4A-2026-07-30-unit-task-ar-652-001-final-followup.md
---

# UNIT-TASK-AR-652-001 - Implement role-aware economic routing receipts and budget enforcement

## Context

Autofolio doctor reported six tier-equivalence warnings; codex-agent collapses all five tiers, native Codex groups worker and strong tiers, and Scribe/doc/research roles fall back to worker_standard. Pilot evidence therefore could not substantiate any savings.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- reviews/W4B-2026-07-30-unit-task-ar-652-001-final-recheck.md
- reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-scope-amendment.md
- scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/auto_dispatch.py
- agents/project/ORG-MODEL.yml

## Target Files

- scripts/model_routing.py
- src/agent_runtime/templates/project/scripts/model_routing.py
- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/auto_dispatch.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/subagent_dispatch.py
- src/agent_runtime/templates/project/scripts/agent_worker.py
- src/agent_runtime/templates/project/scripts/codex_subagent_bridge.py
- src/agent_runtime/templates/project/scripts/eval_harness.py
- src/agent_runtime/templates/project/scripts/verify_sdk_backend.py
- src/agent_runtime/doctor.py
- tests/test_model_routing.py
- tests/test_task_claim_dispatcher.py
- tests/test_doctor.py
- src/agent_runtime/templates/project/scripts/test_model_routing.py
- src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py
- src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py
- src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py
- src/agent_runtime/templates/project/scripts/test_auto_dispatch.py
- src/agent_runtime/templates/project/scripts/test_eval_harness.py
- src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py
- scripts/taskset_work_gate.py
- src/agent_runtime/templates/project/scripts/taskset_work_gate.py
- tests/test_taskset_work_gate.py
- BACKLOG-BOARD.md
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Enforce routing and accounting truth without making a live provider call or changing provider credentials.

## Steps

1. Add failure-first tests for role fallback, false equivalence, missing observation, and cumulative budget overflow.
2. Define role-tier policy and model-plus-reasoning route identity.
3. Persist an atomic execution receipt and cumulative task/claim ledger.
4. Gate dispatch and savings claims on the receipt.
5. Prove template parity and offline provider fixtures.

## Acceptance Criteria

- Cheap roles select the configured low-cost lane.
- High tier requires a registered escalation reason.
- Actual usage cannot be inferred from request configuration.
- Budget enforcement survives a process restart.

## Verification

- `python -m pytest tests/test_model_routing.py tests/test_task_claim_dispatcher.py tests/test_doctor.py -q`
- `python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`
- `python -m pytest src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q`

## Handoff

Attach the role matrix, execution-receipt schema, false-savings negatives, persistent-budget restart proof, template parity, and independent W4b.

## Stop Boundary

Stop before live provider calls, credential reads, account changes, package install, or claims of economic savings without observed usage.
