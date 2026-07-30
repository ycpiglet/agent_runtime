---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-652
display_id: TASK-AR-652
task_uid: 806b6496-dcd9-4b7a-8236-7a3fd8673df0
work_id: TASK-AR-652
work_uid: 806b6496-dcd9-4b7a-8236-7a3fd8673df0
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T12:38:00+09:00
started_at: 2026-07-30T12:36:00+09:00
title: Bind model tiers to actual execution and economic receipts
status: active
priority: P1
difficulty: L
est_hours: 14
est_tokens: 28000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-652/UNIT-TASK-AR-652-001.md
reservation_id: RES-20260730-112500-842c7890-01
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Make selective subagent routing materially change execution and produce trustworthy task-level token and cost evidence.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-123600-task-ar-652-ar652001.json
acceptance:
  - Scribe, exploration, implementation, review, and audit roles resolve through explicit role policy rather than the generic fallback.
  - Requested tier, resolved model and reasoning, observed model and reasoning, tokens, cost, and source are persisted in one immutable execution receipt.
  - Native equivalence compares model and reasoning effort; provider mappings that collapse remain visibly ineligible.
  - Task and claim budget checks use persistent cumulative usage and block an unaffordable dispatch before a provider call.
  - Savings remain unavailable without an observed comparable baseline.
verification:
  - python -m pytest tests/test_model_routing.py tests/test_task_claim_dispatcher.py tests/test_doctor.py -q
  - python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q
  - python -m pytest src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q
  - python scripts/runtime_asset_usage.py --check
---

# TASK-AR-652 - Bind model tiers to actual execution and economic receipts

## Goal

- Make selective subagent routing materially change execution and produce trustworthy task-level token and cost evidence.

## Scope

- Add canonical role-tier defaults, provider/native application receipts, model-and-reasoning equivalence, persistent task budgets, and savings eligibility gates.

## Acceptance Criteria

- Scribe, exploration, implementation, review, and audit roles resolve through explicit role policy rather than the generic fallback.
- Requested tier, resolved model and reasoning, observed model and reasoning, tokens, cost, and source are persisted in one immutable execution receipt.
- Native equivalence compares model and reasoning effort; provider mappings that collapse remain visibly ineligible.
- Task and claim budget checks use persistent cumulative usage and block an unaffordable dispatch before a provider call.
- Savings remain unavailable without an observed comparable baseline.

## Verification

- `python -m pytest tests/test_model_routing.py tests/test_task_claim_dispatcher.py tests/test_doctor.py -q`
- `python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`
- `python -m pytest src/agent_runtime/templates/project/scripts/test_verify_sdk_backend.py -q`
- `python scripts/runtime_asset_usage.py --check`
