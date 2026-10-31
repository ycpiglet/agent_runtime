---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-660-001
work_uid: f9f2da4b-50be-4bb0-b126-fa4bfe04e8c5
kind: unit
parent_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
task_id: TASK-AR-660
task_set_id: TASKSET-AR-SECURITY-RESILIENCE-20261101
initiative_id: INIT-AR-SECURITY-RESILIENCE-20261101
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-11-01T01:40:41+09:00
updated_at: 2026-11-01T03:05:02+09:00
origin_type: owner_request
origin_ref: owner-request:2026-11-01-independent-security-resilience
created_by: codex-security-20261101
summary: Add independent security and resilience reviewer with evidence closure
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - security
  - cross_cutting
context: Owner requests a reusable independent adversarial role covering authorization bypass, request replay and failure recovery; retain existing lifecycle and security-service boundaries.
inputs:
  - AGENTS.md
  - src/agent_runtime/templates/project/agents/roles.yml
  - src/agent_runtime/templates/project/docs/security-service.md
target_files:
  - new:src/agent_runtime/security_review.py
  - new:src/agent_runtime/templates/project/agents/security_reviewer/SKILL.md
  - src/agent_runtime/templates/project/agents/roles.yml
  - src/agent_runtime/templates/project/scripts/agent_orchestrator.py
  - src/agent_runtime/templates/project/docs/security-service.md
  - src/agent_runtime/templates/project/scripts/agent_worker.py
  - src/agent_runtime/templates/project/scripts/agent_terminal.py
  - new:tests/test_security_review.py
  - tests/fixtures/host/agent_runtime.lock.json
  - tests/test_backlog_board_tasksets.py
scope: Add a dispatchable security-reviewer role and a read-only evidence validator. Require exact source revision, independent reviewer, all three test families, and reproduction/fix/retest/regression links. Align the registered taskset catalog, publish a pull request, obtain independent review, and merge only after required checks pass under the owner request of 2026-11-01. No consumer installation, host-policy changes, notifications, permission expansion or release publication.
acceptance:
  - The generated host resolves security-reviewer and security/resilience aliases to the managed skill.
  - The validator blocks self-review and incomplete finding closure; absent coverage remains unknown.
  - The validator never executes a command or accesses a network target; evidence references remain within the declared evidence directory.
verification:
  - python -m pytest tests/test_security_review.py tests/test_security_service.py tests/test_inventory_sync_sanitize.py tests/test_backlog_board_tasksets.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/owner_governance_gate.py
handoff: Return changed files, exact source version, test evidence, limitations, independent review and recovery instructions.
stop_condition: Stop before consumer installation, permission expansion, production mutations or release publication. Pull-request publication and conditional merge are owner-authorized on 2026-11-01.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20261101-023231-task-ar-660-007d.json
  - agents/runtime/task_claims/CLAIM-20261101-014158-task-ar-660-2030.json
verified_at: 2026-11-01T02:44:14+09:00
verified_by: codex-security-20261101
evidence_refs:
  - reviews/VERIFY-2026-11-01-unit-task-ar-660-001-20261101021056.json
  - reviews/VERIFY-2026-11-01-unit-task-ar-660-001-20261101024414.json
defect_signatures:
compound_refs:
review_refs:
  - reviews/REVIEW-2026-11-01-task-ar-660-merged-closeout.md
resolution: done
completed_at: 2026-11-01T03:05:02+09:00
closed_by: codex-security-20261101
measurement_unavailable_reason: Complete cumulative host time/token/cost meter unavailable; original checkpoints and measured verification timings retained
---

# UNIT-TASK-AR-660-001 - Add independent security and resilience reviewer with evidence closure

## Context

Owner requests a reusable independent adversarial role covering authorization bypass, request replay and failure recovery; retain existing lifecycle and security-service boundaries.

## Inputs

- AGENTS.md
- src/agent_runtime/templates/project/agents/roles.yml
- src/agent_runtime/templates/project/docs/security-service.md

## Target Files

- new:src/agent_runtime/security_review.py
- new:src/agent_runtime/templates/project/agents/security_reviewer/SKILL.md
- src/agent_runtime/templates/project/agents/roles.yml
- src/agent_runtime/templates/project/scripts/agent_orchestrator.py
- src/agent_runtime/templates/project/docs/security-service.md
- new:tests/test_security_review.py
- tests/fixtures/host/agent_runtime.lock.json
- src/agent_runtime/templates/project/scripts/agent_worker.py
- src/agent_runtime/templates/project/scripts/agent_terminal.py
- tests/test_backlog_board_tasksets.py

## Scope

Add a dispatchable security-reviewer role and a read-only evidence validator. Require exact source revision, independent reviewer, all three test families, and reproduction/fix/retest/regression links. Align the registered taskset catalog, publish a pull request, obtain independent review, and merge only after required checks pass under the owner request of 2026-11-01. No consumer installation, host-policy changes, notifications, permission expansion or release publication.

## Steps

1. Add the managed role skill and orchestrator alias.
2. Implement bounded read-only report validation with unknown and failure states.
3. Test evidence independence, missing coverage, fixed-finding closure, source binding and unsafe paths; verify generated-host inclusion.

## Acceptance Criteria

- The generated host resolves security-reviewer and security/resilience aliases to the managed skill.
- The validator blocks self-review and incomplete finding closure; absent coverage remains unknown.
- The validator never executes a command or accesses a network target; evidence references remain within the declared evidence directory.

## Verification

- `python -m pytest tests/test_security_review.py tests/test_security_service.py tests/test_inventory_sync_sanitize.py tests/test_backlog_board_tasksets.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/owner_governance_gate.py`

## Handoff

Return changed files, exact source version, test evidence, limitations, independent review and recovery instructions.

## Stop Boundary

Stop before consumer installation, permission expansion, production mutations or release publication. Pull-request publication and conditional merge are owner-authorized on 2026-11-01.
## Integration authorization

- 2026-11-01 owner request: resolve remaining work-ledger mismatch; publish, independently review and conditionally merge. Prior registration and review history retained.
- Catalog repair: add only the registered TASKSET-AR-SECURITY-RESILIENCE-20261101 expectation; preserve exact equality.

- Verification history: 02:10 receipt covers the original product implementation. Subsequent integration receipt024414 passed271 focused tests, host lock and governance; official unit close completed03:05:02. Original evidence retained.
- Board Team is derived generator routing; canonical assignment and actual claim team are risk-and-safety. Generator/policy unchanged.
- Execution: Codex agent instance codex-security-20261101. Model-routing labels are policy metadata; actual model/provider fields remain unverified, not proof of another provider execution.
## Failed verification history

- Preserved failed attempt: reviews/VERIFY-2026-11-01-unit-task-ar-660-001-20261101024208.json. Pointer identity projection was corrected; subsequent passed integration receipt remains the acceptance evidence. Failed file and prior Git revisions retained; no result rewritten.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-11-01T03:05:02+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Complete cumulative host time/token/cost meter unavailable; original checkpoints and measured verification timings retained
- Closed by: `codex-security-20261101`
- Verification evidence:
  - `reviews/VERIFY-2026-11-01-unit-task-ar-660-001-20261101021056.json`
  - `reviews/VERIFY-2026-11-01-unit-task-ar-660-001-20261101024414.json`
- Reviews:
  - `reviews/REVIEW-2026-11-01-task-ar-660-merged-closeout.md`
<!-- work-close:end -->
