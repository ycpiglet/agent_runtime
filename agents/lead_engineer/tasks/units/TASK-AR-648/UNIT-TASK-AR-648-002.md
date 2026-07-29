---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-002
work_uid: 135b334a-29e2-4ed8-9591-477a03f75f3e
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-002
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-29T16:57:16+09:00
updated_at: 2026-07-29T17:15:55+09:00
started_at: 2026-07-29T17:14:04+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-p0-remediation-replan.md
created_by: codex-root-v080-planner
summary: Repair the five Bean Wiki pilot P0 defects and prove a fresh green adoption replay
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-171404-task-ar-648-648002.json
escalation_triggers:
  - ambiguity
  - data_integrity
  - security
context: The independently verified Bean Wiki red pilot preserved host content and external-effect boundaries, but exposed five release-blocking Runtime integration defects. The defects span canonical taskset discovery, linked-worktree identity, sample classification, v2 state adapters, and ownership of producer-mutated registries. They must be repaired without folding the separately observed P1 product gaps into this unit.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-001.md
  - tests/fixtures/pilots/bean-wiki/evidence.json
  - reviews/REVIEW-2026-07-29-task-ar-648-p0-remediation-replan.md
  - agent-runtime@ec08a3d8c2a6613f508f1d9fd3f2f67693b4a92b
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - scripts/taskset_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
  - tests/test_taskset_dispatcher.py
  - tests/test_work_registration.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - tests/test_task_claim_dispatcher.py
  - scripts/work_item_classifier.py
  - src/agent_runtime/templates/project/scripts/work_item_classifier.py
  - tests/test_work_item_classifier.py
  - scripts/state_sync_gate.py
  - src/agent_runtime/templates/project/scripts/state_sync_gate.py
  - tests/test_state_sync_gate.py
  - src/agent_runtime/config.py
  - tests/test_config_v2.py
  - tests/test_inventory_sync_sanitize.py
  - tests/fixtures/host/agent_runtime.lock.json
  - tests/fixtures/host/owner-docs.yml
  - tests/test_lock_merge_driver.py
  - scripts/pilot_acceptance.py
  - tests/fixtures/pilots/bean-wiki/evidence.json
  - tests/fixtures/pilots/bean-wiki/evidence-green.json
  - tests/test_pilot_acceptance.py
  - reviews/PILOT-BEAN-WIKI-v080.md
  - reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-002.md
  - reviews/REVIEW-2026-07-29-task-ar-648-green-evidence-scope-amendment.md
  - reviews/INDEX.md
scope: Implement one focused repair per observed P0, with source/template parity and adversarial regression tests. Replay the exact adoption path in a newly created clean Bean Wiki worktree, update only sanitized Runtime evidence, and preserve the original red observations. Do not implement profile thinning, host-context or role-overlay execution, first-run UX expansion, or provider token/cost telemetry in this unit.
acceptance:
  - A taskset created through work.py new is discovered and planned by taskset_dispatcher from the canonical TASKSET-DEFINITIONS registry, with explicit legacy fallback behavior retained.
  - A worker invoked from its own registered linked Git worktree may claim that worktree, while the actual primary checkout, non-worktree paths, and ambiguous roots remain refused.
  - Installed examples under agents/lead_engineer/tasks/units/examples never become canonical units or orphan findings.
  - A valid v2 configured state adapter plus fresh generated projection satisfies state sync without requiring Runtime identifiers in host-owned BACKLOG.md or requiring an unconfigured STATUS.md.
  - owner-docs.yml is seeded or otherwise classified so work.py new may update it without creating a later managed-file conflict.
  - Source and packaged-template copies remain behaviorally equivalent and all five focused reproducer tests pass.
  - A fresh Bean Wiki replay has zero P0 findings, zero sync conflicts, zero unexpected host/content changes, and zero external effects.
  - The offline validator rejects any fixture that falsely upgrades the replay, removes pinned identity, leaks an absolute path, or claims unobserved model/cost data.
verification:
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_work_registration.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py -q
  - python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python -m pytest tests/test_template_smoke.py tests/test_pilot_acceptance.py -q
  - python scripts/pilot_acceptance.py --host bean-wiki --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report each P0's failing reproducer, repair, negative guard, source/template parity, fresh Bean replay SHA and counts, preserved digests, external-effect counters, updated sanitized fixture digest, independent W4b verdict, and exact-main CI result.
stop_condition: Stop on any live publish, deploy, origin push, Bean host commit, credential access, network delivery, content mutation, primary-checkout mutation, weakened ownership boundary, unsupported green/cost claim, or newly observed P0. Keep P1 product work out of scope.
---

