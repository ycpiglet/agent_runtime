---
title: TASK-AR-654 Fail-Closed Authority Repair W4a
date: 2026-08-01
created_at: 2026-08-01T02:00:11+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
reviewer: le-20260801-000005-kst-ar654repair001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
repair_replan_commit: 017275b2
failure_first_commits: [a4a77727, 04a44fba, 60b1bca2, 52afb845]
implementation_commits: [52510a48, 1b0db7d8]
candidate_commit: 1b0db7d8555e12e781d7ddfa0850037a875f05fd
candidate_tree: 228fca3efa840c96898d3022bdb03829ff41dae1
verification_evidence: reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801015750.json
triggering_w4b: reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
triggering_skeptic: reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json
tags: [w4a, compound, accepted-watch, utf8, bounded-read, claim-authority, closeout]
---

# TASK-AR-654 Fail-Closed Authority Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC — P0: 0, P1: 0, P2: 0.`

Candidate `1b0db7d8555e12e781d7ddfa0850037a875f05fd` repairs the
fail-open paths identified by the superseding W4b and skeptic reviews. It
strictly bounds and decodes accepted-watch authority, resolves one exact
active claim from the primary checkout, persists explicitly linked released
claim authority before every terminal resolution, and requires a current-work
canonical Compound whenever the merged authority declares repeated failure.

This is worker self-verification, not release approval. The claim remains held
until a distinct W4b auditor and a fresh skeptic both approve the exact
candidate and evidence package.

## Exact review target

| Identity | Value |
| --- | --- |
| Original integration base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| Fail-closed replan | `017275b2` |
| RED commits | `a4a77727`, `04a44fba`, `60b1bca2`, `52afb845` |
| Implementation commits | `52510a48`, `1b0db7d8` |
| Candidate commit | `1b0db7d8555e12e781d7ddfa0850037a875f05fd` |
| Candidate tree | `228fca3efa840c96898d3022bdb03829ff41dae1` |
| Worker | `le-20260801-000005-kst-ar654repair001` |
| Active claim | `CLAIM-20260801-000156-task-ar-654-ar654repair001` |

Review both the focused repair range `017275b2..1b0db7d8` and the complete
unit range `e6c8fb4b..1b0db7d8`. Lifecycle history before `017275b2` is
append-only evidence of earlier revisions and approvals; it is not a reason to
skip fresh review of the final candidate.

## Failure-first contract

The four RED commits preceded the principal implementation and cover these
authority boundaries:

1. malformed UTF-8 Markdown and JSON through the source helper, packaged
   helper, direct closure assessment, `work close`, and actual Stop wrapper;
2. accepted-watch files at the byte ceiling, one byte over it, and large
   malformed inputs without unbounded raw reads;
3. exact active-claim task, unit, unit-spec, worktree, schema, claim-ID, overlay,
   and authority-field shape matching, including malformed claim JSON;
4. explicitly linked released claims only, with path containment, schema/ID,
   task/unit identity, multiple-claim union, and persistence across closeout;
5. `done`, `wontfix`, `duplicate`, `superseded`, and `moved_to_vault` all
   retaining the same repeated-failure Compound obligation; and
6. mutation safety: a failed close leaves the work item, claim, and generated
   views unchanged.

Final live validation exposed one additional real-repository case missing from
the synthetic fixtures: a task's `parent_id` is a `TASKSET-*`, not its task
identity. Before the final repair, explicit `TASK-AR-654` assessment produced
`active-claim-context-invalid` because `_canonical_identity()` selected the
taskset parent. The new RED
`test_explicit_task_context_uses_task_work_id_when_parent_is_taskset` failed on
`52510a48` and passes on `1b0db7d8`. Task work ID now precedes taskset parent,
while unit identity continues to require its canonical task and unit-spec
path.

## Accepted-watch fail-closed behavior

`knowledge_records.py` and the packaged `compound_record.py` read no more than
`256 KiB + 1 byte`. Oversized input is rejected before parsing. Accepted bytes
are decoded with strict UTF-8; decoding errors become bounded Compound
findings rather than exceptions or best-effort approval. Physical LF/CRLF
handling and all earlier duplicate-key, YAML semantic-key, scalar,
indentation, and ownership protections remain intact.

The source and packaged helpers are byte-identical at SHA-256
`b9770c129889e11638e9b90cefa8dc37c45c3a096702b65655a0bed2e3e49b9a`.

## Active and released claim authority

`closure_gate.py` now creates one immutable resolution snapshot. A selected
active claim must be a non-overlay `agent-runtime-task-claim/v1` record whose
filename equals its claim ID and whose authority fields are lists of non-empty
strings. Relative worktree paths are anchored to the primary checkout before
the current worktree fallback, so a shadow directory cannot win resolution.
Explicit work requires exact task/unit/unit-spec agreement; inferred Stop
requires one deterministic current-worktree claim. Malformed or ambiguous
authority blocks without leaking signals from a different claim.

