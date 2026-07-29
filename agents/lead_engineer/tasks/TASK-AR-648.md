---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-648
display_id: TASK-AR-648
task_uid: a6d807f7-f61e-402c-b5e9-d50b3de23bf6
work_id: TASK-AR-648
work_uid: a6d807f7-f61e-402c-b5e9-d50b3de23bf6
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T18:34:22+09:00
started_at: 2026-07-29T15:36:41+09:00
title: Run the Bean Wiki web-content pilot
status: in_progress
priority: P0
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-003.md
reservation_id: RES-20260728-163601-b8c2a87a-10
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-p0-remediation-replan.md
created_by: codex-root-v080-planner
summary: Repair the release-blocking defects observed by two reversible Bean Wiki attempts, then replay adoption from a fresh pinned worktree without weakening host ownership, SCM, packaging, or evidence truth.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-153641-task-ar-648-648001.json
  - agents/runtime/task_claims/CLAIM-20260729-171404-task-ar-648-648002.json
---

# TASK-AR-648 - Run the Bean Wiki web-content pilot

## Current Phase

- `UNIT-TASK-AR-648-001` completed the red pilot and independently verified
  five P0 defects. Its evidence is integrated at Agent Runtime
  `main@ec08a3d8c2a6613f508f1d9fd3f2f67693b4a92b`.
- `UNIT-TASK-AR-648-002` repairs only those five P0 defects and reruns the
  adoption from a fresh Bean Wiki worktree. Its integrated code repair passed,
  but the first green replay independently found two additional P0s and is
  therefore blocked.
- `UNIT-TASK-AR-648-003` makes claim SCM mutation explicitly opt-in, packages
  the state-projection dependency for standalone installed-host scripts, and
  repeats the replay in a second fresh Bean Wiki worktree. P1 profile,
  overlay-execution, and provider-observability work remains separately queued.

## Goal

- Determine, with replayable evidence, whether reversible Agent Runtime adoption
  preserves Bean Wiki's existing editorial harness while adding task trace,
  Compound, Scribe, continuity, and model-routing controls.
- Treat footprint, role-overlay execution, and cost claims as hypotheses. Do not
  call the adoption lightweight or economical unless the recorded evidence
  supports those claims.

## Scope

- Use a clean worktree pinned to Bean Wiki
  `origin/main@357eee4fd8c29c33a949adbe3a0ffa80c874bf42`.
- Preserve the completed red-pilot baseline at Agent Runtime
  `main@e23ed65da8de8a9fe6305c3a6ca9955bb0e5c0fb`; implement remediation from
  `main@ec08a3d8c2a6613f508f1d9fd3f2f67693b4a92b`, then apply the repaired
  package template with `profiles: [web-content]` (`core` is implicit) and v2
  ownership in a fresh disposable worktree.
- Preserve Bean Wiki's `AGENTS.md`, `CLAUDE.md`, `BACKLOG.md`,
  `.claude/agents/**`, `.claude/skills/**`, and editorial documents as
  host-owned inputs. Use `BACKLOG.md` as the Scribe state adapter.
- Run three bounded, non-publishing pilot tasks: deterministic adoption
  inventory/apply, a read-only specialist review of
  `coffee-flavor-wheel.html`, and process-level restart recovery.
- Demonstrate one real Compound record-and-retrieve loop from an intentional
  negative adoption test. Capture all Bean worktree changes as disposable
  evidence; do not commit or push the consumer branch.
- Build an offline acceptance fixture and validator in Agent Runtime so CI does
  not depend on the sibling Bean Wiki checkout.

## Acceptance Criteria

- The Bean baseline SHA and every preserved host asset have before/after
  digests; unexpected overwrite count is zero.
- Reconcile output records the exact selected, managed, seeded, preserved,
  excluded, conflict, and added path counts. The report explicitly records
  that the pinned baseline selects 243 `core+web-content` files, of which 237
  default to managed ownership, unless implementation evidence disproves the
  W0 measurement.
- Bootstrap changes map to the persisted upstream `TASK-AR-648` claim; every
  post-bootstrap Bean diff maps to a local pilot task/claim. Unmapped diff
  count is zero.
- Three real tasks complete with trace. The editorial task is read-only with
  respect to `src/content/**`; the restart task resumes from persisted
  checkpoint/claim state in a new process.
- One intentional, non-product negative test produces a Compound record and a
  later matching lookup retrieves it. Scribe writes only its generated
  projection and never edits `BACKLOG.md`.
- Requested tier, selected tier, resolved route, execution surface, and any
  actually observed model/reasoning are separate fields. Token/cost savings
  remain `unavailable` unless provider observations exist.
- No live content publish, deploy, origin push, credential read, or network
  delivery occurs. External-effect counters remain zero.
- Findings are triaged as release-blocking P0, pre-GA P1, or later P2. A P0
  pilot finding blocks `TASK-AR-651` rather than being narrated as success.
- Register-then-dispatch, linked-worktree self-claim, installed-example
  classification, configured state projection, and post-registration
  reconcile all have focused regressions and pass in a fresh Bean replay.
- Default claim creation in an adopted consumer repository leaves Git `HEAD`
  unchanged; crash-safety commits remain available only through an explicit,
  tested opt-in.
- Installed Scribe/state-sync scripts run from a clean consumer process with
  no source checkout, editable install, or ambient `PYTHONPATH`.
- The green replay has zero P0 findings, zero reconcile conflicts, zero
  unexpected host/content mutations, zero host commits, and zero external
  effects. The original red evidence and the blocked first green attempt
  remain immutable and distinguishable from the successful replay.

## Verification

- `python -m pytest tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py -q`
- `python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q`
- `python scripts/pilot_acceptance.py --host bean-wiki --check`
- `python -m pytest tests/test_pilot_acceptance.py -q`
