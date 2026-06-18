---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-578
display_id: TASK-AR-578
task_uid: f7cbe326-b1f6-4237-8e8a-1d8e0a87fa61
work_id: TASK-AR-578
work_uid: f7cbe326-b1f6-4237-8e8a-1d8e0a87fa61
kind: task
parent_id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
registered_at: 2026-06-18T12:51:06+09:00
started_at: 2026-06-18T12:52:20+09:00
created_at: 2026-06-18T12:51:06+09:00
updated_at: 2026-06-18T13:01:58+09:00
title: Publish design-system governance and gate
status: completed
priority: P0
difficulty: M
est_hours: 4
est_tokens: 7000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-DESIGN-SYSTEM-GOVERNANCE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-578/UNIT-TASK-AR-578-001.md
reservation_id: RES-20260618-125106-6b52d53e-01
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-governance
created_by: codex-planner
summary: Create durable design-system governance for Agent Runtime UI work: a diagnostic report, system contract, assetization rules, UI/UX role split, and a deterministic gate with tests.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_design_system_gate.py tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/design_system_gate.py --check
  - python scripts/org_model_gate.py --check
  - python scripts/org_read_api.py --view org
  - python scripts/owner_governance_gate.py
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-18T12:59:14+09:00
verified_by: independent-auditor-design-system-578
evidence_refs:
  - reviews/VERIFY-2026-06-18-task-ar-578-20260618130030.json
resolution: done
completed_at: 2026-06-18T13:01:58+09:00
closed_by: codex-design-system-governance-578
actual_hours: 3.5
actual_tokens: 9000
---

# TASK-AR-578 - Publish design-system governance and gate

## Goal

- Create durable design-system governance for Agent Runtime UI work: a diagnostic report, system contract, assetization rules, UI/UX role split, and a deterministic gate with tests.

## Scope

- Add documentation, role metadata, a read-only gate, and focused tests. Do not rewrite the UI console or create live per-role directories in this checkout.

## Acceptance Criteria

- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md records the current maturity diagnosis, root causes, and recommended operating model.
- docs/design/agent-runtime/DESIGN-SYSTEM.md defines token/component/pattern/one-off classification, new-design proposal workflow, implementation rules, and closeout evidence requirements.
- ORG-MODEL live and template overlays include focused UI/UX roles for lead-designer, design-system-steward, interface-designer, and ux-evaluator while preserving legacy uiux aliases.
- scripts/design_system_gate.py reports raw literal usage and required governance artifacts without mutating files, with focused tests proving pass/fail behavior.

## Verification

- `python -m pytest tests/test_design_system_gate.py tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/design_system_gate.py --check`
- `python scripts/org_model_gate.py --check`
- `python scripts/org_read_api.py --view org`
- `python scripts/owner_governance_gate.py`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-18T13:01:58+09:00`
- Resolution: `done`
- Actual hours: `3.5`
- Actual tokens: `9000`
- Closed by: `codex-design-system-governance-578`
- Evidence:
  - `reviews/VERIFY-2026-06-18-task-ar-578-20260618130030.json`
<!-- work-close:end -->
