---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-003
work_uid: 323199c0-007c-4e46-9d17-65409808e19c
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-003
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-29T18:34:22+09:00
updated_at: 2026-07-29T19:23:03+09:00
started_at: 2026-07-29T18:40:02+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-second-p0-remediation-replan.md
created_by: codex-root-v080-planner
summary: Make claim SCM mutation explicit, package standalone state dependencies, and replay Bean Wiki from a second clean worktree
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-184002-task-ar-648-648003.json
escalation_triggers:
  - data_integrity
  - external_effect
  - repeated_failure
context: The five original Bean P0 repairs passed integrated verification, but the first fresh replay found two more release blockers. Default claim creation silently committed consumer artifacts, and installed state-sync/Scribe scripts depended on an uninstalled source package. The failed worktree and commit are immutable evidence. This unit repairs only those boundaries and repeats the full green replay from the original host baseline.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-1.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-002.md
  - reviews/REVIEW-2026-07-29-task-ar-648-second-p0-remediation-replan.md
  - agent-runtime@cd79b655af86c20dad1b8717d0eb5e6c692dac5a
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_claim_guard.py
  - scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - tests/test_parallel_worktree_gate.py
  - AGENTS.md
  - src/agent_runtime/templates/project/AGENTS.md
  - src/agent_runtime/templates/project/docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - new:scripts/agent_runtime/__init__.py
  - new:scripts/agent_runtime/config.py
  - new:scripts/agent_runtime/state_projection.py
  - new:src/agent_runtime/templates/project/scripts/agent_runtime/__init__.py
  - new:src/agent_runtime/templates/project/scripts/agent_runtime/config.py
  - new:src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py
  - tests/test_state_sync_gate.py
  - tests/test_scribe_due.py
  - tests/test_template_smoke.py
  - tests/test_inventory_sync_sanitize.py
  - tests/fixtures/host/agent_runtime.lock.json
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
  - tests/fixtures/pilots/bean-wiki/evidence-green.json
  - reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-003.md
  - reviews/REVIEW-2026-07-29-task-ar-648-second-p0-remediation-replan.md
  - reviews/INDEX.md
scope: Change claim persistence from implicit SCM mutation to explicit opt-in while retaining the authorized crash-safety primitive. Package only the canonical config/state-projection dependency needed by installed state surfaces, with byte-parity guards. Then replay the full Bean pilot from a new clean worktree and produce a distinct true-green fixture/report only if every boundary passes.
acceptance:
  - Default task_claim_dispatcher create persists claim files but leaves exact Git HEAD unchanged in a clean adopted host.
  - An explicit CLI flag or true-valued compatibility environment setting commits only the claim JSON, handoff, and log; false and malformed settings never authorize a commit.
  - Existing claim_guard crash-safety and idempotency regressions remain green.
  - Claim records persist the selected working-tree or SCM-commit mode; the parallel-worktree gate watches intentional working-tree persistence but still blocks legacy ambiguity and failed explicit commit persistence.
  - A synced host with no source checkout, editable install, or ambient PYTHONPATH runs state_sync_gate.py and scribe_due.py using the packaged portable modules.
  - Canonical src modules, root portable modules, and template portable modules are byte-identical; package selection, lock, and sanitizer evidence include them.
  - A second fresh Bean replay has zero P0s, zero classifier staleness, zero reconcile conflicts, zero unexpected host/content changes, zero host commits, and zero external effects.
  - Every reconcile observation pins the exact Runtime template root, commit, selected-file count, and digest.
  - Original red evidence and blocked attempt-1 evidence remain byte-identical and the green validator rejects any false-zero host commit or source-install dependency.
verification:
  - python -m pytest tests/test_task_claim_dispatcher.py tests/test_claim_guard.py tests/test_state_sync_gate.py tests/test_scribe_due.py tests/test_template_smoke.py -q
  - python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py tests/test_pilot_acceptance.py -q
  - python scripts/pilot_acceptance.py --host bean-wiki --check
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report both new failing/passing reproducers, exact HEAD invariants, explicit crash-safety compatibility, portable module parity, installed-host commands with sanitized PYTHONPATH, selected-file/digest changes, Bean attempt-2 hashes/counts/effects, green fixture semantic digest, independent W4b verdict, and exact-main CI.
stop_condition: Stop on implicit SCM mutation, source-checkout import dependence, red/attempt-1 evidence mutation, new P0, host/content mutation, credential access, network delivery, publish, deploy, origin push, unsupported model/cost claim, or failed independent verification.
verified_at: 2026-07-29T19:23:03+09:00
verified_by: codex-root-task-ar-648-003
evidence_refs:
  - reviews/VERIFY-2026-07-29-unit-task-ar-648-003-20260729190144.json
  - reviews/VERIFY-2026-07-29-unit-task-ar-648-003-20260729192303.json
review_refs:
  - reviews/W4A-2026-07-29-unit-task-ar-648-003.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-003.md
  - reviews/W4A-2026-07-29-unit-task-ar-648-003-r2.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-003-r2.md
defect_signatures:
  - defect:explicit-scm-claim-staged-but-absent-from-head-p:876b70f8b223ef6c
---

# UNIT-TASK-AR-648-003 - Repair Claim SCM and Portable State Runtime

## Context

Bean green attempt 1 preserved editorial content and replayed the original five
repairs, but it was not safe to adopt:

1. default claim creation changed the consumer branch HEAD; and
2. installed state surfaces imported a package that adoption did not install.

The attempt stopped immediately. Its unexpected commit and worktree are
evidence and must not be reset, amended, or reused.

## Scope

Make all SCM mutation explicit at claim creation, retain the existing
crash-safety primitive for authorized control repositories, and install the
smallest portable state dependency that makes the managed scripts truthful.
Do not redesign profiles, role overlays, the UI, or provider telemetry.

## Steps

1. Add red tests for default HEAD mutation and clean-host state import failure.
2. Add an explicit claim-commit opt-in and fail closed on absent, false, or
   malformed compatibility settings.
3. Add a namespace-safe `scripts/agent_runtime` portable package containing
   exact copies of canonical config and state-projection modules.
4. Add canonical/root/template byte-parity and installed-host isolation tests.
5. Regenerate lock/profile evidence and run focused plus full Runtime suites.
6. Obtain independent integrated W4b approval.
7. Create Bean attempt 2 from the original pinned baseline, never from attempt
   1, and run all consumer Python commands with sanitized import state.
8. Regenerate classifier output after final serial lifecycle projection.
9. Produce green evidence only after exact HEAD, host/content, reconcile, and
   external-effect checks all pass.

## Stop Boundary

No implicit commit, failed-attempt rewrite, source-checkout dependency,
consumer content mutation, credential access, network delivery, publish,
deploy, push, unsupported cost/model claim, or continuation after a new P0.
