---
schema_version: agent-runtime-review/v1
id: SKEPTIC-2026-08-02-task-ar-654-adverse-w4b-repair-final
title: TASK-AR-654 Adverse-W4b Repair Final Skeptic Review
date: 2026-08-02
created_at: 2026-08-02T23:59:00+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: skeptic
reviewer: codex-skeptic-task-ar-654-adverse-repair-final-20260802
reviewer_role: skeptic
status: conditional-pass
signal: pass
verdict: APPROVE_CURRENT_SCOPE_ONLY_PENDING_NATIVE_WINDOWS_SCRIBE_AND_ADJACENT_BLOCKERS
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 83b895aeb8df9daaae707fa0892a5191ba552125
candidate_tree: 0d407fbcab08494abb7ea6f428d0f86ca4c53eef
implementation_commit: 94589d6839f84056ac9ce770c7c5fdb0124e33bd
implementation_tree: 5c80db780dd6625ee3cec3c1592ce2b4bde93784
implementation_range: b90f3e02..94589d6839f84056ac9ce770c7c5fdb0124e33bd
w4a_ref: reviews/W4A-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md
w4b_ref: reviews/W4B-2026-08-02-unit-task-ar-654-001-adverse-w4b-repair-final.md
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802231400.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-232400-bind-ancestor-identity-and-release-provenance-at-e8e801007dc0.json
independence_status: independent_repository_evidence_only
implementation_reviewed: true
w4b_acceptance: true
release_authorized: false
claim_disposition: remain_claimed
tags: [task-ar-654, skeptic, adverse-w4b-repair, atomic-publication, claim-identity, release-provenance, compound, current-scope-only]
---

# TASK-AR-654 adverse-W4b repair final skeptic review

## Verdict

`APPROVE_CURRENT_SCOPE_ONLY_PENDING_NATIVE_WINDOWS_SCRIBE_AND_ADJACENT_BLOCKERS — P0: 0, P1: 0, P2: 0.`

Exact candidate `83b895aeb8df9daaae707fa0892a5191ba552125`, tree
`0d407fbcab08494abb7ea6f428d0f86ca4c53eef`, is acceptable only for the
bounded adverse-W4b repair. The root-to-leaf POSIX atomic-parent repair,
canonical claim core-identity admission, released-overlay terminal provenance,
fresh Verify attribution, and append-only Compound coverage withstand this
skeptic replay.

This is not release approval. TASK-AR-654 remains `in_progress`, the unit
remains `verification_status: failed`, and claim
`CLAIM-20260801-000156-task-ar-654-ar654repair001` remains `claimed`.
`release_authorized` is false and `claim_disposition` is `remain_claimed`.

## Independence and exact chain

Reviewer `codex-skeptic-task-ar-654-adverse-repair-final-20260802` is distinct
from worker/Verify identity `le-20260801-000005-kst-ar654repair001` and prior
W4b reviewer
`codex-independent-task-ar-654-adverse-repair-final-w4b-20260802`. This review
used repository evidence and fresh temporary fixtures, without worker
conversation context or inherited implementation conclusions. No live
provider, network, CI dispatch, consumer mutation, or release action was used.

The first-parent chain is linear:

```text
b90f3e02  adverse W4b and accepted bounded replan baseline
94589d68  implementation, regressions, mirror changes, and contract correction
6c9a7c0f  registered Verify, append-only Compound, indexes, and lifecycle evidence
8ad05699  worker W4a and lifecycle record
83b895ae  independent W4b and lifecycle record
```

Source and regression changes stop at `94589d68`. Later commits contain the
named evidence and lifecycle records. `git diff --check b90f3e02..HEAD` passes.
The candidate was clean before this report was created.

## Adverse repair replay

### POSIX atomic parent authority

AST inspection confirms the actual public atomic function surface is exactly
the following six functions in both source and consumer template:

- `write_text_atomic`
- `write_json_atomic`
- `publish_text_atomic`
- `publish_json_atomic`
- `publish_text_owned_atomic`
- `publish_json_owned_atomic`

