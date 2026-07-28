---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-646
display_id: TASK-AR-646
task_uid: 81681d8c-8cc3-48e9-a5fd-b030e01f4f08
work_id: TASK-AR-646
work_uid: 81681d8c-8cc3-48e9-a5fd-b030e01f4f08
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T07:35:20+09:00
started_at: 2026-07-29T06:42:09+09:00
title: Make model routing economically effective and auditable
status: in_progress
priority: P0
difficulty: L
est_hours: 10
est_tokens: 24000
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-646/UNIT-TASK-AR-646-001.md
reservation_id: RES-20260728-163601-b8c2a87a-08
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Make routine native/provider delegation low-cost by default and prove the resolved and observed execution instead of trusting semantic tier labels.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-064209-task-ar-646-0823.json
verification_status: passed
verified_at: 2026-07-29T07:35:20+09:00
verified_by: le-20260729-kst-646001
evidence_refs:
  - reviews/VERIFY-2026-07-29-task-ar-646-20260729073326.json
  - reviews/VERIFY-2026-07-29-task-ar-646-20260729073520.json
---

# TASK-AR-646 - Make model routing economically effective and auditable

## Goal

- Use lower-cost native subagents by default where appropriate and prove when escalation actually changed the invoked model.

## Scope

- Resolve provider capabilities at the real claim, provider, and native-session dispatch boundaries; enforce deterministic-first delegation; record execution/usage truth; and block false cost-saving claims.

## Acceptance Criteria

- Newly registered precise routine units default to `worker_low`; explicit ambiguity, data-integrity, security, cross-cutting, external-effect, high-risk, or repeated-failure signals visibly escalate.
- Equivalent or unresolved provider tier mappings are reported as ineffective/unverified and cannot contribute to savings claims.
- Every generic, provider-worker, and native-session subagent dispatch records its reason, requested/selected tier, resolved/observed model, escalation signal, deterministic preflight, latency, and actual usage/cost availability.
- Lookup-only work cannot emit a model dispatch until deterministic tools are recorded as insufficient; sufficient deterministic work emits no call.
- Runtime uses the provider/native subagent execution surface rather than rebuilding an executor.
- Monetary savings are verified only from comparable billed-cost evidence; token deltas remain explicitly labeled token evidence.

## Verification

- `python -m pytest tests/test_model_routing.py tests/test_work_registration.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_provider_import_contract.py tests/test_template_smoke.py -q`
- `python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python -m pytest -q`
