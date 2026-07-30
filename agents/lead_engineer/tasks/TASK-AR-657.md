---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-657
display_id: TASK-AR-657
task_uid: 396558f9-f6f3-4c9d-aa52-b1ad58d4d786
work_id: TASK-AR-657
work_uid: 396558f9-f6f3-4c9d-aa52-b1ad58d4d786
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
title: Ship consumer adoption and failure operating skills
status: planned
priority: P1
difficulty: M
est_hours: 7
est_tokens: 14000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-657/UNIT-TASK-AR-657-001.md
reservation_id: RES-20260730-112500-842c7890-06
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Make the safe brownfield procedure discoverable and repeatable in every consumer without project-specific harness reinvention.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
depends_on:
  - TASK-AR-654
  - TASK-AR-656
acceptance:
  - A fresh core-profile host receives runtime-adoption and failure-to-regression skills.
  - runtime-adoption enforces baseline/control, ownership, safe apply, idempotence, protected bytes, isolation, exact acceptance, rollback, W4a, and W4b order.
  - The skill never authorizes product, credential, deploy, push, tag, or release actions.
  - Independent verification consumes migration contracts and exact execution receipts.
  - Release conductor requires all three current consumer contracts and zero unresolved release-critical P1 findings.
verification:
  - python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_pilot_acceptance.py tests/test_release_conductor_skill.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/template_mirror_gate.py --check
---

# TASK-AR-657 - Ship consumer adoption and failure operating skills

## Goal

- Make the safe brownfield procedure discoverable and repeatable in every consumer without project-specific harness reinvention.

## Scope

- Add a core runtime-adoption skill, ship failure-to-regression, register both assets, and update independent verification and release skill inputs.

## Acceptance Criteria

- A fresh core-profile host receives runtime-adoption and failure-to-regression skills.
- runtime-adoption enforces baseline/control, ownership, safe apply, idempotence, protected bytes, isolation, exact acceptance, rollback, W4a, and W4b order.
- The skill never authorizes product, credential, deploy, push, tag, or release actions.
- Independent verification consumes migration contracts and exact execution receipts.
- Release conductor requires all three current consumer contracts and zero unresolved release-critical P1 findings.

## Verification

- `python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_pilot_acceptance.py tests/test_release_conductor_skill.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/template_mirror_gate.py --check`
