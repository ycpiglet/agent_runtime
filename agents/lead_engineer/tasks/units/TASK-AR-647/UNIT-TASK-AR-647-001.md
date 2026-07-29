---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-647-001
work_uid: af1cf17b-4cb9-4686-9d2f-9fd0e3238a13
kind: unit
parent_id: TASK-AR-647
unit_id: UNIT-TASK-AR-647-001
task_id: TASK-AR-647
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T13:33:26+09:00
started_at: 2026-07-29T08:54:44+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Add a strict native Allimbot event adapter and enforce the security-service claim boundary
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - security
  - data_integrity
  - external_effect
  - cross_cutting
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-085444-task-ar-647-4e9b.json
risk_tier: high
approval_required: false
security_sensitive: true
context: The legacy client sends free-form text to 127.0.0.1:8787/trigger or ntfy, clean core imports an excluded optional module, and security-service contains notifier files but no enforceable service-risk policy. Allimbot origin/main@5a51ed4b instead provides an allowlisted ProjectEmitter whose emit path writes only to a durable local SQLite spool.
inputs:
  - src/agent_runtime/templates/project/scripts/allimbot.py
  - ../allimbot@5a51ed4b:src/allimbot/integrations.py
  - ../allimbot@5a51ed4b:src/allimbot/client.py
  - ../allimbot@5a51ed4b:integrations/projects/agent-runtime.json
  - reviews/REVIEW-2026-07-29-task-ar-647-w0-t3-replan.md
target_files:
  - src/agent_runtime/allimbot.py
  - new:src/agent_runtime/security_service.py
  - src/agent_runtime/hook_runtime.py
  - src/agent_runtime/update_notify.py
  - src/agent_runtime/doctor.py
  - scripts/owner_governance_gate.py
  - new:scripts/security_service_gate.py
  - scripts/task_claim_dispatcher.py
  - new:agents/project/SECURITY-SERVICE-POLICY.json
  - pyproject.toml
  - new:src/agent_runtime/templates/project/.allimbot.json
  - src/agent_runtime/templates/project/.env.example
  - new:src/agent_runtime/templates/project/agents/project/SECURITY-SERVICE-POLICY.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-PROFILE-MANIFEST.json
  - src/agent_runtime/templates/project/scripts/allimbot.py
  - src/agent_runtime/templates/project/scripts/allimbot_stop_hook.cmd
  - src/agent_runtime/templates/project/scripts/agent_orchestrator.py
  - src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - new:src/agent_runtime/templates/project/scripts/security_service_gate.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - schemas/task-unit.schema.json
  - src/agent_runtime/templates/project/schemas/task-unit.schema.json
  - .github/workflows/test.yml
  - docs/ALLIMBOT-INTEGRATION.md
  - new:src/agent_runtime/templates/project/docs/security-service.md
  - tests/test_allimbot.py
  - new:tests/test_security_service.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_doctor.py
  - tests/test_session_continuity_hooks.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_runtime_asset_usage.py
  - tests/test_owner_governance_consumer_host.py
  - tests/test_owner_governance_chain_parity.py
  - tests/test_update_notify.py
  - tests/test_notify_routing.py
  - tests/test_orchestrator_atomic_writes.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Use the installed Allimbot ProjectEmitter as the sole durable enqueue implementation; enforce the exact Agent Runtime recipe and bounded value policy before optional delivery; migrate internal callers; remove direct delivery; and make security-service add a claim-time risk gate. Keep Allimbot optional, do not duplicate its spool, do not add a network sender, and do not mutate consumer repositories.
acceptance:
  - Only attention.required, task.state.changed, release.gate.failed, and turn.completed with their current allowlisted fields are accepted.
  - Unknown events, unexpected fields, invalid bounded values, or a drifted recipe fail closed before Allimbot construction.
  - Summary text is rendered by the adapter; caller-provided prompt/body/exception/credential text cannot be forwarded.
  - With Allimbot installed, emit creates a durable local spool record without network I/O; Runtime never calls flush.
  - Missing dependency, keyring/config, or writable spool returns unavailable without raising into the host operation.
  - Legacy notify remains a secret-free compatibility signal and all owned call sites use structured events.
  - Clean core has no hard dependency on the profile-only event helper.
  - security-service pre-claim validation covers secrets, auth, migrations, and production external effects using host risk_paths plus managed defaults.
  - data_integrity is valid in the task-unit schema and routes migration/auth work consistently.
  - Direct ntfy, /trigger, legacy environment keys, and the Windows-only stop helper are absent from the managed standard path.
