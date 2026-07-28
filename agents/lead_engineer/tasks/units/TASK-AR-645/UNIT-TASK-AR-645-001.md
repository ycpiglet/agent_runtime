---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-645-001
work_uid: a944e692-2bed-41b1-89e1-6c71ad35d770
kind: unit
parent_id: TASK-AR-645
unit_id: UNIT-TASK-AR-645-001
task_id: TASK-AR-645
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T04:42:09+09:00
started_at: 2026-07-29T03:43:12+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Introduce per-entry task-linked compound records and retrieval
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: At main d41da008 the focused suite passes even though closure accepts unrelated same-day records, claim dispatch performs no task/signature knowledge lookup, the only KEDB reader is coupled to one monolithic compound_log, and sync still treats that live host log as managed by default. Autofolio demonstrates the cost with a 5235-line shared log.
inputs:
  - reviews/REVIEW-2026-07-29-task-ar-645-w0-t3-replan.md
  - reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md
  - agents/project/casebooks/failure-and-compound-casebook.md
  - scripts/closure_gate.py
  - scripts/compound_cadence_gate.py
  - scripts/task_claim_dispatcher.py
  - scripts/work.py
  - src/agent_runtime/templates/project/scripts/kedb_search.py
target_files:
  - BACKLOG-BOARD.md
  - agents/lead_engineer/tasks/TASK-AR-645.md
  - agents/lead_engineer/tasks/units/TASK-AR-645/UNIT-TASK-AR-645-001.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - new:src/agent_runtime/knowledge_records.py
  - new:scripts/compound_record.py
  - new:src/agent_runtime/templates/project/scripts/compound_record.py
  - scripts/closure_gate.py
  - scripts/compound_cadence_gate.py
  - scripts/task_claim_dispatcher.py
  - scripts/work.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/kedb_search.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/work.py
  - src/agent_runtime/templates/project/agents/lead_engineer/compound_log.md
  - agents/project/WORK-SCHEMA.yml
  - src/agent_runtime/templates/project/agents/project/WORK-SCHEMA.yml
  - src/agent_runtime/config.py
  - src/agent_runtime/inventory.py
  - src/agent_runtime/sync.py
  - src/agent_runtime/adoption.py
  - src/agent_runtime/lock.py
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - new:tests/test_compound_records.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_closure_gate.py
  - tests/test_compound_cadence_gate.py
  - tests/test_compound_cadence_obligation.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_adoption.py
  - tests/test_config_v2.py
  - tests/test_work_schema_gate.py
  - tests/test_template_smoke.py
  - tests/fixtures/host/agent_runtime.lock.json
  - agents/runtime/a2a/messages.jsonl
  - agents/runtime/pane_events/pane-events.jsonl
  - agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.json
  - agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.handoff.md
  - agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.log.md
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-independent-auditor-closeout.handoff.md
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-independent-auditor-closeout.json
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-independent-auditor-closeout.log.md
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-skeptic-closeout.handoff.md
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-skeptic-closeout.json
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-skeptic-closeout.log.md
  - reviews/W4A-2026-07-29-unit-task-ar-645-001.md
  - reviews/W4B-2026-07-29-unit-task-ar-645-001.md
  - reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729041748.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729042042.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729043455.json
  - reviews/INDEX.md
scope: Add a machine-validated per-record compound store under agents/project/knowledge/compounds/records, a generated index, deterministic defect signatures, claim-time retrieval, and task-linked closeout validation while keeping the legacy monolith as a read-only compatibility source. Do not migrate or rewrite historical host records.
acceptance:
  - Unrelated same-day records do not satisfy closeout.
  - A task or unit defect_signatures field is normalized deterministically and matching records are surfaced before claim persistence and implementation.
  - New compound records are one JSON file per record, validate work/signature/source/prevention fields, and update a generated index without shared-record edits.
  - Readiness new: target markers are normalized to real repo-relative paths before claim footprint conflict and post-verification checks.
  - Passed verification JSON remains separate from linked review and compound references; work close validates each reference against the current work ID or one declared signature.
  - The legacy compound_log placeholder is seed_once and new record data is host_owned while its index is generated; none is permanently managed.
verification:
  - python -m pytest tests/test_compound_records.py tests/test_task_claim_dispatcher.py tests/test_closure_gate.py tests/test_compound_cadence_gate.py tests/test_compound_cadence_obligation.py tests/test_inventory_sync_sanitize.py tests/test_adoption.py tests/test_config_v2.py tests/test_work_schema_gate.py tests/test_template_smoke.py -q
  - python scripts/runtime_asset_usage.py --check
  - python -m agent_runtime.cli sanitize --root . --check
handoff: Provide a repeat-defect fixture showing create, indexed retrieval at claim time, unrelated-record rejection, linked work close, legacy read-only fallback, and ownership behavior.
stop_condition: Stop before bulk-rewriting historical compound logs, changing consumer repositories, or weakening passed-verification JSON requirements.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.json
verified_at: 2026-07-29T04:34:55+09:00
verified_by: codex-root-v080-integrator
evidence_refs:
  - reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729041748.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729042042.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729043455.json
review_refs:
  - reviews/W4B-2026-07-29-unit-task-ar-645-001.md
resolution: done
completed_at: 2026-07-29T04:42:09+09:00
closed_by: codex-root-v080-integrator
measurement_unavailable_reason: Actual hours and token telemetry were not captured across this multi-agent implementation, independent verification, and CI integration cycle.
---

# UNIT-TASK-AR-645-001 - Introduce per-entry task-linked compound records and retrieval

## Context

At Agent Runtime `main` `d41da008`, the focused suite passes even though
closure accepts unrelated same-day records, claim dispatch performs no
task/signature knowledge lookup, the only KEDB reader is coupled to one
monolithic `compound_log.md`, and sync treats that live host log as managed by
default. Autofolio demonstrates the cost with a 5,235-line shared log.

