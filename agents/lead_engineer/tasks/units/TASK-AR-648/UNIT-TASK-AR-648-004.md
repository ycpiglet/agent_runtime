---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-004
work_uid: 30f87469-5447-42bc-8d4b-b69855241958
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-004
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-29T19:42:00+09:00
updated_at: 2026-07-29T19:42:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-overlay-claim-p0-replan.md
created_by: codex-root-v080-planner
summary: Align auto-review overlay claims with canonical gate and persistence contracts before the fresh Bean replay
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - external_effect
  - repeated_failure
context: Independent W4b approved the staged-only claim repair, but releasing that high-risk claim auto-dispatched a skeptic overlay that immediately self-blocked the parallel-worktree gate. The producer omits canonical lifecycle identity and persistence metadata, while the gate has no narrowly defined orchestration-overlay exception for worktree fields. This unit repairs that seam without weakening HEAD durability and only then replays Bean Wiki.
inputs:
  - reviews/W4B-2026-07-29-unit-task-ar-648-003-r2.md
  - reviews/SKEPTIC-2026-07-29-task-ar-648-overlay-claim-contract.md
  - reviews/REVIEW-2026-07-29-task-ar-648-overlay-claim-p0-replan.md
  - agent-runtime@5ae787d556908d923be46ebc9498bee628a3065b
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - scripts/role_routing.py
  - tests/test_role_routing.py
  - tests/test_role_routing_wiring.py
  - scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - tests/test_parallel_worktree_gate.py
  - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - src/agent_runtime/templates/project/docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - tests/fixtures/host/agent_runtime.lock.json
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
  - tests/fixtures/pilots/bean-wiki/evidence-green.json
  - reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - reviews/W4A-2026-07-29-unit-task-ar-648-004.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-004.md
  - reviews/REVIEW-2026-07-29-task-ar-648-overlay-claim-p0-replan.md
  - reviews/INDEX.md
scope: Define one explicit canonical contract for orchestration overlay claims, add producer-to-gate integration regressions, and preserve the authorized SCM HEAD check. After independent approval, run Bean attempt 2 from the original baseline and promote green evidence only if every preservation and external-effect boundary passes.
acceptance:
  - Automatically generated active overlays carry canonical callsite, pane, phase, progress, parent, handoff, and log fields.
  - Only explicit overlay claims may omit worker worktree and branch fields; ordinary active claims retain the existing fail-closed requirements.
  - Overlay claims explicitly use working-tree persistence without SCM authorization and surface a loss-risk watch while out of HEAD.
  - Auditor and skeptic overlays explicitly allow parallel participation in their parent task set without weakening duplicate-task or duplicate-instance checks.
  - A real high-risk dispatcher release followed immediately by the parallel-worktree gate produces zero block findings.
  - Staged-only authorized SCM claims remain blocked by both direct and failing-hook integration regressions.
  - Focused, full, owner-governance, source-template parity, lock, and sanitizer verification pass at one exact product SHA.
  - A new independent W4b approves the exact repair before any Bean worktree is created.
  - Bean attempt 2 has zero P0s, classifier staleness, reconcile conflicts, unexpected host/content changes, host commits, and external effects.
  - Original red, attempt-1, W4b R2, and skeptic evidence remain immutable.
verification:
  - python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_parallel_worktree_gate.py tests/test_task_claim_dispatcher.py -q
  - python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py tests/test_pilot_acceptance.py -q
  - python scripts/pilot_acceptance.py --host bean-wiki --check
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report the active/released overlay red reproducer, exact field and persistence contract, direct and real-release gate outcomes, preserved staged-authorized blocker, exact product SHA, full W4a and W4b, then Bean attempt-2 digests/counts/effects and green fixture semantic digest.
stop_condition: Stop on a broad overlay exemption, implicit SCM mutation, lost parent linkage, duplicate task-set collision, staged-authorized regression, evidence rewrite, new P0, consumer host/content mutation, credential access, network delivery, publish, deploy, origin push, unsupported model/cost claim, or failed independent verification.
defect_signatures:
  - defect:auto-review-overlay-claim-self-blocks-gate:a3d83ae935bfebcb
---

# UNIT-TASK-AR-648-004 - Repair Auto-review Overlay Claim Contract

## Context

The claim durability fix is valid, but the live high-risk release seam exposed
a producer/validator mismatch that focused unit tests did not cover. The same
Runtime action that approved the repair generated a canonical-schema overlay
claim that the canonical gate could not accept.

## Scope

Repair only the overlay envelope, its narrow no-worker-worktree semantics,
explicit persistence, parallel task-set declaration, and the missing
producer-to-gate test. Do not weaken non-overlay claim validation or redesign
role routing, UI, profiles, or provider telemetry.

## Steps

1. Preserve the generated claim and skeptic report as red operational
   evidence.
2. Add red tests for automatic overlay shape and a real high-risk
   release-to-gate flow.
3. Add the canonical overlay fields and explicit working-tree persistence.
4. Exempt only `overlay: true` records from worker checkout fields.
5. Re-run the staged-only SCM negative and all adjacent role-routing tests.
6. Complete full W4a and independent W4b.
7. Create a new Bean attempt-2 worktree only after approval.
8. Finish the three offline Bean tasks, final classifier projection, and green
   acceptance fixture.

## Stop Boundary

No consumer pilot before independent approval and no publish, deploy, push,
credential read, network delivery, content mutation, implicit commit, broad
gate exemption, or unsupported model/cost claim.
