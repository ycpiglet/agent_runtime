---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-577
display_id: TASK-AR-577
task_uid: 2e74dfb1-12c0-4ed3-b19a-7eb716565cac
work_id: TASK-AR-577
work_uid: 2e74dfb1-12c0-4ed3-b19a-7eb716565cac
kind: task
parent_id: TASKSET-AR-BUSINESS-OPERATIONS-TEAMS
registered_at: 2026-06-17T22:10:00+09:00
created_at: 2026-06-17T22:10:00+09:00
updated_at: 2026-06-17T22:10:00+09:00
title: Add business operations teams to org overlays
status: planned
priority: P0
difficulty: M
est_hours: 3
est_tokens: 4500
owner: lead_engineer
team: project-context
initiative_id: INIT-AR-BUSINESS-OPERATIONS-TEAMS
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-BUSINESS-OPERATIONS-TEAMS
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-577/UNIT-TASK-AR-577-001.md
reservation_id: RES-20260617-221000-d470ad37-01
origin_type: owner_request
origin_ref: chat:2026-06-17-business-operations-teams
created_by: codex-planner
summary: Define finance/accounting, marketing/growth, and sales/revenue teams across live project overlays and host templates while explicitly excluding platform manipulation such as viewbots or spam.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-577 - Add business operations teams to org overlays

## Goal

- Define finance/accounting, marketing/growth, and sales/revenue teams across live project overlays and host templates while explicitly excluding platform manipulation such as viewbots or spam.

## Scope

- Update the org model, human-facing team/org overlays, project context overlays, host templates, and focused tests. Do not create live per-role directories or implement external posting, CRM, payment, or traffic-generation integrations.

## Acceptance Criteria

- ORG-MODEL resolves new business teams and roles using kebab-case canonical ids and practical aliases.
- TEAMS/ORG/PROJECT-CONTEXT overlays describe finance-accounting, marketing-growth, and sales-revenue responsibilities and authority boundaries.
- Template overlays expose the same business team defaults for generated host projects.
- Sales/growth automation boundaries allow only compliant automation and explicitly exclude viewbots, fake traffic, unauthorized bulk posting, spam, and platform manipulation.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_project_context_overlay.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/org_model_gate.py --check`
- `python scripts/org_read_api.py --view org`
- `python scripts/owner_governance_gate.py`
