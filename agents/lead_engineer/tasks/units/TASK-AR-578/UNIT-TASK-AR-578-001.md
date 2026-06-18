---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-578-001
work_uid: 16d2ffe0-0fef-4fc0-97e3-f1d9373c81dc
kind: unit
parent_id: TASK-AR-578
unit_id: UNIT-TASK-AR-578-001
task_id: TASK-AR-578
task_set_id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
initiative_id: INIT-AR-DESIGN-SYSTEM-GOVERNANCE
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-18T12:51:06+09:00
updated_at: 2026-06-18T12:59:20+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-governance
created_by: codex-planner
summary: Publish design-system governance and gate
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Owner accepted the diagnosis that only color/theme is meaningfully assetized and asked for rules, gates, UIUX role refinement, and a way to propose new designs without returning to hardcoded one-off UI.
inputs:
  - docs/design/agent-runtime/DESIGN.md
  - agents/project/ORG-MODEL.yml
  - src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
  - scripts/org_model_gate.py
  - tests/test_org_model_gate.py
  - tests/test_owner_governance_chain_parity.py
target_files:
  - reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - agents/project/ORG-MODEL.yml
  - src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
  - scripts/design_system_gate.py
  - tests/test_design_system_gate.py
  - tests/test_org_model_gate.py
  - tests/test_org_read_api.py
  - tests/test_owner_governance_chain_parity.py
scope: Governance and validation only. Do not refactor src/agent_runtime/ui_console.py in this unit and do not add live agents/<role> directories.
acceptance:
  - The design-system contract separates accepted visual direction from enforceable assetization rules.
  - New visual directions have a proposal and promotion path instead of being blocked or hardcoded directly into pages.
  - The role model routes design strategy, system stewardship, screen implementation, and UX evaluation separately without live directory proliferation.
  - The gate can fail on missing artifacts or raw literals in changed UI files and can pass the current repository baseline.
verification:
  - python -m pytest tests/test_design_system_gate.py tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/design_system_gate.py --check
  - python scripts/org_model_gate.py --check
  - python scripts/org_read_api.py --view org
  - python scripts/owner_governance_gate.py
handoff: Report the created governance docs, role split, gate coverage, residual limitations, and verification results.
stop_condition: Stop after the governance docs, role metadata, gate, tests, verification evidence, and closeout records are complete.
verified_at: 2026-06-18T12:57:35+09:00
verified_by: codex-design-system-governance-578
evidence_refs:
  - reviews/VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735.json
resolution: done
completed_at: 2026-06-18T12:59:20+09:00
closed_by: codex-design-system-governance-578
actual_hours: 3.5
actual_tokens: 9000
---

# UNIT-TASK-AR-578-001 - Publish design-system governance and gate

## Context

The Owner accepted the diagnosis that only color/theme is meaningfully assetized and asked for rules, gates, UIUX role refinement, and a way to propose new designs without returning to hardcoded one-off UI.

## Inputs

- docs/design/agent-runtime/DESIGN.md
- agents/project/ORG-MODEL.yml
- src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
- scripts/org_model_gate.py
- tests/test_org_model_gate.py
- tests/test_owner_governance_chain_parity.py

## Target Files

- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- agents/project/ORG-MODEL.yml
- src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
- scripts/design_system_gate.py
- tests/test_design_system_gate.py
- tests/test_org_model_gate.py
- tests/test_org_read_api.py
- tests/test_owner_governance_chain_parity.py

## Scope

Governance and validation only. Do not refactor src/agent_runtime/ui_console.py in this unit and do not add live agents/<role> directories.

## Steps

1. Write the detailed diagnostic review with current maturity score, repo evidence, external methodology references, and recommended operating model.
2. Create DESIGN-SYSTEM.md as the rule source for token, UI component, pattern component, and one-off classification plus the new-design RFC path.
3. Extend live and template ORG-MODEL UI/UX roles while keeping legacy uiux owner aliases resolvable.
4. Add design_system_gate.py with artifact, role, and raw-literal checks suitable for watch-level governance.
5. Add focused tests for artifact coverage, gate behavior, raw literal detection, and role resolution.
6. Run the recorded verification commands and record evidence in handoff/closeout.

## Acceptance Criteria

- The design-system contract separates accepted visual direction from enforceable assetization rules.
- New visual directions have a proposal and promotion path instead of being blocked or hardcoded directly into pages.
- The role model routes design strategy, system stewardship, screen implementation, and UX evaluation separately without live directory proliferation.
- The gate can fail on missing artifacts or raw literals in changed UI files and can pass the current repository baseline.

## Verification

- `python -m pytest tests/test_design_system_gate.py tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/design_system_gate.py --check`
- `python scripts/org_model_gate.py --check`
- `python scripts/org_read_api.py --view org`
- `python scripts/owner_governance_gate.py`

## Handoff

Report the created governance docs, role split, gate coverage, residual limitations, and verification results.

## Stop Boundary

Stop after the governance docs, role metadata, gate, tests, verification evidence, and closeout records are complete.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-18T12:59:20+09:00`
- Resolution: `done`
- Actual hours: `3.5`
- Actual tokens: `9000`
- Closed by: `codex-design-system-governance-578`
- Evidence:
  - `reviews/VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735.json`
<!-- work-close:end -->
