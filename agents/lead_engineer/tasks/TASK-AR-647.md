---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-647
display_id: TASK-AR-647
task_uid: e331d145-b696-4e1f-8c82-e2aa5267df0b
work_id: TASK-AR-647
work_uid: e331d145-b696-4e1f-8c82-e2aa5267df0b
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T10:26:01+09:00
started_at: 2026-07-29T08:54:44+09:00
title: Adopt native Allimbot events and security-service guardrails
status: in_progress
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: risk-and-safety
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-647/UNIT-TASK-AR-647-001.md
reservation_id: RES-20260728-163601-b8c2a87a-09
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Use current durable, allowlisted Allimbot delivery and add reusable security/external-effect controls for service hosts.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
risk_tier: high
approval_required: false
security_sensitive: true
verification:
  - python -m pytest tests/test_allimbot.py tests/test_security_service.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_session_continuity_hooks.py tests/test_inventory_sync_sanitize.py tests/test_runtime_asset_usage.py tests/test_owner_governance_consumer_host.py tests/test_owner_governance_chain_parity.py tests/test_update_notify.py tests/test_notify_routing.py -q
  - python scripts/runtime_asset_usage.py --check
  - python -m pytest -q
tags:
  - work-cli-created
review_refs:
  - reviews/REVIEW-2026-07-29-task-ar-647-w0-t3-replan.md
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-085444-task-ar-647-4e9b.json
verification_status: passed
verified_at: 2026-07-29T10:26:01+09:00
verified_by: le-20260729-kst-647001
evidence_refs:
  - reviews/VERIFY-2026-07-29-task-ar-647-20260729094525.json
  - reviews/VERIFY-2026-07-29-task-ar-647-20260729102601.json
---

# TASK-AR-647 - Adopt native Allimbot events and security-service guardrails

## Goal

- Use Allimbot's current durable, allowlisted project-event boundary and make
  the `security-service` profile enforce service-risk metadata before a claim
  can start.

## Scope

- Replace `/trigger` and direct-ntfy delivery with a strict
  `ProjectEmitter` adapter that only enqueues locally, migrate runtime call
  sites to structured events, repair clean-core dependency closure, and add a
  profile-scoped pre-claim security gate for secrets, auth, migrations, and
  production external effects.

## Acceptance Criteria

- Runtime accepts only the four events and metadata fields in Allimbot's
  `agent-runtime.json` recipe at `origin/main@5a51ed4b`.
- Event summaries are generated from bounded structured fields; prompts,
  exception messages, credentials, arbitrary body text, and provider
  destinations never cross the runtime event boundary.
- With Allimbot installed, `emit` performs only a durable local spool enqueue;
  Runtime never calls `flush` or sends directly to `/trigger`, ntfy, or
  `/v1/events`.
- Missing Allimbot/configuration/spool availability is a structured fail-open
  delivery result, while unknown events, unexpected metadata, and policy drift
  fail closed before delivery.
- A clean `core` host imports and runs without the optional Allimbot package.
- The `security-service` profile adds a machine-readable policy and pre-claim
  gate that classifies secrets, auth, migration, and production-external-effect
  paths and requires the corresponding risk metadata and review sections.
- Legacy CI and environment wiring cannot bypass the native event/spool
  boundary.

## Verification

- `python -m pytest tests/test_allimbot.py tests/test_security_service.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_session_continuity_hooks.py tests/test_inventory_sync_sanitize.py tests/test_runtime_asset_usage.py tests/test_owner_governance_consumer_host.py tests/test_owner_governance_chain_parity.py tests/test_update_notify.py tests/test_notify_routing.py -q`
- `python scripts/runtime_asset_usage.py --check`
- clean `core` and `core+security-service` generated-host smoke
- isolated Allimbot `origin/main@5a51ed4b` enqueue/allowlist contract smoke with
  a temporary spool and no network
- `python -m pytest -q`