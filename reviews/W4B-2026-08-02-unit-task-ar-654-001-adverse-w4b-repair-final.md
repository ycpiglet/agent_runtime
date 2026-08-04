---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final
title: TASK-AR-654 Adverse-W4b Repair Final Independent W4b
date: 2026-08-02
created_at: 2026-08-02T23:43:50+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4b
reviewer: codex-independent-task-ar-654-adverse-repair-final-w4b-20260802
reviewer_role: independent-auditor
status: conditional-pass
signal: pass
verdict: APPROVE_CURRENT_SCOPE_PENDING_NATIVE_WINDOWS_SCRIBE_ADJACENT_BLOCKERS_AND_SKEPTIC
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 8ad05699f43f45e88a09083e3196e4267ffc4600
candidate_tree: e54ef473772e32d8c0c4e9b1782631cb4e416bdc
implementation_commit: 94589d6839f84056ac9ce770c7c5fdb0124e33bd
implementation_tree: 5c80db780dd6625ee3cec3c1592ce2b4bde93784
implementation_range: b90f3e02..94589d6839f84056ac9ce770c7c5fdb0124e33bd
evidence_commit: 6c9a7c0f16fe597d067f0bdfd120500531e2bee3
w4a_commit: 8ad05699f43f45e88a09083e3196e4267ffc4600
w4a_ref: reviews/W4A-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802231400.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-232400-bind-ancestor-identity-and-release-provenance-at-e8e801007dc0.json
source_w4b: reviews/W4B-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
independence_status: independent
implementation_reviewed: true
w4b_acceptance: true
release_authorized: false
claim_disposition: remain_claimed_pending_skeptic_native_windows_scribe_and_adjacent_blockers
tags: [w4b, task-ar-654, independent-audit, atomic-publication, claim-identity, release-provenance, compound, conditional-pass]
---

# TASK-AR-654 adverse-W4b repair final independent W4b

## Independent verdict

`APPROVE_CURRENT_SCOPE_PENDING_NATIVE_WINDOWS_SCRIBE_ADJACENT_BLOCKERS_AND_SKEPTIC — P0: 0, P1: 0, P2: 0.`

Exact candidate `8ad05699f43f45e88a09083e3196e4267ffc4600`, tree
`e54ef473772e32d8c0c4e9b1782631cb4e416bdc`, passes this independent W4b for
the bounded adverse-W4b repair. The candidate was clean immediately before this
report was created. This approval is not a release decision: the claim remains
held, release is unauthorized, and native Windows, Scribe, adjacent task, and
skeptic gates remain open.

## Exact chain and scope

The reviewed chain is a three-commit, first-parent-linear range with no merge:

```text
b90f3e02  accepted adverse-W4b replan baseline
94589d68  implementation, regressions, managed lock, and contract correction
6c9a7c0f  registered Verify, append-only Compound, indexes, and evidence lifecycle
8ad05699  worker W4a and W4a lifecycle record
```

The implementation commit changes 20 paths. Its 15 non-lifecycle paths are all
inside the registered task/unit/claim target union; the other five are the
canonical task, unit, claim, claim handoff, and append-only claim log. Evidence
and W4a commits add only their named reviews/evidence, generated indexes, the
new Compound, and registered lifecycle updates. No source, regression, or host
lock changes occur after `94589d68`. `git diff --check b90f3e02..HEAD` passes.

## Atomic publication repair

The actual public surface audited is exactly:

- `write_text_atomic`
- `write_json_atomic`
- `publish_text_atomic`
- `publish_json_atomic`
- `publish_text_owned_atomic`
- `publish_json_owned_atomic`

On POSIX, `_posix_parent_fd()` begins at the filesystem root and walks every
lexical component to the direct parent with directory-relative no-follow
`stat`, `mkdir`, and `open`, validating directory type and file identity at each
step. The destination rename/link, sidecar cleanup, and parent fsync remain
bound to the verified direct-parent descriptor.

An independent source/template matrix exercised all six functions against an
already existing direct parent below a symlinked ancestor. All 12 calls refused
with `UnsafePathError`; no outside target was created, the outside sentinel was
unchanged, and no temporary sidecar remained. Source and consumer-template
copies have identical SHA-256
`976cfa522fdf559f269b25ad19f6bbca181d4d8466dc3b3c976675ba818032ca`.

The compatibility statement is bounded and truthful: supported Runtime callers
resolve their Runtime root before constructing authority paths, while a generic
caller that retains an aliased lexical prefix must canonicalize it before using
the primitive. The primitive intentionally rejects a retained alias instead of
silently treating it as an authority root. Native Windows junction/reparse
execution is not inferred from this POSIX result and remains pending.

## Shared claim-reader identity contract

All three claim-store readers are byte-identical with SHA-256
`851d624502da642d1be4ec550d9b229fbfff7ba3f1ab8ce50cfee3397f0a1ecb`.
Their shared `agent-runtime-task-claim/v1` admission rule requires active
`task_id`; rejects every present non-string, blank, padded, or over-160-character
`task_id`, `task_set_id`, and `agent_instance_id`; retains exact
`task_set_id: ""` as the legacy sentinel; permits omission of optional
`task_set_id` and `agent_instance_id`; and permits inactive legacy omission of
`task_id`.