verification:
  - python -m pytest tests/test_allimbot.py tests/test_security_service.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_session_continuity_hooks.py tests/test_inventory_sync_sanitize.py tests/test_runtime_asset_usage.py tests/test_owner_governance_consumer_host.py tests/test_owner_governance_chain_parity.py tests/test_update_notify.py tests/test_notify_routing.py -q
  - python scripts/runtime_asset_usage.py --check
  - python -m pytest -q
handoff: Provide exact event/field/value compatibility, fail-closed versus fail-open results, clean profile dependency closure, security risk-to-required-metadata coverage, and an isolated real-Allimbot spool record with no delivery.
stop_condition: Stop before reading or changing production credentials, flushing the spool, sending a live event, adding a direct network fallback, mutating Bean Wiki/Allimbot/Autofolio, weakening an Owner boundary, or performing version/tag/publish/release work.
verified_at: 2026-07-29T13:33:26+09:00
verified_by: le-20260729-kst-647001
evidence_refs:
  - reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729093804.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729102332.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729111858.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729120428.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729124908.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729132409.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729133326.json
---

# UNIT-TASK-AR-647-001 - Add native events and security-service guardrails

## Context

The legacy client sends free-form text to `127.0.0.1:8787/trigger` or directly
to ntfy. A clean `core` projection excludes that client while
`agent_orchestrator.py` imports it unconditionally. The `security-service`
profile therefore adds two notifier files but no enforceable security
guardrail.

Allimbot `origin/main@5a51ed4b` instead exposes `ProjectEmitter` with an exact
project recipe. `EventClient.emit()` only enqueues into a local SQLite spool;
delivery to `/v1/events` belongs to a separate `flush()` worker. Agent Runtime
must reuse that boundary rather than recreate it.

## Inputs

- src/agent_runtime/templates/project/scripts/allimbot.py
- ../allimbot@5a51ed4b:src/allimbot/integrations.py
- ../allimbot@5a51ed4b:src/allimbot/client.py
- ../allimbot@5a51ed4b:integrations/projects/agent-runtime.json
- reviews/REVIEW-2026-07-29-task-ar-647-w0-t3-replan.md

## Target Files

- src/agent_runtime/allimbot.py
- new:src/agent_runtime/security_service.py
- src/agent_runtime/hook_runtime.py
- src/agent_runtime/update_notify.py
- src/agent_runtime/doctor.py
- scripts/owner_governance_gate.py
- new:scripts/security_service_gate.py
- scripts/task_claim_dispatcher.py
- new:agents/project/SECURITY-SERVICE-POLICY.json
- pyproject.toml
- new:src/agent_runtime/templates/project/.allimbot.json
- src/agent_runtime/templates/project/.env.example
- new:src/agent_runtime/templates/project/agents/project/SECURITY-SERVICE-POLICY.json
- src/agent_runtime/templates/project/agents/project/RUNTIME-PROFILE-MANIFEST.json
- src/agent_runtime/templates/project/scripts/allimbot.py
- src/agent_runtime/templates/project/scripts/allimbot_stop_hook.cmd
- src/agent_runtime/templates/project/scripts/agent_orchestrator.py
- src/agent_runtime/templates/project/scripts/owner_governance_gate.py
- new:src/agent_runtime/templates/project/scripts/security_service_gate.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- schemas/task-unit.schema.json
- src/agent_runtime/templates/project/schemas/task-unit.schema.json
- .github/workflows/test.yml
- docs/ALLIMBOT-INTEGRATION.md
- new:src/agent_runtime/templates/project/docs/security-service.md
- tests/test_allimbot.py
- new:tests/test_security_service.py
- tests/test_task_claim_dispatcher.py
- tests/test_doctor.py
- tests/test_session_continuity_hooks.py
- tests/test_inventory_sync_sanitize.py
- tests/test_runtime_asset_usage.py
- tests/test_owner_governance_consumer_host.py
- tests/test_owner_governance_chain_parity.py
- tests/test_update_notify.py
- tests/test_notify_routing.py
- tests/test_orchestrator_atomic_writes.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Use the installed Allimbot `ProjectEmitter` as the sole durable enqueue
implementation. Enforce the exact Agent Runtime recipe and bounded field-value
policy before optional delivery, migrate owned callers, remove direct
delivery, and make `security-service` add a claim-time risk gate.

