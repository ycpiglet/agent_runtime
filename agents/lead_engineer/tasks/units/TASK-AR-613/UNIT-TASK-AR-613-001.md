---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-613-001
work_uid: cb63eb8b-9171-4055-9e89-05696873d72d
kind: unit
parent_id: TASK-AR-613
unit_id: UNIT-TASK-AR-613-001
task_id: TASK-AR-613
task_set_id: TASKSET-AR-RELEASE-CADENCE-QUERY-RECOVERY
initiative_id: INIT-AR-RELEASE-CADENCE-QUERY-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-23T01:16:34+09:00
updated_at: 2026-07-23T01:50:00+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-cadence-query-recovery-plan.md
created_by: codex-root-planner
summary: Classify and retry unexpected non-zero cadence queries
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - reliability
  - cross_cutting
  - data_integrity
context: PR 315 CI run 29936269777 attempt 1 returned release-auto not-triggered for a valid v0.2.0 plus 40-commit fixture; the unchanged retry passed. TASK-AR-607 isolated dynamically loaded test module facades but intentionally left production query handling unchanged. release_cadence_trigger._git currently treats every positive non-zero return code as a deterministic empty answer, which can collapse a transient Git failure into no-tag or below-threshold state.
inputs:
  - reviews/REVIEW-2026-07-23-release-cadence-query-recovery-plan.md
  - GitHub issue 316
  - GitHub Actions run 29936269777 attempts 1 and 2
  - scripts/release_cadence_trigger.py
  - scripts/release_auto_noncritical.py
target_files:
  - scripts/release_cadence_trigger.py
  - src/agent_runtime/templates/project/scripts/release_cadence_trigger.py
  - tests/test_release_cadence_trigger.py
  - tests/test_release_auto_noncritical.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Add failure-first query result classification and retry coverage, then distinguish the expected no-tag Git response from unexpected non-zero failures. Retry only the unexpected transient path, record exhausted diagnostics, mirror the runtime implementation, and regenerate the host lock.
acceptance:
  - A transient non-zero result followed by real Git output recovers without query errors.
  - Three unexpected non-zero results yield structured command, return code, and sanitized diagnostic evidence.
  - The known no-tag stderr remains a quiet no-baseline-tag result.
  - Root and generated-host implementations are byte-identical and all focused tests pass.
verification:
  - python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/taskset_work_gate.py --check
handoff: Report failure-first evidence, the non-zero/no-tag classification matrix, retry counts, structured diagnostics, focused and repeated test results, parity, host lock, and independent W4b review.
stop_condition: Stop if the fix requires weakening a release gate, changing cadence thresholds, or modifying unrelated status consumers.
verified_at: 2026-07-23T01:50:00+09:00
verified_by: codex-root-task-ar-613
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-613-001-20260723015000.json
---

# UNIT-TASK-AR-613-001 - Classify and retry unexpected non-zero cadence queries

## Context

PR 315 CI run 29936269777 attempt 1 returned release-auto not-triggered for a valid v0.2.0 plus 40-commit fixture; the unchanged retry passed. TASK-AR-607 isolated dynamically loaded test module facades but intentionally left production query handling unchanged. release_cadence_trigger._git currently treats every positive non-zero return code as a deterministic empty answer, which can collapse a transient Git failure into no-tag or below-threshold state.

## Inputs

- reviews/REVIEW-2026-07-23-release-cadence-query-recovery-plan.md
- GitHub issue 316
- GitHub Actions run 29936269777 attempts 1 and 2
- scripts/release_cadence_trigger.py
- scripts/release_auto_noncritical.py

## Target Files

- scripts/release_cadence_trigger.py
- src/agent_runtime/templates/project/scripts/release_cadence_trigger.py
- tests/test_release_cadence_trigger.py
- tests/test_release_auto_noncritical.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Add failure-first query result classification and retry coverage, then distinguish the expected no-tag Git response from unexpected non-zero failures. Retry only the unexpected transient path, record exhausted diagnostics, mirror the runtime implementation, and regenerate the host lock.

## Steps

1. Reproduce one unexpected non-zero Git query result collapsing a valid tagged fixture into not-triggered.
2. Add a deterministic no-tag classifier and retry unexpected non-zero query results without changing thresholds.
3. Prove exhausted failures surface git-query-error through cadence and release-auto.
4. Mirror the implementation, regenerate the host lock, and run repeated focused probes plus the full matrix.

## Acceptance Criteria

- A transient non-zero result followed by real Git output recovers without query errors.
- Three unexpected non-zero results yield structured command, return code, and sanitized diagnostic evidence.
- The known no-tag stderr remains a quiet no-baseline-tag result.
- Root and generated-host implementations are byte-identical and all focused tests pass.

## Verification

- `python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/taskset_work_gate.py --check`

## Handoff

Report failure-first evidence, the non-zero/no-tag classification matrix, retry counts, structured diagnostics, focused and repeated test results, parity, host lock, and independent W4b review.

## Stop Boundary

Stop if the fix requires weakening a release gate, changing cadence thresholds, or modifying unrelated status consumers.