# UNIT-TASK-AR-648-002 - Repair Bean pilot P0s and replay green

## Context

The red pilot was useful precisely because it did not hide integration
failures. Five defects prevent the current Runtime from being a safe
drop-in common harness:

1. registered tasksets are invisible to dispatch;
2. linked workers cannot claim their own clean worktree;
3. packaged examples are mistaken for live work;
4. state sync writes Runtime expectations onto host-owned state; and
5. a Runtime producer mutates a registry that sync still treats as managed.

The repairs share one release gate: the same Bean adoption must replay green
from a fresh pinned worktree without changing editorial content or external
systems.

## Inputs

- `reviews/PILOT-BEAN-WIKI-v080.md`
- `reviews/W4B-2026-07-29-unit-task-ar-648-001.md`
- `tests/fixtures/pilots/bean-wiki/evidence.json`
- Agent Runtime `main@ec08a3d8c2a6613f508f1d9fd3f2f67693b4a92b`
- Bean Wiki `origin/main@357eee4fd8c29c33a949adbe3a0ffa80c874bf42`

## Target Files

- Dispatch: `scripts/taskset_dispatcher.py`, its packaged copy, and focused
  registration/dispatch tests.
- Claims: `scripts/task_claim_dispatcher.py`, its packaged copy, and linked
  worktree tests.
- Classification: `scripts/work_item_classifier.py`, its packaged copy, and
  installed-example tests.
- State: `scripts/state_sync_gate.py`, its packaged copy, configuration
  ownership, and state/sync tests.
- Lock fixture: `tests/fixtures/host/agent_runtime.lock.json`, regenerated
  mechanically after the ownership-default change, plus the canonical
  `tests/fixtures/host/owner-docs.yml` seed required to make the installed-host
  fixture self-contained and `tests/test_lock_merge_driver.py` to copy that
  complete fixture during stale-lock recovery.
- Evidence: the Bean pilot validator, fixture, tests, and report.

## Scope

Repair only the five observed P0 defects, preserve source/template behavior,
and replay Bean Wiki from a fresh disposable worktree. Keep the P1 profile,
role-overlay, first-run UX, and provider-observability work outside this unit.

## Steps

1. Add one failing regression for each of the five red-pilot reproducers.
2. Make dispatch consume the canonical taskset registry and keep legacy
   Python/Markdown definitions as explicit compatibility fallbacks.
3. Resolve the Git common directory and actual primary checkout before claim
   validation; accept only an unambiguous linked worktree self-claim.
4. Exclude the examples namespace from canonical unit discovery in both
   source and packaged-template classifiers.
5. Resolve state sources and generated projection from v2 configuration.
   Keep host adapters read-only and preserve legacy behavior only for
   unconfigured/v1 hosts.
6. Reclassify `owner-docs.yml` as mutable seeded state and prove
   adopt → register → reconcile remains conflict-free.
7. Run focused and full tests, then independently review the exact repair
   diff.
8. Create a new disposable Bean worktree at the pinned baseline and repeat
   plan, apply, lock, register, dispatch, linked claim, classifier, Scribe,
   state-sync, reconcile, and host-preservation checks.
9. Update the sanitized fixture/report as a distinct green replay, re-pin the
   semantic digest, rerun tamper tests, and integrate only after CI passes.

## Acceptance Criteria

- All five original P0 reproductions pass as regressions.
- Primary-checkout, ambiguous-path, stale-projection, host-state mutation, and
  managed-registry divergence negative cases still fail closed.
- Source/template behavior is equivalent.
- The fresh replay records zero P0s and no host/content/external mutation.
- P1 findings remain visible and are not mislabeled as fixed.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py tests/test_work_registration.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py -q`
- `python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q`
- `python -m pytest tests/test_template_smoke.py tests/test_pilot_acceptance.py -q`
- `python scripts/pilot_acceptance.py --host bean-wiki --check`
- `python scripts/owner_governance_gate.py`
- `PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check`
- `python -m pytest -q`

## Handoff

Attach the per-P0 failing/passing evidence, exact source/template diff,
replay worktree SHA and adoption counts, preservation digests, zero-effect
counters, sanitized fixture digest, independent W4b verdict, and exact-main
CI URL.

## Stop Boundary

No publish, deploy, origin push, Bean commit, credential access, event
delivery, article mutation, primary-checkout mutation, weakened fail-closed
guard, or unsupported model/cost claim. P1 work remains separate.