Only `escalation_triggers`, `defect_signatures`, and `compound_refs` are merged
from claim authority. `work.py` reuses the same resolver before mutation.
Released authority is loaded only from explicit `claim_refs`, is contained
under `agents/runtime/task_claims`, must pass schema/ID/path/identity checks,
and is persisted into canonical work frontmatter. Multiple valid linked
released claims contribute a deterministic union; unrelated released claims
are ignored.

Source/template parity is exact:

| Asset | SHA-256 |
| --- | --- |
| `closure_gate.py` pair | `501f7e3fab8c26d1eaba794354c788a025018e4079e5852327c926fb7dbf139f` |
| `work.py` pair | `ebfc74f9b94df7e8a5e4602ec599d73d7826b2ad77a83e0c19b7ff64380ff573` |
| Compound helper pair | `b9770c129889e11638e9b90cefa8dc37c45c3a096702b65655a0bed2e3e49b9a` |

## Compound prevention and append-only evidence

The corrective record
`COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711`
contains both `TASK-AR-654` and `UNIT-TASK-AR-654-001`, all four stable defect
signatures, three durable regression destinations, and the superseding reviews
that triggered the repair. Its SHA-256 is
`1da4db66377f6e330521f35017526439a5d92eb34b9894b8bc08fa36817f5f81`.

The record was atomically created after the first repaired candidate's fresh
Verify (`1104 passed`). It was not edited when the live taskset-parent RED was
added. The final work Verify (`1105 passed`) revalidates the same prevention
files on `1b0db7d8`; this preserves the append-only contract while providing
fresh final-candidate evidence. The earlier physical-line record remains
byte-for-byte untouched. `compound_record.py check` reports pass and the
generated index is current.

## Actual closure-path validation

Both explicit task and unit resolution select only
`CLAIM-20260801-000156-task-ar-654-ar654repair001` with `reason: null`. Both
report `repeat_failure.required=true`, `satisfied=true`, the four stable
signatures, and the corrective Compound as a valid current-work reference.

A non-mutating invocation of the actual `work.py` close validators returned:

```text
authority_findings=[]
done_findings=[]
non_done_findings=[]
```

The actual Stop wrapper returned `block: scribe-source-debt-overdue`. That is
the intended orthogonal Scribe gate: the repeated-failure/Compound lane is
satisfied, while existing `STATUS.md` source debt and active-coverage debt are
not concealed or waived by this task. TASK-AR-654 does not modify that source
or claim completion until the separately authorized Scribe work is complete.

## Verification

| Verification | Result |
| --- | --- |
| New task/taskset RED on pre-fix code | failed with `active-claim-context-invalid` |
| New task/taskset RED after repair | `1 passed` |
| Complete closure + claim dispatcher files | `482 passed` |
| Registered focused suite on final candidate | `1105 passed` in `57.90s` |
| Full Runtime suite on exact candidate | `3948 passed, 3 skipped, 4 known UI warnings` in `218.43s` |
| Runtime asset usage | pass; 39 assets, usage 748, 0 block, 0 watch |
| Template mirror | pass; 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock | pass; current |
| Evidence index | pass; 0 findings |
| Canonical Compound store/index | pass |
| Task and unit claim resolution | pass; one exact repair claim, no findings |
| `git diff --check` | pass |

Fresh machine evidence is
`reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801015750.json`, SHA-256
`f0ccef368703d51eaae1a775128ab81db4a6d508343e581abddd6fb57fc3395c`.
The four warnings are the pre-existing UI route-sweep invalid-escape
deprecation warnings; no test failed.

## Independent review requests

W4b must independently inspect and replay:

- malformed and oversized Markdown/JSON across helper, Stop, and work-close
  consumers;
- exact active-claim selection, primary-root relative worktree anchoring,
  overlay exclusion, schema/ID/authority shape, taskset-parent identity, and
  ambiguity fail-closed behavior;
- explicit released-claim linkage, multiple-claim union, path containment,
  identity validation, persistence, and failed-close mutation safety;
- every terminal resolution's repeated-failure Compound obligation;
- append-only Compound preservation, record/index validation, mirror parity,
  and host lock freshness.

The skeptic should attempt new boundary combinations rather than merely rerun
named tests, with special attention to identity fields that are individually
valid but mutually inconsistent, symlink/path shadows, competing active
claims, authority-field type confusion, and byte-limit/UTF-8 interactions.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer-repository write, version bump,
tag, package publication, push, deployment, or release action occurred. The
repair claim remains active. Only fresh W4b and skeptic approvals may authorize
local claim release and integration; external release still requires explicit
owner approval.
