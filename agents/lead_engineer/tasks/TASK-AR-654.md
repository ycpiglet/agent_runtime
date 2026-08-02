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
updated_at: 2026-08-02T13:57:25+09:00
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
  - reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md
  - reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
  - reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
compound_refs:
  - agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json
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
  - The Compound prevention record links to a regression, gate, task proposal, or accepted watch state.
  - Generic substantial work may still close with an appropriate linked review or retro.
  - failure-to-regression is included in the consumer core profile and asset registry.
verification:
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
- The Compound prevention record links to a regression, gate, task proposal, or accepted watch state.
- Generic substantial work may still close with an appropriate linked review or retro.
- failure-to-regression is included in the consumer core profile and asset registry.

## Verification

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