The POSIX parent opener begins at the filesystem root and walks every lexical
component with directory-relative no-follow metadata/open operations, directory
type checks, and opened-object identity comparison. A fresh source/template
matrix put an already existing direct parent below a symlinked ancestor and
called all six functions in each copy. All `12/12` calls raised
`UnsafePathError`; the outside sentinel was unchanged, no outside destination
was created, and no temporary sidecar survived.

The compatibility statement is bounded rather than universal: POSIX lexical
ancestors must be alias-free and openable as directories. Runtime authority
callers construct paths below resolved roots. A generic caller retaining a
symlinked prefix, including a platform alias such as macOS `/var`, must
canonicalize before calling. Native Windows junction/reparse execution is not
inferred from the POSIX result.

Source and template `atomic_io.py` are byte-identical at SHA-256
`976cfa522fdf559f269b25ad19f6bbca181d4d8466dc3b3c976675ba818032ca`.

### Canonical claim core identities

All three claim-store reader copies are byte-identical at SHA-256
`851d624502da642d1be4ec550d9b229fbfff7ba3f1ab8ce50cfee3397f0a1ecb`.
The audited schema is the actual `agent-runtime-task-claim/v1`, not the
historical W4b's corrected illustrative label.

A fresh `3 readers x 15 cases` matrix passed `45/45` assertions. It rejected
active missing `task_id` and present list, mapping, boolean, null, blank,
padded, or over-160-character core identities. It preserved the declared
compatibility cases: omitted optional `task_set_id`/`agent_instance_id`, exact
empty `task_set_id` as the legacy sentinel, the 160-character boundary, and
inactive legacy omission of `task_id`.

Actual mutation-boundary fixtures also passed:

- `work.py status --json` over a marker-activated malformed active claim
  returned `1` with `active-claim-context-invalid`; every fixture byte and
  marker remained unchanged.
- actual `task_claim_dispatcher.py create` in a temporary linked Git worktree
  returned `1` with `claim-store create refused` and `task_id`; HEAD and every
  fixture byte remained unchanged, and no third claim was created.
- live candidate `work.py status --json` returned `status: ok` with exactly one
  active TASK-AR-654 row and left candidate HEAD, tree, and status unchanged.

### Released-overlay terminal provenance

Existing overlays with status `released` now require nonblank string values
for `released_at`, `verified_by`, `verifier_role`, and
`verification_evidence`. A fresh seven-case replay refused each missing field
and a blank verifier, with no artifact/marker/event mutation. A complete
released overlay and a valid nonterminal overlay were byte-stable idempotent
matches. Source and template `role_routing.py` are byte-identical at SHA-256
`eea19ecd973b8828ff30b3530c49bea0115aeb60bd52c585def09064f67f9b9a`.

## Verify, W4, Compound, and lifecycle truth

The committed Verify SHA-256 is
`0c9b4893b5c7a3bb593c84a7b4012c16f9b80598c73f4af9691afaf7f159e88d`.
It is attributed to the worker identity, starts after implementation commit
`94589d68`, declares exactly five commands, and records five passed return-code
zero results:

| Registered command | Recorded result |
| --- | --- |
| `python -m pytest -q` | `4295 passed, 11 skipped, 4 warnings` |
| registered focused governance suite | `1252 passed, 2 skipped` |
| `python scripts/runtime_asset_usage.py --check` | pass |
| `python scripts/template_mirror_gate.py --check` | `86` common, `83` identical, `3` intentional, findings `0` |
| `python scripts/regen_host_lock_if_needed.py --check` | managed lock current |

The repaired W4a cites this durable evidence instead of promoting the prior
unbound `1591`, `968`, or `363` statements. Its reviewer equals the claim
worker, `w4b_acceptance` is false, and `release_authorized` is false. The fresh
W4b reviewer identity differs, reviews exact candidate `8ad05699`, tree
`e54ef473`, sets bounded `w4b_acceptance` true, and still records
`release_authorized: false` and a remain-claimed disposition. TASK-AR-657's
stronger verifier-authenticity question remains a separate blocker; this
review does not claim to solve it.

