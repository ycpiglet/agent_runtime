---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-654-001
work_uid: 4b57e68f-5a15-4afe-adf2-492f583d3932
kind: unit
parent_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
task_id: TASK-AR-654
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: failed
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-08-02T20:02:52+09:00
started_at: 2026-07-31T04:07:35+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Enforce repeated-failure Compound closure and ship its skill
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - cross_cutting
  - repeated_failure
defect_signatures:
  - defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694
  - defect:accepted-watch-malformed-utf8-fail-open:eac1aefa14add5d1
  - defect:claim-repeated-failure-signals-lost-at-closure:1da2d2d41b194afb
  - defect:accepted-watch-unbounded-raw-file-read:ceb1edfdb452964a
  - defect:released-claim-scalar-authority-shape-accepted:12a9795c8b117218
  - defect:claim-ref-symlink-escapes-canonical-claim-store:09782265a699dc29
  - defect:unit-spec-symlink-alias-accepted-as-canonical-id:8f8644f6caac78e7
  - defect:relative-worktree-falls-back-to-linked-root-shad:a9421e5faf4c59df
  - defect:work-frontmatter-identity-contradicts-canonical:bb011854a4cc3ca2
  - defect:deep-accepted-watch-json-recursion-fail-open:5d494f605a860dac
  - defect:active-claim-symlink-escapes-canonical-claim-sto:3e1307eb404a2428
  - defect:falsy-non-string-unit-spec-falls-back-to-canonic:64fe169f1ab37824
  - defect:falsy-non-string-work-identity-treated-as-missin:2349f1fed3ad7660
  - defect:untrusted-unit-id-bypasses-canonical-claim-conte:9950c5dcb729c2d4
  - defect:broken-ancestor-symlink-hides-canonical-active-c:23158c0595f498bb
  - defect:windows-junction-parent-hides-canonical-active-c:731de644205f5d8d
  - defect:unreadable-active-claim-store-enumerates-as-empt:c7816e3946c29101
  - defect:missing-intermediate-claim-store-parent-hides-ac:4560560004a1fb77
  - defect:active-claim-symlink-loop-escapes-bounded-handli:49bf17a5e1901460
  - defect:claim-status-casing-hides-active-repeated-failur:43313896c2b45087
  - defect:direct-claim-store-replacement-hides-canonical-a:7477bae20f4a3c1f
  - defect:deep-active-claim-json-escapes-bounded-handling:6694294b2602e0ce
  - defect:claim-id-escapes-canonical-artifact-namespace:84dd007e34346fae
  - defect:claim-evidence-alias-escapes-repository-boundary:422a442d426e3c59
  - defect:tracked-inner-marker-activates-without-checkout:7eaad2998875a161
  - defect:claim-store-snapshot-accepts-stale-or-aliased-ba:165eeaa33e9e0650
  - defect:claim-store-marker-activation-leaves-partial-aut:4d351ca878f09963
  - defect:atomic-no-clobber-publication-accepts-destinatio:b5af68a325007016
  - defect:atomic-publication-accepts-aliased-parent-compon:e89f4bf8d6bd13c4
  - defect:claim-create-failure-leaves-partial-transaction:36409fe931d01cfd
  - defect:inactive-claim-re-release-rebinds-verification-p:da793d1a17eecca2
  - defect:incomplete-role-overlay-is-accepted-as-idempoten:88dc7419f9159bb4
  - defect:atomic-publisher-reports-failure-after-committed:2e080352410acda0
  - defect:role-overlay-rollback-deletes-replacement-artifa:24910ed49f07f9b7
  - defect:claim-store-witness-accepts-unknown-claim-status:8e42ea5ea2d844c9
  - defect:partial-compound-coverage-satisfies-declared-def:90587dadec03fe8f
  - defect:claim-json-accepts-nonfinite-or-duplicate-fields:2fc824544a55622d
  - defect:sync-reports-zero-after-committed-claim-migratio:4317243460108472
  - defect:post-commit-fallible-step-reverses-durable-autho:cb20f7de91cd1390
  - defect:work-status-hides-active-claim-integrity-failure:f48114a15d1fee23
