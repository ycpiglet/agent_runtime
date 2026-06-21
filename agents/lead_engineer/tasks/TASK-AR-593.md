---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-593
display_id: TASK-AR-593
task_uid: 1607a42c-76da-4330-a9c6-8ac1309d9d77
work_id: TASK-AR-593
work_uid: 1607a42c-76da-4330-a9c6-8ac1309d9d77
kind: task
parent_id: TASKSET-AR-BUSINESS-OPERATING-SYSTEM
registered_at: 2026-06-21T16:20:00+09:00
created_at: 2026-06-21T16:20:00+09:00
started_at: 2026-06-21T16:48:41+09:00
updated_at: 2026-06-21T17:20:00+09:00
title: Publish business operating lanes and cycle packet
status: completed
priority: P0
difficulty: M
est_hours: 4
est_tokens: 7500
owner: lead_engineer
team: planning-office
initiative_id: INIT-AR-BUSINESS-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-BUSINESS-OPERATING-SYSTEM
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-593/UNIT-TASK-AR-593-001.md
reservation_id: RES-20260621-162000-781cd9ca-01
origin_type: owner_request
origin_ref: chat:2026-06-21-business-operating-system-continuation
created_by: codex-planner
summary: Define operations/support and planning/strategy teams alongside finance, marketing, and sales; publish the reusable business operating packet that tells agents how to run review, seminar, scribe, doc-steward, compound, and retro cycles without unsafe external effects.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_project_context_overlay.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/org_model_gate.py --check
  - python scripts/org_read_api.py --view org
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-OPERATING-SYSTEM --check
verification_status: passed
verified_at: 2026-06-21T17:18:00+09:00
verified_by: lead-engineer-20260621-business-os
evidence_refs:
  - reviews/VERIFY-2026-06-21-task-ar-593-20260621171800.json
resolution: done
completed_at: 2026-06-21T17:20:00+09:00
closed_by: lead-engineer-20260621-business-os
actual_hours: 1.6
actual_tokens: 6900
---

# TASK-AR-593 - Publish business operating lanes and cycle packet

## Goal

- Define operations/support and planning/strategy teams alongside finance, marketing, and sales; publish the reusable business operating packet that tells agents how to run review, seminar, scribe, doc-steward, compound, and retro cycles without unsafe external effects.

## Scope

- Update org overlays, host templates, documentation, and focused tests. Do not create live per-role directories, write to external CRM/accounting/support systems, or contact customers/leads.

## Acceptance Criteria

- Live and template ORG-MODEL registries expose operations-support and planning-strategy teams with canonical roles and practical aliases.
- Live and template TEAMS/ORG/PROJECT-CONTEXT overlays route finance, marketing, sales, operations, support, planning, and strategy work to explicit owners and escalation boundaries.
- agents/project/BUSINESS-OPERATING-SYSTEM.md defines a reusable cycle packet covering review, seminar, scribe, doc-steward, compound, retro, evidence, and next-taskset creation.
- Focused tests prove org resolution, org-read exposure, template parity, and packet safety boundaries.

## Verification

- `python -m pytest tests/test_org_model_gate.py tests/test_org_read_api.py tests/test_project_context_overlay.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/org_model_gate.py --check`
- `python scripts/org_read_api.py --view org`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-BUSINESS-OPERATING-SYSTEM --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-21T17:20:00+09:00`
- Resolution: `done`
- Actual hours: `1.6`
- Actual tokens: `6900`
- Closed by: `lead-engineer-20260621-business-os`
- Evidence:
  - `reviews/VERIFY-2026-06-21-task-ar-593-20260621171800.json`
<!-- work-close:end -->
