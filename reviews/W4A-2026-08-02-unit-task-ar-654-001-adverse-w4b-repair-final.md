---
schema_version: agent-runtime-review/v1
id: W4A-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final
title: TASK-AR-654 Adverse-W4b Repair Final W4a
date: 2026-08-02
created_at: 2026-08-02T23:31:00+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4a
reviewer: le-20260801-000005-kst-ar654repair001
reviewer_role: lead-engineer
status: conditional-pass
signal: pass
verdict: PASS_PENDING_NATIVE_WINDOWS_CI_AND_FRESH_INDEPENDENT_W4B_AND_SKEPTIC
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 6c9a7c0f16fe597d067f0bdfd120500531e2bee3
candidate_tree: a5ed7e3a5996ee25d66da00bf098e8a9bde6aa3f
implementation_commit: 94589d6839f84056ac9ce770c7c5fdb0124e33bd
implementation_tree: 5c80db780dd6625ee3cec3c1592ce2b4bde93784
implementation_range: b90f3e02..94589d6839f84056ac9ce770c7c5fdb0124e33bd
evidence_commit: 6c9a7c0f16fe597d067f0bdfd120500531e2bee3
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802231400.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-232400-bind-ancestor-identity-and-release-provenance-at-e8e801007dc0.json
source_w4b: reviews/W4B-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
replan_ref: reviews/REVIEW-2026-08-02-task-ar-654-ancestor-identity-provenance-t3-replan.md
correction_ref: reviews/REVIEW-2026-08-02-task-ar-654-w4b-evidence-contract-correction.md
compound_scope_ref: reviews/REVIEW-2026-08-02-task-ar-654-adverse-w4b-compound-scope-amendment.md
independence_status: worker_self_check_only
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_fresh_independent_w4b_and_skeptic
tags: [w4a, task-ar-654, atomic-publication, claim-identity, released-provenance, compound, conditional-pass]
---

# TASK-AR-654 adverse-W4b repair final W4a

## Verdict

`PASS_PENDING_NATIVE_WINDOWS_CI_AND_FRESH_INDEPENDENT_W4B_AND_SKEPTIC`.

Exact candidate `6c9a7c0f16fe597d067f0bdfd120500531e2bee3`, tree
`a5ed7e3a5996ee25d66da00bf098e8a9bde6aa3f`, contains the bounded repair for
all four findings in the adverse W4b and the fresh durable evidence that binds
the repairs to actual Runtime contracts. This worker self-check found no
current-scope P0, P1, or P2 finding.

This is W4a only. `w4b_acceptance` remains false, release is not authorized,
and the active claim remains held. A distinct reviewer with no shared working
context must inspect the exact candidate produced after this W4a is committed.
Only if that W4b has no P1 finding may a separate skeptic review run.

## Exact candidate and evidence chain

The committed chain under review is linear:

```text
b90f3e02  adverse W4b and accepted T3 replan
94589d68  implementation, regressions, managed lock, and contract correction
6c9a7c0f  registered Verify, append-only Compound, and evidence lifecycle
```

The worktree was clean before this report was created. Source and test changes
stop at implementation commit `94589d68`; evidence commit `6c9a7c0f` changes
only registered task/unit/claim lifecycle, generated indexes, the new Verify,
the new append-only Compound, and its scope review.

The fresh Verify artifact has SHA-256
`0c9b4893b5c7a3bb593c84a7b4012c16f9b80598c73f4af9691afaf7f159e88d`.
All five recorded commands have `status: passed` and return code `0`:

| Registered command | Durable result |
| --- | --- |
| `python -m pytest -q` | `4295 passed, 11 skipped, 4 warnings` |
| focused governance suite | `1252 passed, 2 skipped` |
| `runtime_asset_usage.py --check` | pass, block `0` |
| `template_mirror_gate.py --check` | `86` common, `83` identical, `3` intentional, findings `0` |
| `regen_host_lock_if_needed.py --check` | managed lock current |

No supplemental pass count is used as approval evidence. The superseded W4a's
unbound `1591`, `968`, and `363` statements are intentionally omitted from the
decision. RED history and compatibility details are cited only through the
committed T3 replan, evidence-contract correction, claim log, regressions, and
fresh registered Verify.

## Finding repair audit

### P1 — aliased ancestor above an existing direct parent