compound_refs:
  - agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-195951-bind-claim-authority-to-one-durable-no-clobber-t-3b8cec108077.json
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260731-040735-task-ar-654-ar654001.json
  - agents/runtime/task_claims/CLAIM-20260801-000156-task-ar-654-ar654repair001.json
context: The claim dispatcher already searches canonical Compound records, but closure_gate accepts any one of compound, review, or retro. The failure-to-regression skill exists only in the Runtime repository and is absent from consumer templates.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - reviews/REVIEW-2026-07-31-task-ar-654-compound-closure-t3-replan.md
  - reviews/REVIEW-2026-07-31-task-ar-654-rsi-skill-contract-scope-amendment.md
  - reviews/REVIEW-2026-08-01-task-ar-654-splitlines-boundary-t3-replan.md
  - reviews/REVIEW-2026-08-01-task-ar-654-compound-record-scope-amendment.md
  - reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md
  - reviews/REVIEW-2026-08-01-task-ar-654-failclosed-compound-scope-amendment.md
  - reviews/AUDIT-2026-08-02-task-ar-654-canonical-authority-probe.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-deep-json-failopen-interruption.md
  - reviews/REVIEW-2026-08-02-task-ar-654-canonical-authority-t3-replan.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md
  - reviews/SKEPTIC-2026-08-02-task-ar-654-canonical-authority-final.md
  - reviews/REVIEW-2026-08-02-task-ar-654-falsy-authority-t3-replan.md
  - reviews/REVIEW-2026-08-02-task-ar-654-strict-authority-compound-scope-amendment.md
  - reviews/W4A-2026-08-02-unit-task-ar-654-001-strict-authority-final.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-strict-authority-final.md
  - reviews/SKEPTIC-2026-08-02-task-ar-654-strict-authority-final.md
  - reviews/REVIEW-2026-08-02-task-ar-654-broken-parent-store-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-store-component-final.md
  - reviews/AUDIT-2026-08-02-task-ar-654-windows-reparse-parent.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-store-components-t3-replan.md
  - reviews/REVIEW-2026-08-02-task-ar-654-work-close-fixture-scope-amendment.md
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-authority-continuity-final.md
  - reviews/AUDIT-2026-08-02-task-ar-654-windows-native-evidence-final.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-store-continuity-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-transaction-boundary.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-transaction-continuity-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-precommit-authority-seams.md
  - reviews/REVIEW-2026-08-02-task-ar-654-authority-seams-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-preverify-transaction-truth.md
  - reviews/REVIEW-2026-08-02-task-ar-654-transaction-truth-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-combined-green-precommit.md
  - reviews/REVIEW-2026-08-02-task-ar-654-postcommit-projection-t3-replan.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-transaction-compound-scope-amendment.md
  - reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
  - reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
  - reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
  - src/agent_runtime/knowledge_records.py
  - src/agent_runtime/templates/project/scripts/compound_record.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - skills/failure-to-regression/SKILL.md
