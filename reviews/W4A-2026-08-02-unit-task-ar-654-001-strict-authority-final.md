---
title: TASK-AR-654 Strict Canonical Authority Final W4a
date: 2026-08-02
created_at: 2026-08-02T13:28:10+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
reviewer: le-20260801-000005-kst-ar654repair001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC
finding_counts: {P0: 0, P1: 0, P2: 0}
superseded_candidate: c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9
repair_replan_commit: 0ba8d85e
failure_first_commit: ea7b2b2e
compatibility_test_commit: 19f2c4a4
implementation_commit: 68943821
candidate_commit: 32bde1d9dffc49bffe1d34a6153359a9d35f2349
candidate_tree: b9d2ea448863e43cb56ddbd381185baeeb7ca680
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802132243.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json
triggering_w4b: reviews/W4B-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md
triggering_skeptic: reviews/SKEPTIC-2026-08-02-task-ar-654-canonical-authority-final.md
tags: [w4a, canonical-authority, claim-store, unit-spec, identity, fail-closed]
---

# TASK-AR-654 Strict Canonical Authority Final W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC — P0: 0, P1: 0, P2: 0.`

Implementation `68943821` repairs the four authority classes that superseded
the prior W4a, and evidence commit `32bde1d9` fixes fresh machine verification
and append-only prevention authority. This is worker self-check only. It does
not authorize claim release, integration, closeout, versioning, publication,
deployment, or external release.

## Exact review target

| Identity | Value |
| --- | --- |
| Superseded candidate | `c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9` |
| Strict-authority replan | `0ba8d85e` |
| Failure-first commit | `ea7b2b2e` |
| Compatibility follow-up | `19f2c4a4` |
| Implementation commit | `68943821` |
| Evidence candidate | `32bde1d9dffc49bffe1d34a6153359a9d35f2349` |
| Candidate tree | `b9d2ea448863e43cb56ddbd381185baeeb7ca680` |
| Active claim | `CLAIM-20260801-000156-task-ar-654-ar654repair001` |

Review the repair range `0ba8d85e..32bde1d9`. The exact tests-before-code
range is `ea7b2b2e^..68943821`; the later evidence commit changes lifecycle
records only.

## Failure-first contract

Before implementation, the selected actual-close matrix reported
`34 failed, 3 passed`. Every negative failed because `work close` returned
success and mutated the target instead of rejecting it. The three passing
controls preserved task-level claim compatibility.

After implementation, all `37` cases pass:

1. an active claim file symlink outside the direct claim store is rejected;
2. a symlinked active claim-store directory is rejected;
3. a canonical-looking duplicate work path outside the registered root path is
   rejected;
4. present unit-claim `unit_spec` values `null`, `false`, `0`, `[]`, `{}`, and
   blank string are rejected;
5. blank-string and empty-container values are rejected for every covered UNIT
   identity alias (`kind`, `work_id`, `id`, `display_id`, `task_id`, `unit_id`,
   `parent_id`) and TASK identity alias (`kind`, `work_id`, `id`, `display_id`,
   `task_id`);
6. a conflicting valid UNIT `unit_id` cannot change the resolver key, skip the
   active repeated-failure claim, or close via `wontfix`; and
7. legacy task-level claims remain accepted when `unit_id`/`unit_spec` are
   absent, blank, or whitespace-only in the permitted task-level form.

Every rejection asserts unit/task, claim, shadow authority object, and
generated-view non-mutation. The conflicting-ID regression also asserts that
the wrong identity is never reported as closed.

## Authority behavior

`_active_claims()` now validates the unresolved claim-store directory and each
`CLAIM-*.json` entry before reading authority. A store or entry must be a
direct non-symlink object whose strict resolved path equals its canonical
lexical path. Broken, redirected, parent-symlinked, or non-file objects produce
bounded integrity findings and no trusted claim context.

Unit claims require a present, non-empty string `unit_spec` exactly equal to
the repository-derived canonical unit path. Task-level claims retain the
historical omitted/blank compatibility lane, but a present non-string value
cannot enter that lane.

Canonical TASK/UNIT identity is derived from the work-item path. Every present
identity alias must be an exact string equal to that derived identity; omitted
optional aliases remain compatible. `work close` uses the path stem only after
strict metadata validation, requires the loaded object to equal the canonical
registered path, and passes the derived ID—not frontmatter—to active-claim
resolution.

Source and packaged templates remain byte-identical:

| Asset pair | SHA-256 |
| --- | --- |
| `closure_gate.py` | `6377ac3ab47274ba834f97280c1909601f28d9fc7cf0c6d1b81d4fe05c9c8bba` |
| `work.py` | `ab927f1cb45860cbc7b2521f2d26f05f81214543f5f044e47cb6232d0957dde7` |

## Append-only Compound and closure assessment

`COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c`
directly contains both work IDs and the four new signatures. Its SHA-256 is
`ea8a74e8f1312749a549afb6c63c1becdba752dd713be37b1c61c1c76a61572a`.
The three prior TASK-AR-654 Compound files are unchanged, and the canonical
store and generated index pass validation.

Explicit TASK and UNIT closure assessments both report
`repeat_failure.required=true`, `satisfied=true`, all fourteen accumulated
signatures, all three current corrective Compound refs, and no repeat-failure
finding. Their only closure block is the orthogonal pre-existing Scribe state:
`source-debt-overdue` plus incomplete active coverage. This task does not waive
or conceal that blocker.

## Verification

| Verification | Result |
| --- | --- |
| New actual-close matrix | `37 passed` |
| Closeout consumers plus lock tests | `957 passed` |
| Registered focused suite | `1151 passed` |
| Full Runtime suite | `3994 passed, 3 skipped, 4 known UI warnings` in `229.03s` |
| Fresh `work verify` | passed; `1151` tests plus three registered gates |
| Owner governance | pass |
| Runtime asset usage | pass; 39 assets, 0 block, 0 watch |
| Template mirror | pass; 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock | current |
| Compound store and evidence index | pass |
| Work schema | 0 findings; 19 unrelated legacy warnings |
| `git diff --check` | pass |

Fresh machine evidence is
`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802132243.json`, SHA-256
`c8f9725f6363c136d14c668ea8024e52435ecc46e52a4f9afd2e7664f3dcc1a5`.
The four warnings are the unchanged UI route-sweep invalid-escape deprecation
warnings.

## Independent review request

W4b must use a distinct agent instance and review the exact candidate tree.
It must repeat actual-close non-mutation checks for claim-file and claim-store
aliases, broken or parent-symlinked claim paths, all six invalid `unit_spec`
shapes, every identity alias, a conflicting valid `unit_id`, and a duplicate
canonical-looking work path. It must also prove normal direct unit claims,
legacy task-level claims, valid primary-relative worktrees, linked released
claims, source/template parity, host lock, Verify, and append-only Compound
authority.

The skeptic should combine identities and paths not named by the matrix,
including present null/boolean/numeric identity values, missing identity
aliases, a noncanonical CLI path whose metadata is otherwise valid, store
parent-component aliases, unrelated claims bound to other worktrees, and
task-level claim omission. Any P1 reopens the unit.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer-repository mutation, version bump,
tag, package publication, push, deployment, or external release action
occurred. The repair claim remains active until both fresh independent reviews
approve this exact candidate.
