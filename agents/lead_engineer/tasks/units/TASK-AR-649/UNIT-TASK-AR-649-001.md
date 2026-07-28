---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-649-001
work_uid: 34e7d639-192e-47ed-ade2-bff02162b8c0
kind: unit
parent_id: TASK-AR-649
unit_id: UNIT-TASK-AR-649-001
task_id: TASK-AR-649
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Adopt and exercise core plus security-service in Allimbot
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Allimbot already has mature product security and durable event integration but no common development-process task/claim/compound/scribe/model-cost harness.
inputs:
  - ../allimbot/docs/PROJECT_STATUS.ko.md
  - ../allimbot/docs/AGENT_INTEGRATIONS.ko.md
  - ../allimbot/integrations/projects/agent-runtime.json
target_files:
  - tests/fixtures/pilots/allimbot
  - reviews/PILOT-ALLIMBOT-v080.md
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
scope: Run profile adoption and three pilot scenarios in a clean worktree with production effects disabled.
acceptance:
  - Unexpected host overwrite count is zero.
  - Critical work requires independent security review.
  - Event metadata is allowlisted and secret-free.
  - Production deployment remains blocked.
verification:
  - python scripts/pilot_acceptance.py --host allimbot --check
  - python -m pytest tests/test_pilot_acceptance.py tests/test_allimbot.py -q
handoff: Attach adoption, test, security-review, event-spool, and external-effect evidence.
stop_condition: Stop before production deploy, remote account mutation, secret creation, or modification of the active dirty host branch.
---

# UNIT-TASK-AR-649-001 - Adopt and exercise core plus security-service in Allimbot

## Context

Allimbot already has mature product security and durable event integration but no common development-process task/claim/compound/scribe/model-cost harness.

## Inputs

- ../allimbot/docs/PROJECT_STATUS.ko.md
- ../allimbot/docs/AGENT_INTEGRATIONS.ko.md
- ../allimbot/integrations/projects/agent-runtime.json

## Target Files

- tests/fixtures/pilots/allimbot
- reviews/PILOT-ALLIMBOT-v080.md
- scripts/pilot_acceptance.py
- tests/test_pilot_acceptance.py

## Scope

Run profile adoption and three pilot scenarios in a clean worktree with production effects disabled.

## Steps

1. Capture host context, risk paths, and verification commands.
2. Apply core plus security-service profile.
3. Run ordinary, Critical, and offline-event tasks.
4. Run Python/web/security gates and record results.

## Acceptance Criteria

- Unexpected host overwrite count is zero.
- Critical work requires independent security review.
- Event metadata is allowlisted and secret-free.
- Production deployment remains blocked.

## Verification

- `python scripts/pilot_acceptance.py --host allimbot --check`
- `python -m pytest tests/test_pilot_acceptance.py tests/test_allimbot.py -q`

## Handoff

Attach adoption, test, security-review, event-spool, and external-effect evidence.

## Stop Boundary

Stop before production deploy, remote account mutation, secret creation, or modification of the active dirty host branch.