target_files:
  - src/agent_runtime/knowledge_records.py
  - scripts/work.py
  - src/agent_runtime/templates/project/scripts/work.py
  - scripts/atomic_io.py
  - src/agent_runtime/templates/project/scripts/atomic_io.py
  - scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - scripts/stop_hook_closure_gate.py
  - src/agent_runtime/templates/project/scripts/stop_hook_closure_gate.py
  - src/agent_runtime/templates/project/scripts/compound_record.py
  - skills/failure-to-regression/SKILL.md
  - new:src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - agents/project/TEMPLATE-MIRROR-CONTRACT.json
  - tests/fixtures/host/agent_runtime.lock.json
  - tests/test_closure_gate.py
  - tests/test_compound_records.py
  - tests/test_work_close.py
  - src/agent_runtime/claim_store.py
  - scripts/agent_runtime/claim_store.py
  - src/agent_runtime/templates/project/scripts/agent_runtime/claim_store.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - scripts/role_routing.py
  - src/agent_runtime/templates/project/scripts/role_routing.py
  - scripts/claim_reaper.py
  - src/agent_runtime/templates/project/scripts/claim_reaper.py
  - scripts/claim_guard.py
  - src/agent_runtime/templates/project/scripts/claim_guard.py
  - scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - src/agent_runtime/sync.py
  - src/agent_runtime/adoption.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/lock.py
  - scripts/template_mirror_gate.py
  - scripts/inflight_overlay.py
  - src/agent_runtime/templates/project/scripts/inflight_overlay.py
  - .github/workflows/test.yml
  - new:agents/runtime/task_claims/.claim-store
  - tests/test_atomic_io.py
  - tests/test_claim_store.py
  - tests/test_lifecycle_defaults.py
  - tests/test_inflight_overlay.py
  - tests/test_claim_guard.py
  - tests/test_parallel_worktree_gate.py
  - tests/test_adoption.py
  - tests/test_doctor.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_role_routing.py
  - tests/test_claim_reaper.py
  - tests/test_claim_reaper_concurrency.py
  - tests/test_claim_reaper_hook.py
  - tests/test_deadlock_watchdog.py
  - tests/test_template_mirror_gate.py
  - tests/host_contracts/test_autofolio_task_claim_dispatcher.py
  - tests/host_contracts/test_autofolio_wave_dispatcher.py
  - tests/test_runtime_asset_usage.py
  - tests/test_rsi_operating_system_docs.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_lock_merge_driver.py
  - tests/test_regen_host_lock_if_needed.py
  - agents/project/knowledge/compounds/records/COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json
  - agents/project/knowledge/compounds/INDEX.json
  - reviews/INDEX.md
scope: Tighten only the repeated-failure lane and preserve ordinary review/retro closure compatibility.
acceptance:
  - Repeated failures cannot bypass Compound.
  - Valid linked Compounds collectively cover every declared defect signature.
  - Compound dedupe and lookup remain deterministic.
  - The skill is discoverable in a freshly adopted host.
  - No legacy Compound log is rewritten.
  - A tracked inner marker requires explicit checkout activation without generation rebinding.
  - New authority uses canonical no-clobber publication and identity-bound rollback.
  - No fallible post-commit cleanup or ownership-capture step can reverse a durable authority result.
  - Complete snapshots and W0 status use the bounded locked canonical claim reader.
  - Shared JSON rejects every non-finite number and sync reports its observed committed post-state.
  - Inactive re-release preserves verification provenance and role idempotency validates the complete deterministic contract.
  - Native Windows Python 3.10, 3.11, and 3.12 evidence is required before release.
verification:
  - python -m pytest -q
  - python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/template_mirror_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Attach the failure-first transaction matrix, native Windows evidence state, full-suite Verify, complete Compound coverage proof, template parity, W4a, independent W4b, and skeptic verdict.
stop_condition: Stop before rewriting legacy Compound history, widening Compound to ordinary work, dispatching CI without Owner approval, or performing version, publish, deployment, consumer, or external release actions.
verified_at: 2026-08-02T19:50:23+09:00
verified_by: le-20260801-000005-kst-ar654repair001
evidence_refs:
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731043905.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731050030.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731052414.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731054736.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731061244.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731233354.json
  - reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801002151.json
  - reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801014422.json
  - reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801015750.json
  - reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802122023.json
  - reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802132243.json
  - reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802195023.json
