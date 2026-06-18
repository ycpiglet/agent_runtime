---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-585-001
work_uid: c4e1afed-d93e-4c51-aa3e-68b1450f0bd0
kind: unit
parent_id: TASK-AR-585
unit_id: UNIT-TASK-AR-585-001
task_id: TASK-AR-585
task_set_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
initiative_id: INIT-AR-RELEASE-AUTOMATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-06-18T22:26:32+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Make execution gate target version parametric
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: release_execution_gate.py L109-112 hardcode target_version=='0.1.8' and target_tag=='v0.1.8', so it blocks any release past 0.1.8. release_council_gate.py already resolves the expected version from pyproject.toml via _pyproject_version and compares parametrically.
inputs:
  - scripts/release_council_gate.py (reference: _pyproject_version + resolved_expected pattern)
  - scripts/release_execution_gate.py
  - current pyproject.toml version
target_files:
  - scripts/release_execution_gate.py
  - tests/test_release_execution_gate.py
scope: Only the version-equality checks and any v0.1.8-pinned DEFAULT_* paths. Leave route logic (release_route assignments) and approval-status handling untouched.
acceptance:
  - No '0.1.8' literal remains in the gate evaluation logic.
  - Parametric pass + mismatch-block tests both green.
verification:
  - python -m pytest tests/test_release_execution_gate.py -q
handoff: Gate is version-parametric; hand to unit 2 (auto-release path) which depends on a working execution gate.
stop_condition: Stop if changing the version checks would require altering approval-route semantics; flag for review instead.
---

# UNIT-TASK-AR-585-001 - Make execution gate target version parametric

## Context

release_execution_gate.py L109-112 hardcode target_version=='0.1.8' and target_tag=='v0.1.8', so it blocks any release past 0.1.8. release_council_gate.py already resolves the expected version from pyproject.toml via _pyproject_version and compares parametrically.

## Inputs

- scripts/release_council_gate.py (reference: _pyproject_version + resolved_expected pattern)
- scripts/release_execution_gate.py
- current pyproject.toml version

## Target Files

- scripts/release_execution_gate.py
- tests/test_release_execution_gate.py

## Scope

Only the version-equality checks and any v0.1.8-pinned DEFAULT_* paths. Leave route logic (release_route assignments) and approval-status handling untouched.

## Steps

1. Add a pyproject version resolver (reuse or mirror release_council_gate._pyproject_version).
2. Replace the hardcoded target_version/target_tag equality checks with: target_version == resolved package version, target_tag == 'v'+target_version.
3. Re-point any DEFAULT decision/output paths that are pinned to a v0.1.8 filename to be parametric or generic.
4. Update tests: one fixture at the current version passes; a mismatched-version fixture blocks.
5. Run the gate tests and owner_governance_gate.

## Acceptance Criteria

- No '0.1.8' literal remains in the gate evaluation logic.
- Parametric pass + mismatch-block tests both green.

## Verification

- `python -m pytest tests/test_release_execution_gate.py -q`

## Handoff

Gate is version-parametric; hand to unit 2 (auto-release path) which depends on a working execution gate.

## Stop Boundary

Stop if changing the version checks would require altering approval-route semantics; flag for review instead.