## Inputs

- reviews/REVIEW-2026-07-29-task-ar-645-w0-t3-replan.md
- reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md
- agents/project/casebooks/failure-and-compound-casebook.md
- scripts/closure_gate.py
- scripts/compound_cadence_gate.py
- scripts/task_claim_dispatcher.py
- scripts/work.py
- src/agent_runtime/templates/project/scripts/kedb_search.py

## Target Files

- BACKLOG-BOARD.md
- agents/lead_engineer/tasks/TASK-AR-645.md
- agents/lead_engineer/tasks/units/TASK-AR-645/UNIT-TASK-AR-645-001.md
- agents/project/NEXT-SESSION-POINTER.yml
- agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
- agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
- new:src/agent_runtime/knowledge_records.py
- new:scripts/compound_record.py
- new:src/agent_runtime/templates/project/scripts/compound_record.py
- scripts/closure_gate.py
- scripts/compound_cadence_gate.py
- scripts/task_claim_dispatcher.py
- scripts/work.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/kedb_search.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/work.py
- src/agent_runtime/templates/project/agents/lead_engineer/compound_log.md
- agents/project/WORK-SCHEMA.yml
- src/agent_runtime/templates/project/agents/project/WORK-SCHEMA.yml
- src/agent_runtime/config.py
- src/agent_runtime/inventory.py
- src/agent_runtime/sync.py
- src/agent_runtime/adoption.py
- src/agent_runtime/lock.py
- agents/project/RUNTIME-ASSET-REGISTRY.json
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- new:tests/test_compound_records.py
- tests/test_task_claim_dispatcher.py
- tests/test_closure_gate.py
- tests/test_compound_cadence_gate.py
- tests/test_compound_cadence_obligation.py
- tests/test_inventory_sync_sanitize.py
- tests/test_adoption.py
- tests/test_config_v2.py
- tests/test_work_schema_gate.py
- tests/test_template_smoke.py
- tests/fixtures/host/agent_runtime.lock.json
- agents/runtime/a2a/messages.jsonl
- agents/runtime/pane_events/pane-events.jsonl
- agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.json
- agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.handoff.md
- agents/runtime/task_claims/CLAIM-20260729-034312-task-ar-645-645001.log.md
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-independent-auditor-closeout.handoff.md
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-independent-auditor-closeout.json
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-independent-auditor-closeout.log.md
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-skeptic-closeout.handoff.md
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-skeptic-closeout.json
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-645-skeptic-closeout.log.md
- reviews/W4A-2026-07-29-unit-task-ar-645-001.md
- reviews/W4B-2026-07-29-unit-task-ar-645-001.md
- reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729041748.json
- reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729042042.json
- reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729043455.json
- reviews/INDEX.md

## Scope

Add a machine-validated per-record compound store under
`agents/project/knowledge/compounds/records`, a generated index, deterministic
defect signatures, claim-time retrieval, and task-linked closeout validation.
Keep the legacy monolith as a read-only compatibility source. Do not migrate
or rewrite historical host records.

## Steps

1. Define the JSON compound-record schema, safe record path, deterministic
   signature normalization, and atomic create/check/index CLI.
2. Add optional `defect_signatures`, `compound_refs`, and `review_refs` work
   fields and make claim creation surface matching records before persistence.
   Normalize readiness `new:` markers before persisting the claim footprint.
3. Require linked review/compound records for substantial or repeat-defect
   closeout without weakening passed verification-JSON evidence.
4. Count individual records in cadence, retain a read-only legacy KEDB
   fallback, and generate one deterministic index from concurrent record files.
5. Make the legacy seed, canonical records, and generated index respectively
   `seed_once`, `host_owned`, and `generated` in adoption/sync/lock behavior.

## Acceptance Criteria

- Unrelated same-day records do not satisfy closeout.
- A task or unit `defect_signatures` field is normalized deterministically and
  matching records are surfaced before claim persistence and implementation.
- New compound records are one JSON file per record, validate
  work/signature/source/prevention fields, and update a generated index
  without shared-record edits.
- Readiness `new:` target markers are normalized to real repo-relative paths
  before claim footprint conflict and post-verification checks.
- Passed verification JSON remains separate from linked review and compound
  references; `work close` validates each reference against the current work
  ID or one declared signature.
- The legacy `compound_log.md` placeholder is `seed_once`, new record data is
  `host_owned`, and its index is `generated`; none is permanently managed.

## Verification

- `python -m pytest tests/test_compound_records.py tests/test_task_claim_dispatcher.py tests/test_closure_gate.py tests/test_compound_cadence_gate.py tests/test_compound_cadence_obligation.py tests/test_inventory_sync_sanitize.py tests/test_adoption.py tests/test_config_v2.py tests/test_work_schema_gate.py tests/test_template_smoke.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python -m agent_runtime.cli sanitize --root . --check`

## Handoff

Provide a repeat-defect fixture showing create, indexed retrieval at claim
time, unrelated-record rejection, linked `work close`, legacy read-only
fallback, and ownership behavior.

## Stop Boundary

Stop before bulk-rewriting historical compound logs, changing consumer
repositories, or weakening passed-verification JSON requirements.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-29T04:42:09+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Actual hours and token telemetry were not captured across this multi-agent implementation, independent verification, and CI integration cycle.
- Closed by: `codex-root-v080-integrator`
- Verification evidence:
  - `reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729041748.json`
  - `reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729042042.json`
  - `reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729043455.json`
- Reviews:
  - `reviews/W4B-2026-07-29-unit-task-ar-645-001.md`
<!-- work-close:end -->
