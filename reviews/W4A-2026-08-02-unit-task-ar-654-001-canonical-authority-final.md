---
title: TASK-AR-654 Canonical Authority Final W4a
date: 2026-08-02
created_at: 2026-08-02T12:26:08+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
reviewer: le-20260801-000005-kst-ar654repair001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC
finding_counts: {P0: 0, P1: 0, P2: 0}
superseded_candidate: 1b0db7d8555e12e781d7ddfa0850037a875f05fd
repair_replan_commit: cd65cdc78d07efb49b074ac7a289b3bf5168a442
failure_first_commit: 512bb4f5548d65fac4eb186fafa7a8a160928a73
implementation_commit: c63c646100e220fb0d24acc291fc2f6f9a00b854
candidate_commit: 86fa7a27826d358a6b970b3443e6365ba06ad6a8
candidate_tree: 3f9bb9bbad54a888b58f2faf52ce48af4339688a
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802122023.json
triggering_audit: reviews/AUDIT-2026-08-02-task-ar-654-canonical-authority-probe.md
triggering_w4b: reviews/W4B-2026-08-02-unit-task-ar-654-001-deep-json-failopen-interruption.md
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json
tags: [w4a, canonical-authority, symlink, identity, deep-json, fail-closed, compound]
---

# TASK-AR-654 Canonical Authority Final W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC — P0: 0, P1: 0, P2: 0.`

Implementation `c63c646100e220fb0d24acc291fc2f6f9a00b854` closes all six
P1 boundaries that superseded the prior W4a. Evidence and the append-only
Compound are fixed in candidate
`86fa7a27826d358a6b970b3443e6365ba06ad6a8`. This is worker self-check only;
it does not authorize claim release or integration.

## Exact review target

| Identity | Value |
| --- | --- |
| Superseded candidate | `1b0db7d8555e12e781d7ddfa0850037a875f05fd` |
| Canonical-authority replan | `cd65cdc78d07efb49b074ac7a289b3bf5168a442` |
| Failure-first commit | `512bb4f5548d65fac4eb186fafa7a8a160928a73` |
| Implementation commit | `c63c646100e220fb0d24acc291fc2f6f9a00b854` |
| Evidence candidate | `86fa7a27826d358a6b970b3443e6365ba06ad6a8` |
| Candidate tree | `3f9bb9bbad54a888b58f2faf52ce48af4339688a` |
| Worker | `le-20260801-000005-kst-ar654repair001` |
| Active claim | `CLAIM-20260801-000156-task-ar-654-ar654repair001` |

Review the repair range `cd65cdc7..86fa7a27` and use the earlier range only
as append-only history. The exact implementation delta is
`512bb4f5^..c63c6461`.

## Failure-first contract

The ten selected contracts failed before implementation and pass afterward:

1. scalar released-claim authority is rejected without mutating unit, claim,
   or generated views;
2. a claim ref symlink outside the canonical claim store is rejected;
3. a unit-spec symlink alias is not accepted as canonical identity;
4. canonical unit path and contradictory task frontmatter cannot combine into
   trusted authority;
5. a missing primary-relative worktree cannot fall back to a linked-root
   shadow;
6. source and packaged accepted-watch helpers convert deeply nested JSON into
   one bounded domain finding;
7. direct closure assessment and the actual Stop hook do not surface a
   recursion traceback or silently approve it; and
8. any unexpected Stop gate exception emits an explicit bounded block while
   the documented disable bypass stays silent.

The test-only commit precedes the implementation in history. The selected
suite initially reported ten failures. On the implementation it reports
`10 passed`; the complete closure and Compound files report `890 passed`.

## Canonical authority behavior

Relative claim worktrees in linked checkouts now resolve only against the Git
primary checkout. Claim `unit_spec` must equal the repository-derived unit
path and must be a direct regular file without a symlinked component. Task and
unit identity is derived from the canonical work-item path; conflicting
`kind`, `work_id`, `id`, `display_id`, `task_id`, `unit_id`, or unit
`parent_id` fails closed.

