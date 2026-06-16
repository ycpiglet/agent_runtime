---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-570-001
work_uid: 843b0ea1-d801-415b-9161-6cfdb1517f5b
kind: unit
parent_id: TASK-AR-570
unit_id: UNIT-TASK-AR-570-001
task_id: TASK-AR-570
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
initiative_id: INIT-AR-SELF-IMPROVEMENT-CADENCE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-06-17T08:31:23+09:00
updated_at: 2026-06-17T08:31:23+09:00
origin_type: owner_request
origin_ref: owner-request:low-frequency-agent-skill-self-improvement-cycle
created_by: codex-planner
summary: Build self-improvement metrics baseline
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Existing collaboration_governance_gate.py reports role claim gaps, runtime_asset_usage.py reports asset usage, scribe_due.py and doc_steward_due.py expose advisory cadence. Combine these into one evidence-based baseline for the Owner's low-frequency agent/skill objective.
inputs:
  - agents/project/COLLABORATION-GOVERNANCE.json
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - agents/runtime/task_claims/*.json
  - scripts/collaboration_governance_gate.py
  - scripts/runtime_asset_usage.py
  - scripts/scribe_due.py
  - scripts/doc_steward_due.py
target_files:
  - scripts/self_improvement_cycle.py
  - tests/test_self_improvement_cycle.py
scope: Add a read-mostly assessment command and focused tests. Do not remove existing waivers or fabricate role claim evidence.
acceptance:
  - JSON output contains role_gaps, asset_gaps, advisory_signals, score, and maturity_level.
  - The current repo baseline exposes scribe waiver debt and monitored role gaps without failing unrelated lifecycle watches.
  - Tests exercise fixture policies/assets and deterministic score calculation.
verification:
  - python -m pytest tests/test_self_improvement_cycle.py -q
  - python scripts/self_improvement_cycle.py assess --json
handoff: Report baseline metrics and the exact low-frequency roles/assets that need the next cycle.
stop_condition: Stop after the baseline command and tests pass; do not start artifact-generation work without the next unit claim.
---

# UNIT-TASK-AR-570-001 - Build self-improvement metrics baseline

## Context

Existing collaboration_governance_gate.py reports role claim gaps, runtime_asset_usage.py reports asset usage, scribe_due.py and doc_steward_due.py expose advisory cadence. Combine these into one evidence-based baseline for the Owner's low-frequency agent/skill objective.

## Inputs

- agents/project/COLLABORATION-GOVERNANCE.json
- agents/project/RUNTIME-ASSET-REGISTRY.json
- agents/runtime/task_claims/*.json
- scripts/collaboration_governance_gate.py
- scripts/runtime_asset_usage.py
- scripts/scribe_due.py
- scripts/doc_steward_due.py

## Target Files

- scripts/self_improvement_cycle.py
- tests/test_self_improvement_cycle.py

## Scope

Add a read-mostly assessment command and focused tests. Do not remove existing waivers or fabricate role claim evidence.

## Steps

1. Load collaboration governance findings and runtime asset metrics through their public analyze functions.
2. Capture scribe/doc-steward advisory status without making them blocking gates.
3. Classify each role or asset issue as missing_claim_evidence, waiver_debt, low_reuse, advisory_due, or lifecycle_watch.
4. Emit JSON and human-readable summaries with counts and maturity score inputs.

## Acceptance Criteria

- JSON output contains role_gaps, asset_gaps, advisory_signals, score, and maturity_level.
- The current repo baseline exposes scribe waiver debt and monitored role gaps without failing unrelated lifecycle watches.
- Tests exercise fixture policies/assets and deterministic score calculation.

## Verification

- `python -m pytest tests/test_self_improvement_cycle.py -q`
- `python scripts/self_improvement_cycle.py assess --json`

## Handoff

Report baseline metrics and the exact low-frequency roles/assets that need the next cycle.

## Stop Boundary

Stop after the baseline command and tests pass; do not start artifact-generation work without the next unit claim.
