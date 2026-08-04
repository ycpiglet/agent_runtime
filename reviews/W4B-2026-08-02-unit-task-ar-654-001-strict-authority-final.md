---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-02-unit-task-ar-654-001-strict-authority-final
title: TASK-AR-654 Strict Authority Final Independent W4b
date: 2026-08-02
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: w4b
reviewer: codex-independent-task-ar-654-strict-authority-final-w4b
reviewer_role: independent-auditor
status: blocked
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: de01e01d1b8f966bb4414dd18c44bd45966f12d0
candidate_tree: 0d5581db71be18bde997f5aa5f11c8b622a4619f
implementation_range: 0ba8d85e..de01e01d
independence_status: independent
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_repair_and_fresh_review
w4a_ref: reviews/W4A-2026-08-02-unit-task-ar-654-001-strict-authority-final.md
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802132243.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json
tags: [w4b, strict-authority, claim-store, parent-alias, fail-closed, data-integrity, revise]
---

# TASK-AR-654 Strict Authority Final Independent W4b

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

Independent reviewer
`codex-independent-task-ar-654-strict-authority-final-w4b` reviewed exact
candidate `de01e01d1b8f966bb4414dd18c44bd45966f12d0`, tree
`0d5581db71be18bde997f5aa5f11c8b622a4619f`. The candidate retains one
fail-open active-claim-store path and is not releasable.

This is a bounded software-quality and data-integrity consistency review, not
a security assessment. All behavioral fixture state was created under
temporary directories. No product, task, unit, claim, generated view, index,
Compound, commit, merge, release, or external state was changed by this
reviewer. This report is the reviewer's only repository write.

## P1-1 — Broken parent alias makes the active claim store disappear

`scripts/closure_gate.py::_active_claims()` tests
`agents/runtime/task_claims.exists()` before validating its parent components.
When `agents/runtime` is a broken directory symlink, the descendant
`task_claims` path does not exist and is not itself a symlink. The function
therefore returns an empty claim set without the bounded
`active-claim-store-integrity-invalid` finding.

An independent actual-close fixture contained a canonical closeable unit and
an active unit claim carrying the only repeated-failure authority. The
populated `agents/runtime` directory was moved aside, then its canonical path
was replaced with a broken directory symlink. The exact command was:

```text
python -m pytest -q /tmp/task-ar-654-w4b-VQO25K/test_strict_authority_probe.py::test_broken_active_claim_store_parent_must_fail_before_mutation
```

Result: `1 failed in 0.18s`. The underlying `work close` returned `0`, printed
`work-close: closed`, emitted no stderr, and reported the canonical UNIT as
closed. It mutated the unit plus `BACKLOG-BOARD.md`, both work-item
classification projections, and `reviews/INDEX.md`; the hidden shadow claim
remained unchanged. The expected result was a bounded active-claim-context
error before every task/unit/claim/generated-view mutation.

The direct store symlink, direct claim-file symlink, valid parent symlink, and
broken final `task_claims` symlink cases do fail closed. They do not cover this
broken parent-component branch because `Path.exists()` follows the broken
ancestor before the code inspects only the final path with `is_symlink()`.

Required repair is to validate every canonical claim-store path component,
including non-existent descendants of broken symlink parents, before treating
the store as absent. Add an actual-close non-mutation regression for this exact
parent-component shape. No repair was attempted in W4b.

## Checks completed before the P1 was found

| Command/check | Result |
| --- | --- |
| `git rev-parse HEAD` | `de01e01d1b8f966bb4414dd18c44bd45966f12d0` |
| `git rev-parse HEAD^{tree}` | `0d5581db71be18bde997f5aa5f11c8b622a4619f` |
| Review W4a, prior adverse W4b/skeptic, T3 replan, implementation range, fresh Verify, and new Compound | completed |
| Maintained actual-close strict-authority matrix | `37 passed in 3.96s` |
| Independent exact TASK/UNIT identity values (`null`, `false`, `0`, `[]`, `{}`, blank), valid parent alias, broken entry, and broken final store fixtures | `75 passed in 5.90s` |
| Valid direct active claim, linked released claim, legacy task-level claims, and primary-relative linked-worktree controls | `6 passed in 0.75s` |
| Full relevant closeout consumers: `test_compound_records.py`, `test_closure_gate.py`, `test_task_claim_dispatcher.py`, `test_regen_host_lock_if_needed.py` | `994 passed in 65.42s` |
| Registered focused suite from the unit spec | `1151 passed in 67.51s` |
| Source/template `closure_gate.py` parity | byte-identical, SHA-256 `6377ac3ab47274ba834f97280c1909601f28d9fc7cf0c6d1b81d4fe05c9c8bba` |
| Source/template `work.py` parity | byte-identical, SHA-256 `ab927f1cb45860cbc7b2521f2d26f05f81214543f5f044e47cb6232d0957dde7` |
| `python scripts/template_mirror_gate.py --check` | pass: expected/common 84, identical 81, intentional 3, findings 0 |
| `python scripts/regen_host_lock_if_needed.py --check` | pass; host lock current |
| `python scripts/runtime_asset_usage.py --check` | pass |
| `python scripts/compound_record.py --root . check` | `compound-record: pass` |
| Prior three TASK-AR-654 Compound records versus `0ba8d85e^..HEAD` | byte-unchanged (`git diff --exit-code` passed) |
| New Compound SHA-256 | `ea8a74e8f1312749a549afb6c63c1becdba752dd713be37b1c61c1c76a61572a`; directly links TASK, UNIT, four signatures, and fresh Verify |
| Fresh Verify SHA-256 and content | `c8f9725f6363c136d14c668ea8024e52435ecc46e52a4f9afd2e7664f3dcc1a5`; passed status/signal and four registered commands |
| `git diff --check` | pass |

These positive results establish the requested covered paths: direct active
claim store/entry consistency, all six falsey unit-claim `unit_spec` values,
exact present TASK/UNIT identities, conflicting valid `unit_id`, duplicate
canonical-looking work paths, pre-mutation rejection for the maintained
matrix, valid direct/released/primary-relative compatibility, source/template
parity, host lock, Compound append-only linkage, and focused/full consumer
tests. They do not neutralize the actual-close mutation demonstrated by P1-1.

Per the stop-on-P1 instruction, no further adversarial combinations were run
after reproducing P1-1.

## Release decision

**Do not release, merge, or close TASK-AR-654 on this candidate.** Keep the
claim held. Candidate `de01e01d1b8f966bb4414dd18c44bd45966f12d0` is rejected
at W4b and does not authorize claim release, integration, versioning,
publication, deployment, or external release. A repaired exact candidate
requires fresh Verify, W4a, independent W4b, and skeptic approval.
