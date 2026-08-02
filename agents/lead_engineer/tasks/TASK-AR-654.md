---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-654
display_id: TASK-AR-654
task_uid: ef3cb8e5-d5b9-443e-ad93-5948ade62659
work_id: TASK-AR-654
work_uid: ef3cb8e5-d5b9-443e-ad93-5948ade62659
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-08-03T00:09:30+09:00
started_at: 2026-07-31T04:07:35+09:00
title: Require Compound for declared repeated failures
status: in_progress
priority: P1
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: quality
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-654/UNIT-TASK-AR-654-001.md
reservation_id: RES-20260730-112500-842c7890-03
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
escalation_triggers:
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
  - defect:container-valued-core-claim-identity-permits-dup:53594ebe603a7c1f
review_refs:
  - reviews/REVIEW-2026-07-31-task-ar-654-compound-closure-t3-replan.md
  - reviews/REVIEW-2026-07-31-task-ar-654-rsi-skill-contract-scope-amendment.md
  - reviews/REVIEW-2026-08-01-task-ar-654-splitlines-boundary-t3-replan.md
  - reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
  - reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md
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
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-transaction-compound-scope-amendment.md
  - reviews/W4A-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
  - reviews/REVIEW-2026-08-02-task-ar-654-ancestor-identity-provenance-t3-replan.md
  - reviews/REVIEW-2026-08-02-task-ar-654-w4b-evidence-contract-correction.md
  - reviews/REVIEW-2026-08-02-task-ar-654-adverse-w4b-compound-scope-amendment.md
  - reviews/W4A-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md
  - reviews/SKEPTIC-2026-08-02-task-ar-654-adverse-w4b-repair-final.md
  - reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md
  - reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
  - reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
compound_refs:
  - agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-195951-bind-claim-authority-to-one-durable-no-clobber-t-3b8cec108077.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-232400-bind-ancestor-identity-and-release-provenance-at-e8e801007dc0.json
evidence_refs:
  - reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802195023.json
  - reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802231400.json
summary: Prevent a repeated defect from closing with only a generic review or retro and no reusable prevention record.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260731-040735-task-ar-654-ar654001.json
  - agents/runtime/task_claims/CLAIM-20260801-000156-task-ar-654-ar654repair001.json
acceptance:
  - Claim-time knowledge lookup remains before persistence.
  - A task with repeated_failure or defect signatures cannot close without a linked canonical Compound record.
  - Valid linked Compounds collectively cover every declared defect signature.
  - The Compound prevention record links to a regression, gate, task proposal, or accepted watch state.
  - Generic substantial work may still close with an appropriate linked review or retro.
  - failure-to-regression is included in the consumer core profile and asset registry.
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
---

# TASK-AR-654 - Require Compound for declared repeated failures

## Goal

- Prevent a repeated defect from closing with only a generic review or retro and no reusable prevention record.

## Scope

- Make defect signatures and repeated_failure triggers require a linked canonical Compound record and ship the failure-to-regression operating skill to consumers.

## Acceptance Criteria

- Claim-time knowledge lookup remains before persistence.
- A task with repeated_failure or defect signatures cannot close without a linked canonical Compound record.
- Valid linked Compounds collectively cover every declared defect signature.
- The Compound prevention record links to a regression, gate, task proposal, or accepted watch state.
- Generic substantial work may still close with an appropriate linked review or retro.
- failure-to-regression is included in the consumer core profile and asset registry.
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

## Reopened fail-closed authority repair

Fresh independent review superseded the physical-line W4a for release
purposes. TASK-AR-654 remains in progress under
`reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md` until
malformed input, claim-signal propagation, bounded reads, and both task/unit
closeout authorities pass a new W4 sequence.

## Corrective Compound scope

The exact append-only prevention record created from the fresh machine Verify
is owned under
`reviews/REVIEW-2026-08-01-task-ar-654-failclosed-compound-scope-amendment.md`.
It binds both task and unit authority, all four stable defect signatures, and
the regressions that now prevent malformed, oversized, shadowed, or omitted
claim authority from failing open.

## Reopened canonical authority repair

Independent probing after W4a found five canonical identity/path/type gaps,
and the interrupted W4b found a deep accepted-watch JSON exception that the
actual Stop wrapper silently allowed. The claim remains held under
`reviews/REVIEW-2026-08-02-task-ar-654-canonical-authority-t3-replan.md` until
all six REDs, fresh machine evidence, a new Compound, complete W4b, and fresh
skeptic approval exist.

