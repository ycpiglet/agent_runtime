---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-650
display_id: TASK-AR-650
task_uid: a80a7fe2-ae55-4529-a8aa-c38319a0d6d8
work_id: TASK-AR-650
work_uid: a80a7fe2-ae55-4529-a8aa-c38319a0d6d8
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-30T12:00:00+09:00
title: Rehearse Autofolio v0.6 to v0.8 migration
status: in_progress
started_at: 2026-07-30T08:36:49+09:00
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-083649-task-ar-650-ar650001.json
priority: P0
difficulty: L
est_hours: 10
est_tokens: 20000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-650/UNIT-TASK-AR-650-001.md
reservation_id: RES-20260728-163601-b8c2a87a-12
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Prove the new ownership/profile model materially reduces Autofolio's unmanaged seams without changing product behavior.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
  - migration-rehearsal
  - exact-product
  - causal-isolation
depends_on:
  - TASK-AR-649
escalation_triggers:
  - ambiguity
  - data_integrity
  - cross_cutting
risk_tier: high
---

# TASK-AR-650 - Rehearse Autofolio v0.6 to v0.8 migration

## Goal

- Prove the new ownership/profile model materially reduces Autofolio's unmanaged seams without changing product behavior.

## Scope

- Preserve registered taskset order before RC dispatch, then run an
  exact-product, exact-host, causally isolated migration and safe-apply
  rehearsal. Preserve attempts 1 and 2 as immutable RED evidence, use a newly
  committed direct-claim repair for attempt 3, classify every legacy seam, and
  verify protected product bytes and host tests without product feature
  changes.

## Acceptance Criteria

- All 20 pinned v0.6 unmanaged paths have a managed, seed_once, host_owned,
  generated, or temporary-conflict disposition.
- Temporary seams decrease materially.
- No Autofolio product file is silently overwritten.
- The v0.6 to RC migration is repeatable from a clean worktree.
- Registered taskset order selects TASK-AR-650 before TASK-AR-651.
- Registered task dependencies survive into worker units; missing, invalid,
  duplicate, self, and cyclic references fail before writes.

## Verification

- `python scripts/pilot_acceptance.py --host autofolio --check`
- `python -m pytest tests/test_work_registration.py tests/test_taskset_dispatcher.py -q`
- `python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q`
