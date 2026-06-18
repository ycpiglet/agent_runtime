---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-575-001
work_uid: 7a507e0a-3960-4912-a732-62cbbd812a8a
kind: unit
parent_id: TASK-AR-575
unit_id: UNIT-TASK-AR-575-001
task_id: TASK-AR-575
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
initiative_id: INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-06-17T17:15:00+09:00
updated_at: 2026-06-17T18:09:03+09:00
origin_type: owner_request
origin_ref: reviews/REPORT-2026-06-17-self-improvement-maturity.md
created_by: codex-planner
summary: Burn down runtime asset low-reuse debt
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The maturity report shows low_reuse_assets 17 against target_next 8 and mature target 2. This unit should prioritize real workflow exercise or explicit lifecycle decisions.
inputs:
  - reviews/REPORT-2026-06-17-self-improvement-maturity.md
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - scripts/runtime_asset_usage.py
target_files:
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - OPS-COMMAND-REFERENCE.md
  - reviews
  - scripts/runtime_asset_usage.py
  - reviews/INDEX.md
scope: Review low-reuse assets and create real usage or lifecycle decisions. Keep unrelated registry refactors out of scope.
acceptance:
  - At least five low-reuse assets have real evidence or lifecycle decisions.
  - The asset_gaps or low_reuse_assets metric decreases, or a blocker review explains why not.
  - No asset is deprecated without owner-facing rationale.
verification:
  - python scripts/runtime_asset_usage.py --check
  - python scripts/self_improvement_cycle.py assess
  - python scripts/evidence_index_generator.py --check
handoff: Report asset_gaps and low_reuse_assets before/after plus changed evidence paths.
stop_condition: Stop after asset debt changes are measurable and indexed.
verified_at: 2026-06-17T18:09:03+09:00
verified_by: release-steward-20260617-runtime-assets-575
evidence_refs:
  - reviews/VERIFY-2026-06-17-unit-task-ar-575-001-20260617180903.json
---

# UNIT-TASK-AR-575-001 - Burn down runtime asset low-reuse debt

## Context

The maturity report shows low_reuse_assets 17 against target_next 8 and mature target 2. This unit should prioritize real workflow exercise or explicit lifecycle decisions.

## Inputs

- reviews/REPORT-2026-06-17-self-improvement-maturity.md
- agents/project/RUNTIME-ASSET-REGISTRY.json
- scripts/runtime_asset_usage.py

## Target Files

- agents/project/RUNTIME-ASSET-REGISTRY.json
- OPS-COMMAND-REFERENCE.md
- reviews
- scripts/runtime_asset_usage.py
- reviews/INDEX.md

## Scope

Review low-reuse assets and create real usage or lifecycle decisions. Keep unrelated registry refactors out of scope.

## Steps

1. Run runtime_asset_usage.py and rank low-reuse assets by owner value.
2. For each selected asset, either exercise it in a real workflow or document a lifecycle decision.
3. Update registry/docs only when the decision changes the durable contract.
4. Re-run usage and self-improvement assessment.

## Acceptance Criteria

- At least five low-reuse assets have real evidence or lifecycle decisions.
- The asset_gaps or low_reuse_assets metric decreases, or a blocker review explains why not.
- No asset is deprecated without owner-facing rationale.

## Verification

- `python scripts/runtime_asset_usage.py --check`
- `python scripts/self_improvement_cycle.py assess`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Report asset_gaps and low_reuse_assets before/after plus changed evidence paths.

## Stop Boundary

Stop after asset debt changes are measurable and indexed.