review_refs:
  - reviews/REVIEW-2026-08-01-task-ar-654-failclosed-compound-scope-amendment.md
  - reviews/W4A-2026-08-01-unit-task-ar-654-001-failclosed-authority-repair.md
  - reviews/AUDIT-2026-08-02-task-ar-654-canonical-authority-probe.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-deep-json-failopen-interruption.md
  - reviews/REVIEW-2026-08-02-task-ar-654-canonical-authority-t3-replan.md
  - reviews/REVIEW-2026-08-02-task-ar-654-canonical-compound-scope-amendment.md
  - reviews/W4A-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md
  - reviews/SKEPTIC-2026-08-02-task-ar-654-canonical-authority-final.md
  - reviews/REVIEW-2026-08-02-task-ar-654-falsy-authority-t3-replan.md
  - reviews/REVIEW-2026-08-02-task-ar-654-strict-authority-compound-scope-amendment.md
  - reviews/W4A-2026-08-02-unit-task-ar-654-001-strict-authority-final.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-strict-authority-final.md
  - reviews/SKEPTIC-2026-08-02-task-ar-654-strict-authority-final.md
  - reviews/REVIEW-2026-08-02-task-ar-654-broken-parent-store-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-store-component-final.md
  - reviews/AUDIT-2026-08-02-task-ar-654-windows-reparse-parent.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-store-components-t3-replan.md
  - reviews/REVIEW-2026-08-02-task-ar-654-work-close-fixture-scope-amendment.md
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-authority-continuity-final.md
  - reviews/AUDIT-2026-08-02-task-ar-654-windows-native-evidence-final.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-store-continuity-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-transaction-boundary.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-transaction-continuity-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-precommit-authority-seams.md
  - reviews/REVIEW-2026-08-02-task-ar-654-authority-seams-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-preverify-transaction-truth.md
  - reviews/REVIEW-2026-08-02-task-ar-654-transaction-truth-t3-replan.md
  - reviews/AUDIT-2026-08-02-task-ar-654-combined-green-precommit.md
  - reviews/REVIEW-2026-08-02-task-ar-654-postcommit-projection-t3-replan.md
  - reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
  - reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md
  - reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
  - reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
---

# UNIT-TASK-AR-654-001 - Enforce repeated-failure Compound closure and ship its skill

## Context

The claim dispatcher already searches canonical Compound records, but closure_gate accepts any one of compound, review, or retro. The failure-to-regression skill exists only in the Runtime repository and is absent from consumer templates.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- reviews/REVIEW-2026-07-31-task-ar-654-compound-closure-t3-replan.md
- reviews/REVIEW-2026-08-01-task-ar-654-compound-record-scope-amendment.md
- reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md
- reviews/REVIEW-2026-08-01-task-ar-654-failclosed-compound-scope-amendment.md
- reviews/AUDIT-2026-08-02-task-ar-654-canonical-authority-probe.md
- reviews/W4B-2026-08-02-unit-task-ar-654-001-deep-json-failopen-interruption.md
- reviews/REVIEW-2026-08-02-task-ar-654-canonical-authority-t3-replan.md
- reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
- reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
- src/agent_runtime/knowledge_records.py
- src/agent_runtime/templates/project/scripts/compound_record.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- skills/failure-to-regression/SKILL.md

## Target Files

- src/agent_runtime/knowledge_records.py
- scripts/work.py
- src/agent_runtime/templates/project/scripts/work.py
- scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- scripts/stop_hook_closure_gate.py
- src/agent_runtime/templates/project/scripts/stop_hook_closure_gate.py
- src/agent_runtime/templates/project/scripts/compound_record.py
- skills/failure-to-regression/SKILL.md
- new:src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
- agents/project/RUNTIME-ASSET-REGISTRY.json
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- agents/project/TEMPLATE-MIRROR-CONTRACT.json
- tests/fixtures/host/agent_runtime.lock.json
- tests/test_closure_gate.py
- tests/test_compound_records.py
- tests/test_work_close.py
- tests/test_task_claim_dispatcher.py
- tests/test_runtime_asset_usage.py
- tests/test_rsi_operating_system_docs.py
- tests/test_inventory_sync_sanitize.py
- tests/test_lock_merge_driver.py
- tests/test_regen_host_lock_if_needed.py
- agents/project/knowledge/compounds/records/COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b.json
- agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json
- agents/project/knowledge/compounds/INDEX.json

## Scope

Tighten only the repeated-failure lane and preserve ordinary review/retro closure compatibility.

## Steps

1. Add a negative where repeated_failure closes with review only.
2. Aggregate task/unit repeated-failure signals and require a current-work
   canonical Compound with a repository-contained supported prevention
   destination.
