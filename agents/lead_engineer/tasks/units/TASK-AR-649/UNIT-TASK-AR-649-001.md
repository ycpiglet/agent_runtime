---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-649-001
work_uid: 34e7d639-192e-47ed-ade2-bff02162b8c0
kind: unit
parent_id: TASK-AR-649
unit_id: UNIT-TASK-AR-649-001
task_id: TASK-AR-649
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
team: risk-and-safety
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-30T07:44:00+09:00
started_at: 2026-07-30T07:44:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Adopt and exercise core plus security-service in Allimbot
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - security
  - data_integrity
  - external_effect
  - cross_cutting
risk_tier: high
approval_required: false
security_sensitive: true
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-074400-task-ar-649-ar649001.json
repository_path: /home/keti-itp-01/ycpiglet/.control-clones/agent-runtime-task-ar-648
worktree_path: /home/keti-itp-01/ycpiglet/.control-clones/agent-runtime-task-ar-648/.worktrees/TASK-AR-648-002-impl
branch: codex/unit-task-ar-648-002-implementation
base_ref: d2e89c74db6d4d5e0cec5b061bd5563e5acb12d7
adopt_existing_branch: true
context: Allimbot already has mature product security and durable event integration but no common development-process task/claim/compound/scribe/model-cost harness. Bean Wiki is independently green. The exact Runtime product is frozen at 4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2. Allimbot primary is dirty with unrelated Owner work and is observation-only; target and control must start clean at 5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd.
inputs:
  - reviews/W4B-2026-07-30-unit-task-ar-648-016.md
  - reviews/REVIEW-2026-07-30-task-ar-649-allimbot-t3-replan.md
  - docs/ALLIMBOT-INTEGRATION.md
  - docs/pilot-acceptance-contract.md
  - docs/pilot-isolation-contract.md
  - agent-runtime-product@4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2
  - agent-runtime-lifecycle@d2e89c74
  - allimbot@5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd
target_files:
  - new:tests/fixtures/pilots/allimbot/evidence-green-attempt-1.json
  - new:tests/fixtures/pilots/allimbot/isolation-green-attempt-1.json
  - new:tests/fixtures/pilots/contracts/allimbot-v080-green-attempt-1.json
  - new:reviews/PILOT-ALLIMBOT-v080-GREEN-ATTEMPT-1.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-649-001.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-649-001.md
  - new:reviews/REVIEW-2026-07-30-task-ar-649-allimbot-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-649.md
  - agents/lead_engineer/tasks/units/TASK-AR-649/UNIT-TASK-AR-649-001.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - agents/runtime/a2a/messages.jsonl
  - new:agents/runtime/instances/codex-root-task-ar-649-001.json
  - agents/runtime/pane_events/pane-events.jsonl
  - new:agents/runtime/task_claims/CLAIM-20260730-074400-task-ar-649-ar649001.handoff.md
  - new:agents/runtime/task_claims/CLAIM-20260730-074400-task-ar-649-ar649001.json
  - new:agents/runtime/task_claims/CLAIM-20260730-074400-task-ar-649-ar649001.log.md
  - BACKLOG-BOARD.md
  - ARCHIVE-INDEX.md
  - reviews/INDEX.md
scope: From a fresh target and same-commit frozen control at Allimbot 5cc15ff3, apply exact Runtime 4929415d core plus security-service. Preserve .env.example and .gitattributes as host-owned, use docs/PROJECT_STATUS.ko.md as the host-owned Scribe source, and declare auth, Supabase migration, workflow, and Vercel surfaces as risk paths. Run exactly three offline traces: ordinary adoption at worker_low, one Critical read-only auth/security review with one independent reviewer, and worker_low native-event spool recovery plus Compound, restart, and Scribe. The live dirty primary is observation-only. No product-file edit, consumer commit, install, credential read, flush, network delivery, migration, deploy, or release action is allowed.
acceptance:
  - Runtime execution is pinned to 4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2 and its exact product, template, and scripts trees; the detached product checkout stays clean.
  - Target and control start at Allimbot 5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd. The frozen control never changes. Live-primary drift is observation-only and never attributed to the pilot.
  - Only the disposable target is an observed write root. Raw v1 and digest-bound portable v2 isolation pass with zero blockers.
  - Core plus security-service selects 251 files; ownership, safe apply, lock, doctor, immediate and post-registration reconcile complete with zero conflicts and exact provenance.
  - .env.example, .gitattributes, security/release policy files, native integration recipe, and the complete tracked Allimbot tree retain matching before/after digests. Target HEAD and tracked diff remain unchanged.
  - Exactly three local task, unit, and claim traces complete with truthful requested/selected tiers and unavailable provider telemetry unless actually observed.
  - The Critical task targets registered auth surfaces, carries required high-risk metadata and Security Controls, and receives exactly one distinct independent security review without changing auth or product files.
  - A valid native Runtime event is written only to a disposable Allimbot SQLite spool, survives a second process, has an empty body and exact allowlisted fields, contains no secret marker, and is never flushed or delivered.
  - One intentional unsafe-event negative is rejected before enqueue, creates one task-linked Compound record, and later retrieves that record first without unrelated matches.
  - Two distinct local processes resume the same task and claim; Scribe writes only its configured projection and preserves docs/PROJECT_STATUS.ko.md.
  - Installed no-STATUS continuity, state sync, RBAC, taskset, security-service, Owner governance, and host tests pass without a block finding.
  - A strict allimbot plus allimbot-v080-green-attempt-1 contract binds exact evidence and isolation digests; every Bean contract remains unchanged and passing.
  - Publish, deploy, migration, origin push, consumer commit, credential read/change, network delivery, dependency installation, provider-live execution, spool flush, and product/content mutation counters are integer zero.
  - Canonical W4a and fresh independent W4b pass with no Runtime P0/P1 before release-candidate work.
