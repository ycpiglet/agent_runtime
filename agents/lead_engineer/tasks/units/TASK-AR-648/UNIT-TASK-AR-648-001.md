---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-001
work_uid: 6e563637-ea70-43fe-946e-b1d9aa18bb79
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-001
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T16:29:20+09:00
started_at: 2026-07-29T15:36:41+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-w0-t3-replan.md
created_by: codex-root-v080-planner
summary: Run a reversible, evidence-first core plus web-content adoption pilot in Bean Wiki
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-153641-task-ar-648-648001.json
context: Bean Wiki has strong host-owned editorial agents and publishing gates but no common task/claim/Compound/Scribe/model-routing harness. The pinned core plus web-content projection is 243 files and web-content contributes no profile-specific file, so adoption weight and overlay execution must be measured rather than assumed.
inputs:
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42:AGENTS.md
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42:CLAUDE.md
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42:BACKLOG.md
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42:docs/EDITORIAL.md
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42:docs/AGENT-EDITORIAL-OPS.md
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42:src/content/topic-plan.ts
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42:src/content/articles/coffee-flavor-wheel.html
  - allimbot@5a51ed4b6c42b0fea1ac97352209f47ff52f3b52:integrations/projects/bean-wiki.json
  - autofolio@ca88433cf155fd03d616584fda7ed4aa3d33fd71:agent_runtime.yml
  - autofolio@ca88433cf155fd03d616584fda7ed4aa3d33fd71:docs/AGENT_RUNTIME_INTEGRATION.md
target_files:
  - new:tests/fixtures/pilots/bean-wiki
  - new:reviews/PILOT-BEAN-WIKI-v080.md
  - new:scripts/pilot_acceptance.py
  - new:tests/test_pilot_acceptance.py
scope: In disposable clean worktrees only, record a pre-adoption inventory, create the explicit v2 host adapter, run adopt plan then reconcile/apply-safe/lock, execute three safe tasks, and collect replayable evidence. The specialist review may write a local review artifact but must not change src/content. No host commit, push, deploy, live publish, credential access, or network event delivery.
acceptance:
  - Unexpected host overwrite count is zero.
  - Doctor blockers and dangling dependencies are zero.
  - Bootstrap provenance and local task traces cover every pilot diff.
  - Compound retrieval and process-level restart recovery are demonstrated.
  - Scribe projection is fresh while BACKLOG.md remains byte-identical.
  - Model routing distinguishes configured intent from observed execution and makes no unsupported savings claim.
  - Publish, deploy, origin-push, credential-read, and network-delivery counters are zero.
  - Offline fixture validation detects tampered ownership, missing trace, false model observation, and nonzero external effects.
verification:
  - python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py tests/test_model_routing.py tests/test_scribe_due.py -q
  - python scripts/pilot_acceptance.py --host bean-wiki --check
  - python -m pytest tests/test_pilot_acceptance.py -q
handoff: Attach pinned SHAs, before/after digests, reconcile counts, duration, footprint, seams, bootstrap provenance, three task traces, Compound query evidence, Scribe/restart evidence, routing truth, Bean verification output, and P0/P1/P2 findings.
stop_condition: Stop before any live publish, deploy, origin push, host commit, credential access, network delivery, content mutation, unrelated dirty checkout mutation, or unsupported success/cost claim.
verified_at: 2026-07-29T16:28:58+09:00
verified_by: le-20260729-task-ar-648-001-codex
evidence_refs:
  - reviews/VERIFY-2026-07-29-unit-task-ar-648-001-20260729162858.json
review_refs:
  - reviews/W4B-2026-07-29-unit-task-ar-648-001.md
resolution: done
completed_at: 2026-07-29T16:29:20+09:00
closed_by: le-20260729-task-ar-648-001-codex
actual_hours: 0.88
measurement_unavailable_reason: Provider token and cost usage were not exposed; elapsed wall time is recorded separately as actual_hours.
---

# UNIT-TASK-AR-648-001 - Adopt and exercise core plus web-content in Bean Wiki

## Context

Bean Wiki has strong host-owned editorial agents and publishing gates but no
common task/claim/Compound/Scribe/model-routing harness. At the pinned
baselines, Agent Runtime selects 243 files for `core+web-content` (237 managed
by default) and `web-content` adds no file beyond `core`. The pilot must
therefore measure adoption weight and host-overlay execution rather than
assuming the result is lightweight.

## Inputs