Task, unit, and active claim contain the same ordered 41 unique defect
signatures and the same ordered five Compound refs. The five records contain
43 raw signature entries and a 41-signature union: uncovered `0`, extraneous
`0`. The new record overlaps the prior union in exactly the two documented
recurrences; the new container-identity signature was not in the earlier
union. Its signature-set SHA-256 is
`da6a60b5f42c6ca4fbe46a4fcdb4b30b8fca0fa29b1e89a7ff860fc4a40bad60`.
All four earlier linked Compound blobs are identical at baseline `b90f3e02`
and HEAD, so the repair is append-only.

Both task and unit closure commands intentionally return `decision: block`,
`reason: scribe-source-debt-overdue`, with missing `scribe_source_debt` and
`scribe_active_coverage`. In both reports, repeated-failure authority is
separately `required: true`, `satisfied: true`, with 41 covered signatures and
an empty uncovered list. This is truthful blocked lifecycle state, not an
implicit closeout.

## Independent command evidence

| Check | Result |
| --- | --- |
| `pytest` complete `test_atomic_io.py`, `test_claim_store.py`, `test_task_claim_dispatcher.py`, `test_role_routing.py`, `test_lifecycle_defaults.py` | `336 passed, 6 skipped` |
| Six-function atomic source/template temporary probe | `12/12` bounded refusals; outside/residue failures `0` |
| Three-reader identity temporary probe | `45/45` assertions |
| Actual malformed W0 and dispatcher temporary probes | both refused; byte/HEAD mutations `0` |
| Released/nonterminal overlay temporary probe | `7/7`; invalid refused and valid idempotent, mutation `0` |
| `python scripts/template_mirror_gate.py --check` | pass; `86/83/3`, findings `0` |
| `python scripts/regen_host_lock_if_needed.py --check` | current |
| `python scripts/compound_record.py --root . check` | pass |
| `python scripts/evidence_index_generator.py --check` | pass, findings `0`, before creation of this permitted untracked report |
| `python scripts/work_schema_gate.py --items --check` | findings `0`; 19 unrelated existing warnings |
| `python scripts/state_sync_gate.py --check` | block `0`; one known `STATUS.md` watch |
| `python scripts/parallel_worktree_gate.py --check` | block `0`, watch `0` |
| `python scripts/state_machine_gate.py` | findings `0` |
| `python scripts/runtime_asset_usage.py --check` | 39 assets, block `0`, watch `0` |
| `python scripts/compound_cadence_gate.py --check` | pass, watch `0` |
| `python scripts/owner_governance_gate.py` | pass |
| `python scripts/attribution_gate.py --check` | block `0`; 836 historical watches |
| task/unit `closure_gate.py --check --json` | expected block only at Scribe source debt/active coverage; Compound coverage satisfied |
| changed Python `py_compile` to a temporary cache | 7 files passed |
| source/template `cmp`, public-API AST parity, prior-Compound blob parity, range diff check | pass |

Pytest used `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`. All
behavioral fixture state lived in temporary directories outside the candidate
worktree.

## Remaining blockers and disposition

The maximum verdict is current-scope-only. Every following blocker remains
explicit and unsatisfied:

- native Windows Python 3.10, 3.11, and 3.12 execution;
- archive-aware Scribe source-debt cleanup and active coverage;
- TASK-AR-655 negative lease/grace bounds;
- TASK-AR-657 verifier-approval authenticity; and
- TASK-AR-651 portable version and package cascade.

Therefore the current repair may retain bounded W4b acceptance, but the claim
must remain claimed. This skeptic review does not authorize claim release,
task/unit closeout, merge or integration, consumer mutation, CI dispatch,
push, tag, versioning, packaging, publication, deployment, or external
release.