A separate 15-case matrix across all three copies passed 45 assertions,
including the 160-character positive boundary and all stated compatibility
cases. The full regression run also exercised marker initialization and
activation, the locked canonical snapshot, actual `work.py status`, and actual
dispatcher `create`. Malformed containers/scalars are rejected before a W0
projection or second claim mutation; before/after snapshots remain identical.
The live candidate W0 view returns one canonical claimed row for TASK-AR-654.

## Released overlay provenance

An existing role overlay with `status: released` is accepted as idempotent only
when `released_at`, `verified_by`, `verifier_role`, and
`verification_evidence` are all strings with nonblank trimmed content. Removing
any one field fails closed without rewriting artifacts. A complete released
overlay remains byte-stable and idempotent, and a valid nonterminal overlay is
not required to carry release-only fields. The six focused lifecycle cases
passed. Source and template bytes are identical with SHA-256
`eea19ecd973b8828ff30b3530c49bea0115aeb60bd52c585def09064f67f9b9a`.

## Verify and W4a evidence attribution

The committed Verify has SHA-256
`0c9b4893b5c7a3bb593c84a7b4012c16f9b80598c73f4af9691afaf7f159e88d`.
Its declared and actual command counts are both five; every command records
`status: passed` and return code `0`:

| Command | Durable result |
| --- | --- |
| `python -m pytest -q` | `4295 passed, 11 skipped, 4 warnings` |
| focused governance command recorded in Verify | `1252 passed, 2 skipped` |
| `python scripts/runtime_asset_usage.py --check` | passed, return code `0` |
| `python scripts/template_mirror_gate.py --check` | `86` common, `83` identical, `3` intentional, findings `0` |
| `python scripts/regen_host_lock_if_needed.py --check` | managed lock current |

The timestamps bind the Verify after implementation `94589d68` and before
evidence commit `6c9a7c0f`. The W4a cites the committed Verify, Compound, adverse
W4b, accepted replan, contract correction, and Compound scope amendment. It
does not use the superseded W4a's unbound supplemental counts as approval
evidence and explicitly keeps W4b acceptance and release authorization false.

## Append-only Compound and coverage

The new Compound has SHA-256
`321fa612833cee76b1286992cdbea5b38a426ef26ff61fe34b6b7e9885612b27`,
schema `agent-runtime-compound-record/v1`, status `mitigated`, both work IDs,
three unique ordered signatures, three source refs, five prevention refs, and
one Verify ref. Every reference is a direct regular repository file, and all
five prevention files changed in the implementation commit.

Task, unit, and active claim have identical ordered arrays of 41 unique defect
signatures and five explicit Compound refs. Their sorted-newline signature hash
is `da6a60b5f42c6ca4fbe46a4fcdb4b30b8fca0fa29b1e89a7ff860fc4a40bad60`.
The five linked records contain 43 raw signature entries and a 41-signature
union: uncovered `0`, extraneous `0`.

The new record overlaps the prior linked union in exactly two signatures: the
ancestor-alias publication signature and the incomplete-overlay idempotency
signature. That overlap is justified recurrence: both were already claimed by
the earlier `19:59:51` record and were then independently reproduced by the
adverse W4b, showing the earlier prevention was insufficient. The
container-valued identity signature is the new record's one previously
uncovered member. All four prior Compound files have identical base/HEAD blob
IDs, so the repair is append-only rather than a historical rewrite.

## Independent execution

| Check | Result |
| --- | --- |
| Relevant five complete test files | `336 passed, 6 skipped` |
| Released/nonterminal overlay subset | `6 passed` |
| Atomic six-function source/template probe | `12/12` bounded refusals; outside/residue `0/0` |
| Three-reader identity probe | `45/45` assertions |
| Template mirror | pass; `86/83/3`, findings `0` |
| Host lock | current |
| Compound record and evidence index | pass; findings `0` |
| Work schema | findings `0`; 19 unrelated existing warnings |
| State sync | block `0`; one known `STATUS.md` watch |
| Parallel worktree | block `0`, watch `0` |
| State-machine schema | pass; findings `0` |
| Runtime asset usage | pass; block `0`, watch `0` |
| Compound cadence | pass; watch `0` |
| Changed Python `py_compile`, source/template parity, range diff-check | pass |

## Remaining gates and disposition

Task and unit closure both report `repeat_failure.required: true`,
`repeat_failure.satisfied: true`, 41 covered signatures, and an empty uncovered
list. Their only closure decision is `scribe-source-debt-overdue`, with missing
`scribe_source_debt` and `scribe_active_coverage`; this W4b does not authorize
the archive-aware Scribe mutation needed to clear it.

- Native Windows Python 3.10, 3.11, and 3.12 execution remains pending.
- A separate skeptic review is now the next current-scope review gate.
- TASK-AR-655 remains planned and owns negative lease/grace bounds.
- TASK-AR-657 remains planned and owns verifier-approval authenticity.
- TASK-AR-651 remains planned and owns the portable version/package cascade.
- TASK-AR-654 remains `in_progress`, the unit remains
  `verification_status: failed`, and the claim remains `claimed`.

Therefore `w4b_acceptance` is true only for this bounded repair. Claim release,
task closeout, merge/integration, consumer mutation, CI dispatch, push, tag,
versioning, packaging, publication, deployment, and external release remain
unauthorized.