- Bean Wiki `origin/main@357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
  host protocol, editorial SSOT, agents/skills, topic plan, backlog, and
  `coffee-flavor-wheel.html`.
- Allimbot `origin/main@5a51ed4b6c42b0fea1ac97352209f47ff52f3b52`
  Bean Wiki recipe, inspected only; no event delivery.
- Autofolio `ca88433cf155fd03d616584fda7ed4aa3d33fd71`
  v0.6 integration config and three-layer divergence ledger, inspected only.
- Agent Runtime `main@e23ed65da8de8a9fe6305c3a6ca9955bb0e5c0fb`.

## Target Files

- tests/fixtures/pilots/bean-wiki
- reviews/PILOT-BEAN-WIKI-v080.md
- scripts/pilot_acceptance.py
- tests/test_pilot_acceptance.py

## Scope

Use disposable clean worktrees. Preserve Bean Wiki's editorial assets with an
explicit v2 ownership and host-context adapter, then execute:

1. a deterministic adoption inventory, plan, reconcile, safe apply, and lock;
2. a read-only specialist review of `coffee-flavor-wheel.html`; and
3. a process-level checkpoint/restart/resume task.

The only allowed Bean content operation is reading. Runtime/evidence artifacts
may be written under the claimed pilot surface. The consumer branch is never
committed or pushed.

## Steps

1. Verify both dirty primary checkouts are untouched, create clean pinned
   worktrees, and hash the full Bean host-asset allowlist.
2. Write the bounded v2 config plus `agents/host/HOST-CONTEXT.yml` and role
   overlay. Record that bootstrap diff against the persisted upstream claim.
3. Run `doctor --pre-adoption`, `adopt --plan --json`, `sync --reconcile
   --json`, then `sync --apply-safe`; refuse unexpected conflicts or unsafe
   targets. Write and check the v2 lock only after reconcile is acceptable.
4. Register/claim each local pilot task before its post-bootstrap diff. Record
   deterministic-preflight and requested/selected/resolved/observed routing
   fields.
5. Review `coffee-flavor-wheel.html` against the existing editorial SSOT
   without editing it. Store only bounded local review evidence.
6. Cause one intentional validation failure in a disposable pilot fixture,
   record it through Compound, and prove a matching lookup retrieves it before
   the next task.
7. Create a continuity checkpoint, terminate the first CLI process, start a
   second process, and prove it resumes the same task/claim. Generate and
   re-evaluate the Scribe projection without editing `BACKLOG.md`.
8. Run Bean's `build:content`, `check-content`, `check:editorial`, and
   `git diff --check` gates as available. Record commands, return codes, and
   bounded output digests.
9. Export a sanitized offline fixture into Agent Runtime, validate positive
   and tampered negative cases, triage findings, then discard the Bean
   worktree without committing or pushing it.

## Acceptance Criteria

- Unexpected host overwrite count is zero.
- Doctor blockers and dangling dependencies are zero.
- Bootstrap provenance and task claims cover every pilot diff.
- The three pilot tasks, Compound retrieval, Scribe projection, and
  process-level restart have replayable evidence.
- Existing host assets and all `src/content/**` files are byte-identical.
- Routing evidence never promotes configured intent into an observed model or
  token/cost claim.
- Publish, deploy, origin-push, host-commit, credential-read, and
  network-delivery counters are all zero.

## Verification

- `python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py tests/test_model_routing.py tests/test_scribe_due.py -q`
- `python scripts/pilot_acceptance.py --host bean-wiki --check`
- `python -m pytest tests/test_pilot_acceptance.py -q`

## Handoff

Attach pinned SHAs, before/after digests, reconcile counts, duration, footprint,
seams, bootstrap provenance, task traces, Compound query evidence,
Scribe/restart evidence, routing truth, Bean verification output, and
P0/P1/P2 findings.

## Stop Boundary

Stop before live publish, deploy, origin push, host commit, credential access,
network delivery, content mutation, modification of either dirty primary
checkout, or any unsupported success/cost claim.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-29T16:29:20+09:00`
- Resolution: `done`
- Actual hours: `0.88`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Provider token and cost usage were not exposed; elapsed wall time is recorded separately as actual_hours.
- Closed by: `le-20260729-task-ar-648-001-codex`
- Verification evidence:
  - `reviews/VERIFY-2026-07-29-unit-task-ar-648-001-20260729162858.json`
- Reviews:
  - `reviews/W4B-2026-07-29-unit-task-ar-648-001.md`
<!-- work-close:end -->
