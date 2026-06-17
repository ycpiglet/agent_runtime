---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-577-001
work_uid: a1952521-fa6b-4419-99aa-755fd5681cff
kind: unit
parent_id: TASK-AR-577
unit_id: UNIT-TASK-AR-577-001
task_id: TASK-AR-577
task_set_id: TASKSET-AR-BUSINESS-OPERATIONS-TEAMS
initiative_id: INIT-AR-BUSINESS-OPERATIONS-TEAMS
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-17T22:10:00+09:00
updated_at: 2026-06-17T22:34:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-17-business-operations-teams
created_by: codex-planner
summary: Publish business operations org model
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Owner wants accounting, marketing, and sales teams that can guide product monetization, asset management, and go-to-market work when this runtime is used to build products. The chosen policy is mixed B2B SaaS plus content/partner growth, with compliant automation only.
inputs:
  - agents/project/ORG-MODEL.yml
  - agents/project/TEAMS.md
  - agents/project/ORG.md
  - agents/project/PROJECT-CONTEXT.yml
  - src/agent_runtime/templates/project/agents/project/ORG.md
  - src/agent_runtime/templates/project/agents/project/TEAMS.md
  - src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml
target_files:
  - agents/project/ORG-MODEL.yml
  - agents/project/TEAMS.md
  - agents/project/ORG.md
  - agents/project/PROJECT-CONTEXT.yml
  - src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
  - src/agent_runtime/templates/project/agents/project/ORG.md
  - src/agent_runtime/templates/project/agents/project/TEAMS.md
  - src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml
  - tests/test_org_model_gate.py
  - tests/test_org_read_api.py
  - tests/test_owner_governance_chain_parity.py
scope: Add business-side teams and focused validation only. Keep live checkout roles as ORG-MODEL metadata rather than new agents/<role> directories. Keep external-system execution, payment integration, CRM sync, posting bots, and traffic automation out of scope.
acceptance:
  - The new roles resolve through org_model_gate without underscore canonical ids.
  - org_read_api.org_tree contains the three new team keys even with no live instances.
  - Template docs provide the same business-team starter defaults.
  - Sales automation text states compliant automation only and rejects viewbots, fake traffic, unauthorized bulk posting, spam, and platform manipulation.
verification:
  - python -m pytest tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_project_context_overlay.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/org_model_gate.py --check
  - python scripts/org_read_api.py --view org
  - python scripts/owner_governance_gate.py
handoff: Report the added teams/roles, template coverage, explicit prohibited growth automation, and verification results.
stop_condition: Stop after the business operations org model is registered, implemented, verified, and closed with W4/W5/W6 evidence.
verified_at: 2026-06-17T22:32:00+09:00
verified_by: lead-engineer-20260617-business-ops-577
evidence_refs:
  - reviews/VERIFY-2026-06-17-unit-task-ar-577-001-20260617223200.json
resolution: done
completed_at: 2026-06-17T22:34:00+09:00
closed_by: lead-engineer-20260617-business-ops-577
actual_hours: 2.2
actual_tokens: 5400
---

# UNIT-TASK-AR-577-001 - Publish business operations org model

## Context

The Owner wants accounting, marketing, and sales teams that can guide product monetization, asset management, and go-to-market work when this runtime is used to build products. The chosen policy is mixed B2B SaaS plus content/partner growth, with compliant automation only.

## Inputs

- agents/project/ORG-MODEL.yml
- agents/project/TEAMS.md
- agents/project/ORG.md
- agents/project/PROJECT-CONTEXT.yml
- src/agent_runtime/templates/project/agents/project/ORG.md
- src/agent_runtime/templates/project/agents/project/TEAMS.md
- src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml

## Target Files

- agents/project/ORG-MODEL.yml
- agents/project/TEAMS.md
- agents/project/ORG.md
- agents/project/PROJECT-CONTEXT.yml
- src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
- src/agent_runtime/templates/project/agents/project/ORG.md
- src/agent_runtime/templates/project/agents/project/TEAMS.md
- src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml
- tests/test_org_model_gate.py
- tests/test_org_read_api.py
- tests/test_owner_governance_chain_parity.py

## Scope

Add business-side teams and focused validation only. Keep live checkout roles as ORG-MODEL metadata rather than new agents/<role> directories. Keep external-system execution, payment integration, CRM sync, posting bots, and traffic automation out of scope.

## Steps

1. Add finance-accounting, marketing-growth, and sales-revenue teams to the live ORG-MODEL registry.
2. Add canonical roles and aliases for finance/accounting, marketing/growth, and sales/revenue responsibilities.
3. Update live TEAMS, ORG, and PROJECT-CONTEXT overlays with team purpose, roles, context, and access boundaries.
4. Add matching host-template overlays, including an ORG-MODEL template if absent.
5. Add focused tests that prove the new teams and aliases resolve and the org read API exposes the teams.
6. Run the recorded verification commands.

## Acceptance Criteria

- The new roles resolve through org_model_gate without underscore canonical ids.
- org_read_api.org_tree contains the three new team keys even with no live instances.
- Template docs provide the same business-team starter defaults.
- Sales automation text states compliant automation only and rejects viewbots, fake traffic, unauthorized bulk posting, spam, and platform manipulation.

## Verification

- `python -m pytest tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_project_context_overlay.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/org_model_gate.py --check`
- `python scripts/org_read_api.py --view org`
- `python scripts/owner_governance_gate.py`

## Handoff

Report the added teams/roles, template coverage, explicit prohibited growth automation, and verification results.

## Stop Boundary

Stop after the business operations org model is registered, implemented, verified, and closed with W4/W5/W6 evidence.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-17T22:34:00+09:00`
- Resolution: `done`
- Actual hours: `2.2`
- Actual tokens: `5400`
- Closed by: `lead-engineer-20260617-business-ops-577`
- Evidence:
  - `reviews/VERIFY-2026-06-17-unit-task-ar-577-001-20260617223200.json`
<!-- work-close:end -->