3. Rewrite, copy, validate, and register the failure-to-regression skill in the
   consumer core template without root-only casebook dependencies.
4. Verify ordinary non-repeated work remains compatible.

## Acceptance Criteria

- Repeated failures cannot bypass Compound.
- Valid linked Compounds collectively cover every declared defect signature.
- Compound dedupe and lookup remain deterministic.
- The skill is discoverable in a freshly adopted host.
- No legacy Compound log is rewritten.
- A tracked inner marker requires explicit checkout activation without generation rebinding.
- New authority uses canonical no-clobber publication and identity-bound rollback.
- No fallible post-commit cleanup or ownership-capture step can reverse a durable authority result.
- Complete snapshots and W0 status use the bounded locked canonical claim reader.
- Shared JSON rejects every non-finite number and sync reports its observed committed post-state.
- Inactive re-release preserves verification provenance and role idempotency validates the complete deterministic contract.
- Native Windows Python 3.10, 3.11, and 3.12 evidence is required before release.

## Verification

- `python -m pytest -q`
- `python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/template_mirror_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Attach the failure-first transaction matrix, native Windows evidence state,
full-suite Verify, complete Compound coverage proof, template parity, W4a,
independent W4b, and skeptic verdict.

## Stop Boundary

Stop before rewriting legacy Compound history, widening Compound to ordinary
work, dispatching CI without Owner approval, or performing version, publish,
deployment, consumer, or external release actions.

## Reopened after skeptic closeout

The 2026-07-31 skeptic closeout found a P1 physical-line boundary bypass after
the prior W4a/W4b sequence. The unit is therefore failed and reopened under
`reviews/REVIEW-2026-08-01-task-ar-654-splitlines-boundary-t3-replan.md` until
the exact repaired candidate passes fresh machine evidence, W4a, independent
W4b, and skeptic review.

## Compound record scope amendment

The repeated-failure repair owns its current-work canonical Compound record and
generated Compound index under
`reviews/REVIEW-2026-08-01-task-ar-654-compound-record-scope-amendment.md`.
This does not widen the ordinary-work closure contract or permit legacy record
rewrites.

## Reopened after fail-closed authority reviews

The physical-line matrix passed, but fresh W4b and skeptic reviews found
malformed-UTF-8 fail-open behavior, lost active-claim repeated-failure
authority, an unbounded raw accepted-watch read, and two closeout metadata
inconsistencies. The unit remains failed under
`reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md` until
one new candidate passes fresh machine, W4a, W4b, skeptic, and actual closeout
validation.

## Corrective Compound scope amendment

The fresh Verify-backed record at
`agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json`
is an additive lifecycle target under
`reviews/REVIEW-2026-08-01-task-ar-654-failclosed-compound-scope-amendment.md`.
The earlier physical-line record remains immutable and is retained only as
source history.

## Reopened after canonical authority probes

The W4a candidate is superseded for release purposes by
`reviews/AUDIT-2026-08-02-task-ar-654-canonical-authority-probe.md` and
`reviews/W4B-2026-08-02-unit-task-ar-654-001-deep-json-failopen-interruption.md`.
The unit is failed and reopened under
`reviews/REVIEW-2026-08-02-task-ar-654-canonical-authority-t3-replan.md` for six
new failure-first repairs and an entirely fresh W4 sequence.

## Reopened after final canonical-authority reviews

The candidate recorded by the prior W4a is superseded by the final W4b and
skeptic reviews. Four strict-authority classes remain open: direct active-claim
store identity, typed non-empty unit specs, typed canonical frontmatter
identity, and path-derived close resolver identity. The unit remains failed
under `reviews/REVIEW-2026-08-02-task-ar-654-falsy-authority-t3-replan.md` until
the new REDs, implementation, Verify, Compound, W4a, W4b, and skeptic sequence
is complete.

## Strict-authority Compound scope amendment

The append-only record at
`agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json`
is now a current-work authority target under
`reviews/REVIEW-2026-08-02-task-ar-654-strict-authority-compound-scope-amendment.md`.
It binds both work IDs and all four new signatures to the fresh Verify without
changing the three earlier records.

## Canonical-authority Compound scope amendment

The exact append-only prevention record at
`agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json`
is now part of this unit under
`reviews/REVIEW-2026-08-02-task-ar-654-canonical-compound-scope-amendment.md`.
It links the task and unit to all six new stable signatures and the fresh
machine evidence while preserving both prior records unchanged.

## Work-close fixture scope amendment

`tests/test_work_close.py` is now an explicit target under
`reviews/REVIEW-2026-08-02-task-ar-654-work-close-fixture-scope-amendment.md`.
The only authorized edit is central fixture alignment with the installed-host
direct Runtime parent contract.

## Reopened after claim-store continuity audits

The component candidate and its fixture-only follow-up are superseded by
`reviews/AUDIT-2026-08-02-task-ar-654-claim-authority-continuity-final.md` and
`reviews/AUDIT-2026-08-02-task-ar-654-windows-native-evidence-final.md`. The
unit remains failed under
`reviews/REVIEW-2026-08-02-task-ar-654-claim-store-continuity-t3-replan.md`
until the failure-first witness, status, bounded-input, migration, native
Windows, machine, Compound, and new W4 sequence is complete.

## Refined after claim transaction-boundary audit

The durable witness work now also owns the create/update transaction boundary
under
`reviews/REVIEW-2026-08-02-task-ar-654-claim-transaction-continuity-t3-replan.md`.
The unit remains failed while canonical claim/evidence paths, explicit
tracked-inner activation, snapshot-bound marker creation, exclusive
publication, identity-bound rollback, immutable release provenance, complete
role-overlay idempotency, native Windows execution, fresh Verify/Compound, and
the new W4 sequence are incomplete.

## Reopened after authority-seam audit

The candidate remains failed under
`reviews/REVIEW-2026-08-02-task-ar-654-authority-seams-t3-replan.md` until
publication truth, identity-bound rollback, canonical active/released/witness
reading, full declared-signature coverage, strict JSON, deterministic overlay
seed validation, native junction selection, and truthful sync partial-state
reporting pass fresh machine and independent review.

## Refined after transaction-truth preverify

The locally green dirty candidate is superseded by
`reviews/AUDIT-2026-08-02-task-ar-654-preverify-transaction-truth.md`. The
unit remains failed under
`reviews/REVIEW-2026-08-02-task-ar-654-transaction-truth-t3-replan.md` while
post-commit ownership/cleanup truth, complete snapshots, canonical W0 status,
finite JSON, actual sync post-state, and complete stable role metadata lack
failure-first proof. Native Windows and all fresh W4 evidence remain pending.

## Refined after combined-green precommit review

The `4230 passed` local baseline is superseded by
`reviews/AUDIT-2026-08-02-task-ar-654-combined-green-precommit.md`. The unit
remains failed under
`reviews/REVIEW-2026-08-02-task-ar-654-postcommit-projection-t3-replan.md`
until post-close projection warnings, sync exit truth, optional SCM isolation,
marker-aware witness preservation, and canonical dispatcher/W0 projections
have failure-first proof. Adjacent release blockers remain assigned to their
existing planned tasks and do not broaden this unit.

## Fresh local Verify; native Windows still pending

`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802195023.json` records
the exact post-implementation local candidate passing all five registered
commands, including `4249 passed, 11 skipped` for the full suite and `1251
passed, 2 skipped` for the focused governance suite. The evidence, verifier,
and timestamp remain preserved above, but `verification_status` remains
`failed` until the native Windows 3.10/3.11/3.12 matrix and fresh exact-commit
W4a, independent W4b, and skeptic review are available. This is not release
authorization.

The append-only claim-transaction Compound now covers the remaining 26
signatures. Together with the three immutable earlier records, linked valid
Compound coverage is complete for all 40 declared signatures; the unit stays
failed only for the fresh exact-commit review sequence and native Windows
execution boundary described above.