verification:
  - python scripts/pilot_isolation_gate.py --evidence tests/fixtures/pilots/allimbot/isolation-green-attempt-1.json --check --json
  - python scripts/pilot_acceptance.py --host allimbot --fixture tests/fixtures/pilots/allimbot/evidence-green-attempt-1.json --check --json
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-6.json --check --json
  - python -m pytest tests/test_pilot_isolation_gate.py tests/test_pilot_acceptance.py tests/test_allimbot.py tests/test_security_service.py -q
  - python -m pytest tests/test_task_claim_dispatcher.py tests/test_state_sync_gate.py tests/test_continuity_contract_gate.py tests/test_owner_governance_consumer_host.py tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/runtime_asset_usage.py --check
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
handoff: Attach exact Runtime/Allimbot provenance, target/control/primary snapshots, adoption and preservation counts, three route/claim traces, Critical metadata and independent review, event-spool/restart/secret-rejection evidence, Compound and Scribe results, host test results, raw/portable isolation digests, exact acceptance identity, integer-zero effects, W4a, and independent W4b.
stop_condition: Stop on any Runtime P0/P1, product drift, dirty-primary targeting, frozen-control mutation, write outside the disposable target, host/product overwrite, consumer commit, unreviewed Critical claim, event-policy fail-open, secret-like spool content, flush or delivery call, credential access, dependency install, provider-live execution, migration, external effect, contract ambiguity, release, version, tag, package, push, publish, or deploy action.
---

# UNIT-TASK-AR-649-001 - Adopt and exercise core plus security-service in Allimbot

## Context

Bean Wiki is independently green on exact Runtime product `4929415d`. Allimbot
already has mature product security and durable event integration but no common
development-process task/claim/Compound/Scribe/model-cost harness. Its live
primary contains unrelated Owner changes and is never a pilot target.

## Inputs

- Exact Runtime product `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2`
- Runtime lifecycle baseline `d2e89c74`
- Clean Allimbot baseline `5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd`
- Allimbot primary pre-existing status digest
  `19f6706dc44e5f3d2484715723fc2c2414218f8ec5949872c8a4ddd3f5a956a8`
- Allimbot primary pre-existing tracked-diff digest
  `c90de2ff8397144a33a708f8c551162f6578cea9efcb4af30256cf1246902a69`
- Bean attempt-6 W4b and Runtime pilot isolation/acceptance contracts

## Target Files

- Runtime-only Allimbot evidence, isolation, exact contract, report, W4a/W4b
- Runtime task/unit/pointer/assumption/generated lifecycle records
- Disposable target Runtime projection and bounded pilot evidence only

## Scope

Create one clean target and one frozen control from the exact Allimbot commit.
Capture isolation before writes, install `core+security-service` only in the
target, and run exactly three offline traces. Never copy the live primary's
uncommitted changes into either pilot checkout.

## Steps

1. Re-anchor assumptions, pass readiness and canonical selection, then create
   a default Runtime claim.
2. Create exact product, target, and frozen control; capture primary, target,
   control, Bean, and Runtime isolation before target writes.
3. Apply `core+security-service` with host ownership and risk-path overlays.
4. Run ordinary adoption, Critical independent auth review, and offline native
   event/restart/Compound/Scribe traces.
5. Prove target/control/product preservation, host Python/web/security checks,
   raw and portable isolation, exact contract acceptance, and zero effects.
6. Obtain canonical W4a and a fresh independent W4b.

## Acceptance Criteria

- Exact Runtime and Allimbot provenance plus causal isolation pass.
- Adoption is conflict-free and stable; target HEAD and all tracked product
  bytes remain unchanged.
- Critical work is metadata-gated and independently security-reviewed.
- Native events are allowlisted, secret-free, locally durable across a process
  boundary, and never flushed.
- Compound, restart, Scribe, continuity, taskset, and Owner governance pass.
- Exact acceptance and W4a/W4b have no Runtime P0/P1.

## Security Controls

- Do not read environment files, keyrings, hosted account state, or credentials.
- Inject only non-secret local pilot configuration and use an isolated SQLite
  spool inside the disposable target.
- Never call `flush`, a provider adapter, a remote API, Supabase, or Vercel.
- Review auth paths read-only; no Critical claim starts without canonical
  metadata and a distinct reviewer.

## Rollback

Discard the disposable target. The frozen control and live primary remain
untouched, and Runtime lifecycle evidence records the result.

## External Effect Boundary

Claim and profile gates authorize local evidence work only. They do not
authorize migration, deploy, credential access, remote account mutation,
notification delivery, release, tag, push, or publication.

## Verification

- Exact-product isolation and strict Allimbot acceptance
- Focused Runtime native-event/security/adoption/continuity regressions
- Read-only Allimbot Python/web/security checks with existing dependencies
- Product/control/primary preservation and integer-zero external effects

## Handoff

Return exact provenance and snapshots, adoption counts, complete preservation,
three claim/routing traces, Critical review, local spool/restart/Compound/Scribe
proof, host tests, raw/portable evidence digests, strict contract identity,
zero-effect counters, W4a, and independent W4b.

## Stop Boundary

Stop before any primary/control/product write, product-file edit, consumer
commit, secret or credential read, install, flush, network/provider call,
migration, deploy, release, version, tag, package, push, or publication action.
