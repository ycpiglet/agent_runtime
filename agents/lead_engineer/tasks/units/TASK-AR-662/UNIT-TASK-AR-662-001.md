---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-662-001
work_uid: 2f600391-e43a-462c-ba48-46f198d0bc5c
kind: unit
parent_id: TASK-AR-662
unit_id: UNIT-TASK-AR-662-001
task_id: TASK-AR-662
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Add semantic integration and independent baseline controls
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-661-001
escalation_triggers:
context: Bean Wiki demonstrated that ordinary CI can remain green while navigation, design, or responsive behavior regresses after parallel integration.
inputs:
  - scripts/owner_governance_gate.py
  - new:scripts/review_claim_gate.py
  - new:scripts/verification_decision_gate.py
  - reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
target_files:
  - new:scripts/semantic_integration_gate.py
  - new:scripts/baseline_governance.py
  - scripts/owner_governance_gate.py
  - new:scripts/review_claim_gate.py
  - new:scripts/verification_decision_gate.py
  - new:tests/test_semantic_integration_gate.py
  - new:tests/test_baseline_governance.py
  - new:tests/test_verifier_attestation.py
  - new:docs/semantic-integration-contract.md
scope: Define repository-configurable critical journeys, design contracts, responsive/accessibility evidence, verifier provenance, and protected baseline approval. Do not encode one product's UI into core defaults.
acceptance:
  - Known green-but-wrong fixtures fail.
  - Baseline changes cannot self-approve.
  - Non-UI repositories can configure equivalent domain contracts without visual tooling.
  - Verifier evidence names actor, tools, inputs, and exact commit.
verification:
  - python -m pytest -q tests/test_semantic_integration_gate.py tests/test_baseline_governance.py tests/test_verifier_attestation.py
handoff: Provide a green-unit/red-journey fixture, baseline-approval matrix, and exact-SHA verifier evidence.
stop_condition: Stop before globally requiring a product-specific browser or screenshot stack.
---

# UNIT-TASK-AR-662-001 - Add semantic integration and independent baseline controls

## Context

Bean Wiki demonstrated that ordinary CI can remain green while navigation, design, or responsive behavior regresses after parallel integration.

## Inputs

- scripts/owner_governance_gate.py
- new:scripts/review_claim_gate.py
- new:scripts/verification_decision_gate.py
- reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md

## Target Files

- new:scripts/semantic_integration_gate.py
- new:scripts/baseline_governance.py
- scripts/owner_governance_gate.py
- new:scripts/review_claim_gate.py
- new:scripts/verification_decision_gate.py
- new:tests/test_semantic_integration_gate.py
- new:tests/test_baseline_governance.py
- new:tests/test_verifier_attestation.py
- new:docs/semantic-integration-contract.md

## Scope

Define repository-configurable critical journeys, design contracts, responsive/accessibility evidence, verifier provenance, and protected baseline approval. Do not encode one product's UI into core defaults.

## Steps

1. Define semantic assertions that cannot be replaced by snapshots.
2. Bind journey and verifier evidence to the candidate SHA.
3. Require independent approval and rationale for baseline updates.
4. Detect incompatible ownership of shared design contracts.
5. Integrate blocking results into the merge attestation.

## Acceptance Criteria

- Known green-but-wrong fixtures fail.
- Baseline changes cannot self-approve.
- Non-UI repositories can configure equivalent domain contracts without visual tooling.
- Verifier evidence names actor, tools, inputs, and exact commit.

## Verification

- `python -m pytest -q tests/test_semantic_integration_gate.py tests/test_baseline_governance.py tests/test_verifier_attestation.py`

## Handoff

Provide a green-unit/red-journey fixture, baseline-approval matrix, and exact-SHA verifier evidence.

## Stop Boundary

Stop before globally requiring a product-specific browser or screenshot stack.
