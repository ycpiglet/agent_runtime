---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-663-001
work_uid: e7a1cb02-9de7-4a02-8afb-d80be5c7866d
kind: unit
parent_id: TASK-AR-663
unit_id: UNIT-TASK-AR-663-001
task_id: TASK-AR-663
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:00:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Re-attest and finish repeated-failure Compound enforcement
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: The V080 Compound task reached a bounded conditional approval after extensive fail-closed repairs, but remained open for Scribe, skeptic, adjacent-task, and native-Windows evidence. Its task/unit authority was then overwritten by an earlier canonical TASK-AR-654 although its code and evidence were merged.
inputs:
  - reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md
  - reviews/AUDIT-2026-08-02-task-ar-654-windows-native-evidence-final.md
  - agents/project/work-items/WORK-IDENTITY-RECOVERIES.json
  - scripts/closure_gate.py
  - scripts/compound_record.py
target_files:
  - scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - scripts/compound_record.py
  - src/agent_runtime/templates/project/scripts/compound_record.py
  - skills/failure-to-regression/SKILL.md
  - src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - tests/test_compound_records.py
  - tests/test_closure_gate.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_runtime_asset_usage.py
  - tests/test_claim_store.py
  - tests/test_atomic_io.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Re-attest all current behavior and repair locally reproducible gaps. Native Windows execution must be real or remain explicitly blocked; POSIX modeling cannot satisfy it.
acceptance:
  - Review-only closure cannot satisfy a declared repeated failure.
  - All defect signatures have exact canonical Compound coverage or closure blocks.
  - No old Compound record changes bytes.
  - External platform absence cannot be reported as verified.
verification:
  - PYTHONPATH=src python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_claim_store.py tests/test_atomic_io.py -q
  - PYTHONPATH=src python scripts/compound_record.py --check
  - PYTHONPATH=src python scripts/runtime_asset_usage.py --check
  - PYTHONPATH=src python scripts/template_mirror_gate.py --check
handoff: Attach collision-map proof, append-only hash matrix, RED/fix evidence, complete current suite, native-Windows disposition, fresh skeptic, W4a, and independent W4b.
stop_condition: Stop before rewriting legacy Compound history, claiming unexecuted native-Windows coverage, external CI, consumer mutation, claim release without W4b, push, tag, publish, or deploy.
depends_on:
  - TASK-AR-662
---

# UNIT-TASK-AR-663-001 - Re-attest and finish repeated-failure Compound enforcement

## Context

The V080 Compound task reached a bounded conditional approval after extensive fail-closed repairs, but remained open for Scribe, skeptic, adjacent-task, and native-Windows evidence. Its task/unit authority was then overwritten by an earlier canonical TASK-AR-654 although its code and evidence were merged.

## Inputs

- reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
- reviews/W4B-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md
- reviews/AUDIT-2026-08-02-task-ar-654-windows-native-evidence-final.md
- agents/project/work-items/WORK-IDENTITY-RECOVERIES.json
- scripts/closure_gate.py
- scripts/compound_record.py

## Target Files

- scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- scripts/compound_record.py
- src/agent_runtime/templates/project/scripts/compound_record.py
- skills/failure-to-regression/SKILL.md
- src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- tests/test_compound_records.py
- tests/test_closure_gate.py
- tests/test_task_claim_dispatcher.py
- tests/test_runtime_asset_usage.py
- tests/test_claim_store.py
- tests/test_atomic_io.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Re-attest all current behavior and repair locally reproducible gaps. Native Windows execution must be real or remain explicitly blocked; POSIX modeling cannot satisfy it.

## Steps

1. Claim the new task/unit and prove all old worker/overlay claim digests map to the lost UUID, not the current Host Gates task.
2. Run the complete Compound, closure, claim-authority, atomic publication, asset, and template suites on current main.
3. Reproduce any remaining current failure RED-first and record a T3 amendment before source changes.
4. Verify Scribe and adjacent dependencies are now satisfied, preserve every prior Compound record append-only, and classify native-Windows evidence separately.
5. Create fresh machine evidence, W4a, skeptic review, and independent W4b bound to TASK-AR-663.

## Acceptance Criteria

- Review-only closure cannot satisfy a declared repeated failure.
- All defect signatures have exact canonical Compound coverage or closure blocks.
- No old Compound record changes bytes.
- External platform absence cannot be reported as verified.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_claim_store.py tests/test_atomic_io.py -q`
- `PYTHONPATH=src python scripts/compound_record.py --check`
- `PYTHONPATH=src python scripts/runtime_asset_usage.py --check`
- `PYTHONPATH=src python scripts/template_mirror_gate.py --check`

## Handoff

Attach collision-map proof, append-only hash matrix, RED/fix evidence, complete current suite, native-Windows disposition, fresh skeptic, W4a, and independent W4b.

## Stop Boundary

Stop before rewriting legacy Compound history, claiming unexecuted native-Windows coverage, external CI, consumer mutation, claim release without W4b, push, tag, publish, or deploy.