The repaired POSIX parent opener now starts at the filesystem root and walks
every lexical directory component with directory-relative, no-follow
`stat`/`open` operations and file-identity comparison. A symlinked ancestor can
no longer disappear behind an already existing direct parent.

`tests/test_atomic_io.py` covers all six functions that actually exist on the
public surface:

- `write_text_atomic`
- `write_json_atomic`
- `publish_text_atomic`
- `publish_json_atomic`
- `publish_text_owned_atomic`
- `publish_json_owned_atomic`

Every case requires bounded refusal, an unchanged or absent outside target,
and no temporary residue. Source and consumer-template copies are byte
identical. The final W4b's nonexistent bytes/YAML function names and incorrect
claim fixture schema label are preserved as history and corrected in the
committed evidence-contract review.

The bounded compatibility contract is explicit: POSIX callers must supply a
canonical path whose lexical ancestors are alias-free and openable as
directories. Supported Runtime roots and pytest temporary roots are
canonicalized before suffix construction. A generic `authority_root` API for
arbitrary aliased paths is not silently inferred by this repair.

### P1 — malformed core identity becomes active authority

All three byte-identical claim-store readers now apply one admission rule
before marker activation, canonical snapshot use, W0 projection, duplicate
checks, or dispatcher mutation:

- active `task_id` is required;
- any present core identity is a nonblank exact-trimmed string of at most 160
  characters;
- exact `task_set_id: ""` remains the dispatcher's legacy absent sentinel;
- optional `task_set_id` and `agent_instance_id` omissions remain compatible;
  and
- inactive legacy claims may omit `task_id`.

Marker, canonical-snapshot, actual W0/status, and actual dispatcher-create
regressions reject lists, mappings, booleans, numbers, nulls, blanks, padding,
and over-bound identities before a second authority or projection mutation can
occur.

### P2 — released overlay lacks terminal provenance

Role idempotency now applies a status-specific terminal rule. An existing
`released` overlay must contain nonblank `released_at`, `verified_by`,
`verifier_role`, and `verification_evidence`. Missing or blank terminal
provenance fails closed without rewriting the existing artifacts. Complete
released overlays remain byte-stable and idempotent; nonterminal overlays are
not incorrectly required to carry release-only fields. Source/template parity
is exact.

### P2 — W4a supplemental counts were not durable evidence

This W4a binds its decision only to named committed artifacts and commands.
The registered Verify contains the exact command list, timestamps, return
codes, stdout, verifier identity, and result. The separate contract correction
states the historical discrepancy without rewriting the prior W4a or adverse
W4b.

## Compound and closure truth

The new append-only Compound has SHA-256
`321fa612833cee76b1286992cdbea5b38a426ef26ff61fe34b6b7e9885612b27`.
It links both work IDs, the three repaired signatures, the exact five
regression files, and the fresh Verify. Its two recurrent signatures overlap an
earlier immutable record because the earlier prevention proved insufficient;
the new container-identity signature had no prior canonical match.

Task, unit, and active claim have ordered parity for 41 unique signatures and
five explicit Compound references. The linked-record union covers all 41 with
no uncovered or extraneous signature; the raw count is 43 because the two
recurrences are intentionally append-only. All four earlier Compound files
remain byte-identical to the implementation candidate.

Closure is still blocked, but only by the independently visible Scribe lane:
`scribe-source-debt-overdue`, with missing `scribe_source_debt` and
`scribe_active_coverage`. The repeat-failure section reports `required: true`,
`satisfied: true`, and an empty uncovered-signature list. This W4a neither
cleans `STATUS.md` nor treats a fresh projection as canonical cleanup.

## Remaining release blockers

- Native Windows Python 3.10, 3.11, and 3.12 execution remains pending; local
  POSIX results and modeled Windows tests do not replace it.
- A fresh independent W4b on the post-W4a exact candidate is mandatory.
- A separate skeptic review is mandatory only after W4b has no P1 finding.
- TASK-AR-655 still owns negative lease/grace bounds.
- TASK-AR-657 still owns verifier-approval authenticity.
- TASK-AR-651 still owns portable version cascade and package-gate evidence.
- Archive-aware Scribe source cleanup and active coverage remain separately
  authorized work.

No claim release, task closeout, integration, consumer pilot mutation, CI
dispatch, push, tag, version bump, package publication, deployment, or external
release is authorized by this W4a.