## Canonical-authority Compound scope

The fresh machine-backed append-only record at
`agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json`
is owned under
`reviews/REVIEW-2026-08-02-task-ar-654-canonical-compound-scope-amendment.md`.
It carries both work IDs and the six canonical path, shape, identity, and deep
JSON signatures without changing either earlier Compound record.

## Reopened strict canonical authority repair

The final canonical-authority W4b and skeptic reviews found four additional
claim-store, typed-field, and resolver-key failures in actual closeout. The
prior W4a is superseded and the claim remains held under
`reviews/REVIEW-2026-08-02-task-ar-654-falsy-authority-t3-replan.md` until
failure-first repairs, fresh machine evidence, a new append-only Compound, and
an entirely fresh W4 sequence all pass.

## Strict-authority Compound scope

The fresh Verify-backed append-only record at
`agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json`
is owned under
`reviews/REVIEW-2026-08-02-task-ar-654-strict-authority-compound-scope-amendment.md`.
It directly links both work IDs and all four new store, type, identity, and
resolver-key signatures while preserving all earlier records unchanged.

## Reopened broken-parent claim-store repair

The strict-authority candidate is superseded by a fresh skeptic P1: a broken
`agents/runtime` symlink makes the canonical active-claim store appear absent
and actual closeout mutates state without its repeated-failure authority. The
claim remains held under
`reviews/REVIEW-2026-08-02-task-ar-654-broken-parent-store-t3-replan.md` until
the failure-first repair, new Verify and Compound evidence, and an entirely
fresh W4 sequence pass.

## Reopened cross-platform claim-store component repair

The first broken-parent repair passed the full suite but was superseded by two
independent audits. Windows junction metadata, unreadable enumeration, missing
intermediate parents, and unbounded entry loops remain open under
`reviews/REVIEW-2026-08-02-task-ar-654-claim-store-components-t3-replan.md`.
No earlier W4 or machine pass authorizes closeout.

## Work-close fixture scope amendment

The full-suite-only fixture alignment for `tests/test_work_close.py` is
authorized by
`reviews/REVIEW-2026-08-02-task-ar-654-work-close-fixture-scope-amendment.md`.
It may create only the direct Runtime parent already guaranteed by consumer
templates; it must not weaken missing-parent production validation.

## Reopened claim-store continuity repair

The component implementation and fixture alignment are superseded for release
purposes by the status-authority, durable-continuity, bounded-JSON, and native
Windows findings recorded in two fresh audits. The claim remains held under
`reviews/REVIEW-2026-08-02-task-ar-654-claim-store-continuity-t3-replan.md`.
No earlier test, Verify, Compound, or W4 result authorizes closeout.

## Refined claim transaction-continuity repair

Failure-first contract review expanded the durable-witness plan to include
canonical artifact/evidence paths, explicit tracked-inner checkout activation,
snapshot-bound marker transactions, exclusive no-clobber publication,
identity-bound create rollback, immutable release provenance, and complete role
overlay idempotency. The exact scope and ten new stable signatures are recorded
in
`reviews/REVIEW-2026-08-02-task-ar-654-claim-transaction-continuity-t3-replan.md`.
The claim remains held; native Windows evidence and an entirely fresh W4
sequence are still required before release.

## Reopened authority-seam repair

Independent precommit review found that a locally green continuity candidate
still misreported post-commit publication, could delete a competing role
artifact, bypassed the canonical reader at closeout/witness seams, and allowed
partial Compound signature coverage. Strict JSON, deterministic overlay seed,
native junction, and truthful partial-sync reporting were also incomplete.
The exact refinement is accepted under
`reviews/REVIEW-2026-08-02-task-ar-654-authority-seams-t3-replan.md`; no prior
local suite or W4 result authorizes release.

## Refined transaction-truth repair

The green dirty-tree baseline is superseded by independent preverify races in
post-commit ownership capture and descriptor cleanup, complete snapshot
validation, W0 claim enumeration, exponent-overflow JSON, sync post-state, and
stable role metadata. The bounded repair is accepted under
`reviews/REVIEW-2026-08-02-task-ar-654-transaction-truth-t3-replan.md`.
TASK-AR-654 remains in progress until the new RED matrix, fresh Verify,
twenty-six-signature Compound coverage, exact-commit W4, and native Windows
evidence are complete.