Keep Allimbot optional. Do not duplicate its spool, add a network sender,
declare delivery success without an event ID, or mutate a consumer repository.

## Steps

1. Add the exact managed `.allimbot.json` recipe and strict structured event
   API.
2. Delegate successful enqueue to installed `ProjectEmitter`; distinguish
   policy rejection from dependency/config/spool unavailability.
3. Replace internal free-form notifications and the Windows-only stop helper
   with structured, cross-platform event calls.
4. Remove `/trigger`, direct ntfy, and the legacy CI/environment path.
5. Add a managed security policy plus optional pre-claim/Owner gate for service
   risk classes.
6. Repair core/security profile dependency closure and expose secret-free
   doctor status.
7. Verify with fakes, clean profiles, and an isolated real Allimbot spool;
   never flush.

## Acceptance Criteria

- Only `attention.required`, `task.state.changed`, `release.gate.failed`, and
  `turn.completed` with their current allowlisted fields are accepted.
- Unknown events, unexpected fields, invalid bounded values, or a drifted
  recipe fail closed before Allimbot construction.
- Summary text is rendered by the adapter; caller-provided
  prompt/body/exception/credential text cannot be forwarded.
- With Allimbot installed, `emit` creates a durable local spool record without
  network I/O; Runtime never calls `flush`.
- Missing dependency, keyring/config, or writable spool returns `unavailable`
  without raising into the host operation.
- Legacy `notify` remains a secret-free compatibility signal and all owned
  call sites use structured events.
- Clean `core` has no hard dependency on the profile-only event helper.
- `security-service` pre-claim validation covers secrets, auth, migrations,
  and production external effects using `host.risk_paths` plus managed
  defaults.
- `data_integrity` is valid in the task-unit schema and routes migration/auth
  work consistently.
- Direct ntfy, `/trigger`, legacy environment keys, and the Windows-only stop
  helper are absent from the managed standard path.

## Verification

- `python -m pytest tests/test_allimbot.py tests/test_security_service.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_session_continuity_hooks.py tests/test_inventory_sync_sanitize.py tests/test_runtime_asset_usage.py tests/test_owner_governance_consumer_host.py tests/test_owner_governance_chain_parity.py tests/test_update_notify.py tests/test_notify_routing.py -q`
- `python scripts/runtime_asset_usage.py --check`
- clean `core` and `core+security-service` generated-host smoke
- isolated Allimbot `origin/main@5a51ed4b` enqueue/allowlist contract smoke with
  a temporary spool and no network
- `python -m pytest -q`

## Handoff

Provide exact event/field/value compatibility, fail-closed versus fail-open
results, clean profile dependency closure, security risk-to-required-metadata
coverage, and an isolated real-Allimbot spool record with no delivery.

## Stop Boundary

Stop before reading or changing production credentials, flushing the spool,
sending a live event, adding a direct network fallback, mutating Bean
Wiki/Allimbot/Autofolio, weakening an Owner boundary, or performing
version/tag/publish/release work.

## Security Controls

- Never forward caller-supplied free text, exception messages, prompts,
  environment values, tokens, endpoints, provider names, or destinations.
- Validate the managed recipe and every event value before importing or
  constructing Allimbot.
- Report only boolean/configuration status and bounded reason codes in doctor;
  never secret values or raw dependency exceptions.
- Treat an installed package or writable spool failure as delivery
  unavailability, not permission to use a fallback transport.

## Rollback

Revert the scoped implementation commit and restore the previous managed
profile projection. No production migration, credential rotation, external
delivery, or consumer mutation is performed by this unit. Spool fixtures stay
temporary and are deleted after verification.

## External Effect Boundary

This unit may remove legacy external-delivery wiring, but it must not send a
notification, invoke `flush`, access a production endpoint/token, install or
change a provider account, or publish a package/release. The later Allimbot
pilot owns consumer configuration and real-host evidence.