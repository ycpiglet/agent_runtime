---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-593-001
work_uid: b14f0608-5023-4a5e-894f-d5ed94655d8c
kind: unit
parent_id: TASK-AR-593
unit_id: UNIT-TASK-AR-593-001
task_id: TASK-AR-593
task_set_id: TASKSET-AR-BUSINESS-OPERATING-SYSTEM
initiative_id: INIT-AR-BUSINESS-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-21T16:20:00+09:00
updated_at: 2026-06-21T17:15:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-operating-system-continuation
created_by: codex-planner
summary: Publish business operating lanes and cycle packet
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Owner wants the accounting, marketing, sales, operations, support, planning, and strategy parts to keep moving in repeated cycles while using product features such as review, compound, retro, scribe, doc-steward, and seminar artifacts. The next smallest step is to make those lanes executable as org metadata and a reusable cycle packet before creating downstream implementation tasksets.
inputs:
  - agents/project/ORG-MODEL.yml
  - agents/project/TEAMS.md
  - agents/project/ORG.md
  - agents/project/PROJECT-CONTEXT.yml
  - src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
  - src/agent_runtime/templates/project/agents/project/ORG.md
  - src/agent_runtime/templates/project/agents/project/TEAMS.md
  - src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml
  - docs/superpowers/plans/2026-06-17-business-operations-teams.md
  - reviews/W4B-2026-06-17-TASK-AR-577.md
target_files:
  - agents/project/ORG-MODEL.yml
  - agents/project/TEAMS.md
  - agents/project/ORG.md
  - agents/project/PROJECT-CONTEXT.yml
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
  - src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
  - src/agent_runtime/templates/project/agents/project/ORG.md
  - src/agent_runtime/templates/project/agents/project/TEAMS.md
  - src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml
  - src/agent_runtime/templates/project/agents/project/BUSINESS-OPERATING-SYSTEM.md
  - tests/test_org_model_gate.py
  - tests/test_org_read_api.py
  - tests/test_project_context_overlay.py
  - tests/test_owner_governance_chain_parity.py
  - reviews/SEMINAR-2026-06-21-business-operating-system.md
  - reviews/SCRIBE-2026-06-21-business-operating-system.md
  - reviews/COMPOUND-2026-06-21-business-operating-system.md
  - reviews/RETRO-2026-06-21-business-operating-system.md
scope: Documentation, org metadata, template parity, and tests only. External accounting, CRM, support desk, social posting, email, payment, or customer-contact mutations are out of scope.
acceptance:
  - The new roles resolve through org_model_gate without underscore canonical ids.
  - org_read_api.org_tree contains operations-support and planning-strategy team keys even with no live instances.
  - The business operating packet requires review/seminar/scribe/doc-steward/compound/retro evidence before a business cycle claims completion.
  - Safety boundaries prohibit external-system writes, customer contact, scraping, spam, payment mutation, and unsupported automation without Owner approval.
verification:
  - python -m pytest tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_project_context_overlay.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/org_model_gate.py --check
  - python scripts/org_read_api.py --view org
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-OPERATING-SYSTEM --check
handoff: Report the new operations/support and planning/strategy lanes, business cycle packet, collaboration evidence artifacts, safety boundaries, and verification results.
stop_condition: Stop after the operating lanes, packet docs, template parity, focused tests, collaboration records, and verification evidence are complete.
verified_at: 2026-06-21T17:10:00+09:00
verified_by: lead-engineer-20260621-business-os
evidence_refs:
  - reviews/VERIFY-2026-06-21-unit-task-ar-593-001-20260621171000.json
resolution: done
completed_at: 2026-06-21T17:15:00+09:00
closed_by: lead-engineer-20260621-business-os
actual_hours: 1.4
actual_tokens: 6100
---

# UNIT-TASK-AR-593-001 - Publish business operating lanes and cycle packet

## Context

The Owner wants the accounting, marketing, sales, operations, support, planning, and strategy parts to keep moving in repeated cycles while using product features such as review, compound, retro, scribe, doc-steward, and seminar artifacts. The next smallest step is to make those lanes executable as org metadata and a reusable cycle packet before creating downstream implementation tasksets.

## Inputs

- agents/project/ORG-MODEL.yml
- agents/project/TEAMS.md
- agents/project/ORG.md
- agents/project/PROJECT-CONTEXT.yml
- src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
- src/agent_runtime/templates/project/agents/project/ORG.md
- src/agent_runtime/templates/project/agents/project/TEAMS.md
- src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml
- docs/superpowers/plans/2026-06-17-business-operations-teams.md
- reviews/W4B-2026-06-17-TASK-AR-577.md

## Target Files

- agents/project/ORG-MODEL.yml
- agents/project/TEAMS.md
- agents/project/ORG.md
- agents/project/PROJECT-CONTEXT.yml
- agents/project/BUSINESS-OPERATING-SYSTEM.md
- src/agent_runtime/templates/project/agents/project/ORG-MODEL.yml
- src/agent_runtime/templates/project/agents/project/ORG.md
- src/agent_runtime/templates/project/agents/project/TEAMS.md
- src/agent_runtime/templates/project/agents/project/PROJECT-CONTEXT.example.yml
- src/agent_runtime/templates/project/agents/project/BUSINESS-OPERATING-SYSTEM.md
- tests/test_org_model_gate.py
- tests/test_org_read_api.py
- tests/test_project_context_overlay.py
- tests/test_owner_governance_chain_parity.py
- reviews/SEMINAR-2026-06-21-business-operating-system.md
- reviews/SCRIBE-2026-06-21-business-operating-system.md
- reviews/COMPOUND-2026-06-21-business-operating-system.md
- reviews/RETRO-2026-06-21-business-operating-system.md

## Scope

Documentation, org metadata, template parity, and tests only. External accounting, CRM, support desk, social posting, email, payment, or customer-contact mutations are out of scope.

## Steps

1. Add operations-support and planning-strategy teams to live and template ORG-MODEL registries.
2. Add canonical roles and aliases for operations, support, planning, strategy, customer success, and business analysis responsibilities.
3. Update TEAMS, ORG, and PROJECT-CONTEXT overlays with role boundaries and escalation rules for the expanded business operating lanes.
4. Publish BUSINESS-OPERATING-SYSTEM.md as the cycle packet SSoT and mirror it into the host template.
5. Record seminar, scribe, compound, and retro artifacts for this cycle.
6. Extend focused tests and run the recorded verification commands.

## Acceptance Criteria

- The new roles resolve through org_model_gate without underscore canonical ids.
- org_read_api.org_tree contains operations-support and planning-strategy team keys even with no live instances.
- The business operating packet requires review/seminar/scribe/doc-steward/compound/retro evidence before a business cycle claims completion.
- Safety boundaries prohibit external-system writes, customer contact, scraping, spam, payment mutation, and unsupported automation without Owner approval.

## Verification

- `python -m pytest tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_project_context_overlay.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/org_model_gate.py --check`
- `python scripts/org_read_api.py --view org`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-OPERATING-SYSTEM --check`

## Handoff

Report the new operations/support and planning/strategy lanes, business cycle packet, collaboration evidence artifacts, safety boundaries, and verification results.

## Stop Boundary

Stop after the operating lanes, packet docs, template parity, focused tests, collaboration records, and verification evidence are complete.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-21T17:15:00+09:00`
- Resolution: `done`
- Actual hours: `1.4`
- Actual tokens: `6100`
- Closed by: `lead-engineer-20260621-business-os`
- Evidence:
  - `reviews/VERIFY-2026-06-21-unit-task-ar-593-001-20260621171000.json`
<!-- work-close:end -->