## Refined post-commit and projection repair

The second green dirty-tree baseline is superseded by reproduced closeout,
sync-exit, optional-SCM, marker-recovery, and projection truth gaps. The
bounded repair is accepted under
`reviews/REVIEW-2026-08-02-task-ar-654-postcommit-projection-t3-replan.md`.
Adjacent W4b authenticity, lease/grace bounds, and portable release cascade
findings remain explicit blockers routed to TASK-AR-657, TASK-AR-655, and
TASK-AR-651; they are not claimed as solved by TASK-AR-654.

## Claim-transaction evidence recorded

Implementation commit `19362133d2dffc91647b23beab8f01956a403f7f` passed
the fresh registered Verify. The fourth append-only Compound now makes all 40
declared defect signatures collectively covered by linked canonical records.
TASK-AR-654 remains in progress for exact-commit W4a, independent W4b,
skeptic review, and native Windows 3.10/3.11/3.12 evidence. This evidence does
not authorize claim release or any external release action.

## Reopened after claim-transaction W4b

Independent W4b rejected candidate `d1300a92` with two P1 and two P2
findings. The bounded repair is accepted under
`reviews/REVIEW-2026-08-02-task-ar-654-ancestor-identity-provenance-t3-replan.md`.
The prior W4a is superseded for approval purposes; the task now declares 41
signatures with one new container-identity signature uncovered until fresh
prevention and an append-only Compound are recorded.

## Adverse-W4b repair implementation green

The ancestor-alias, container-valued identity, and incomplete released-overlay
findings now have RED-first regressions and a combined local GREEN result. The
exact atomic API surface, claim schema, compatibility boundary, and durable
W4a evidence rule are corrected without rewriting historical reviews in
`reviews/REVIEW-2026-08-02-task-ar-654-w4b-evidence-contract-correction.md`.
The unit remains failed and claimed until the implementation is committed, a
fresh registered Verify and append-only Compound are recorded, and a new exact
W4 sequence succeeds.

## Adverse-W4b Verify and Compound recorded

Implementation `94589d68` passed fresh registered Verify with full Runtime
`4295 passed, 11 skipped` and focused governance `1252 passed, 2 skipped`.
The fifth append-only Compound now covers the one previously uncovered
container-identity signature and records the two recurrent prevention failures.
All 41 declared signatures are covered by the five linked records. The exact
scope and immutable-overlap rationale are recorded in
`reviews/REVIEW-2026-08-02-task-ar-654-adverse-w4b-compound-scope-amendment.md`.
This does not change the failed/in-progress disposition or authorize release.

## Adverse-W4b repair W4a

Worker self-check on exact evidence candidate `6c9a7c0f`, tree `a5ed7e3a`,
found no current-scope P0/P1/P2 and issued
`PASS_PENDING_NATIVE_WINDOWS_CI_AND_FRESH_INDEPENDENT_W4B_AND_SKEPTIC` in
`reviews/W4A-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md`.
W4b acceptance remains false and the claim remains held pending a distinct
no-shared-context review of the post-W4a candidate.

## Adverse-W4b repair independent W4b

Distinct no-shared-context review of exact candidate `8ad05699`, tree
`e54ef473`, found no current-scope P0/P1/P2 and issued
`APPROVE_CURRENT_SCOPE_PENDING_NATIVE_WINDOWS_SCRIBE_ADJACENT_BLOCKERS_AND_SKEPTIC`
in
`reviews/W4B-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md`.
This sets bounded W4b acceptance true but does not authorize release. The task
remains in progress and the claim remains held pending a distinct skeptic,
native Windows evidence, Scribe closure work, and the registered adjacent
release blockers.

## Adverse-W4b repair final skeptic

Distinct skeptic review of exact post-W4b candidate `83b895ae`, tree
`0d407fbc`, issued
`APPROVE_CURRENT_SCOPE_ONLY_PENDING_NATIVE_WINDOWS_SCRIBE_AND_ADJACENT_BLOCKERS`
with no P0/P1/P2 findings in
`reviews/SKEPTIC-2026-08-02-task-ar-654-adverse-w4b-repair-final.md`.
The bounded W4 chain is complete. TASK-AR-654 remains in progress and its
claim remains held because native Windows execution, Scribe closure debt, and
TASK-AR-655/TASK-AR-657/TASK-AR-651 are still release blockers.