Explicitly linked released claims must be direct files in
`agents/runtime/task_claims`, must retain filename/claim-ID identity, and must
use non-empty string lists for every authority field. Invalid authority never
reaches close mutation. Normal absolute claims and valid Git-primary relative
worktrees remain accepted; an independent read-only matrix reported
`25 passed` with no finding.

## Parser and Stop boundaries

The accepted-watch JSON byte limit is preserved and structural recursion is
now bounded by converting `RecursionError` to
`compound:prevention-watch-invalid-json-depth` in both helper copies. The
actual Stop wrapper emits `decision=block`, `reason=closure-gate-error` on an
unexpected exception and includes no exception detail. Explicit disable is
unchanged and produces no Stop payload.

Source and packaged assets remain byte-identical:

| Asset pair | SHA-256 |
| --- | --- |
| `closure_gate.py` | `bc3b347227b53049b6e1d0c8bc701e567d64a75829009f70d47fbb9773aaf2b7` |
| `work.py` | `7d2d837c8582795f1df5e7d8274719d025a081e02abea54309661f6b372845f4` |
| `stop_hook_closure_gate.py` | `5ad0ce6f3d0b7d8996891ca82df7abc675c547622834038e21afc98f96bd88b4` |
| Compound helper | `2e75f1b93c12b17f5e5995d64760318cb24a6ab3a83a9b9bde8a5eb9c12d344c` |

## Append-only Compound

`COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52`
contains both work IDs and exactly the six new stable signatures. It links the
independent probe, interrupted W4b, T3 replan, both failure-first test files,
and fresh Verify. Its SHA-256 is
`269b7dc7367b0078c7f86b054ae331e5a704ae2db6011eded33a8de592db02cb`.
Both older Compound records remain unchanged. `compound_record.py check`
passes and task/unit search returns the new record at score 100.

Explicit task and unit closure assessments report
`repeat_failure.required=true`, `satisfied=true`, all ten accumulated
signatures, both current valid Compound refs, and no repeat-failure finding.
Their only block is the orthogonal pre-existing
`scribe-source-debt-overdue` state. This task neither conceals nor waives that
debt.

## Verification

| Verification | Result |
| --- | --- |
| Selected six-boundary regression suite | `10 passed` |
| Closure + Compound files | `890 passed` |
| Claim dispatcher | `63 passed` |
| Registered focused suite | `1114 passed` in `60.33s` |
| Full Runtime suite on implementation candidate | `3957 passed, 3 skipped, 4 known UI warnings` in `229.15s` |
| Owner governance on evidence candidate | pass |
| Runtime asset usage | pass; 39 assets, 0 block, 0 watch |
| Template mirror | pass; 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock | pass; current |
| Work schema | 0 findings; 19 unrelated legacy warnings |
| Evidence and Compound indexes | pass |
| `git diff --check` | pass |

Fresh machine evidence is
`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802122023.json`, SHA-256
`db8501b24488ba9b1f7f65f68d2834c1dbe27637accb4f389e215a8c1b1c0203`.
The four warnings are the existing UI route-sweep invalid-escape deprecation
warnings; no test failed.

## Independent review request

W4b must use a different agent instance and independently inspect the exact
candidate, the W4a evidence, normal claim compatibility, canonical lexical and
resolved path binding, released-claim authority types, frontmatter identity,
deep JSON behavior, actual Stop output, failed-close non-mutation, mirror
parity, host lock, and append-only Compound linkage.

The skeptic must seek combinations not named by the existing tests, especially
symlinked parent components, alternate lexical spellings, mutually conflicting
identity aliases, JSON just below the byte ceiling with extreme structure,
and unexpected gate errors. Any P1 reopens the unit.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer-repository write, version bump,
tag, package publication, push, deployment, or external release action
occurred. The repair claim remains active until distinct W4b and skeptic
approvals exist.
