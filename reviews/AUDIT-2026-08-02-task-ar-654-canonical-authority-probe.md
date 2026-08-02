---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-canonical-authority-probe
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
review_kind: independent-probe
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 5, P2: 0}
created_at: 2026-08-02T11:14:53+09:00
reviewer: task_ar_654_claim_context_impl
recorded_by: codex-root-task-ar-654-orchestrator
candidate_commit: 1b0db7d8555e12e781d7ddfa0850037a875f05fd
tags: [task-ar-654, independent-probe, claim-authority, canonical-path, symlink, identity]
---

# TASK-AR-654 canonical authority independent probe

## Verdict

`REVISE — P0: 0, P1: 5, P2: 0.`

The independent probe extracted exact candidate
`1b0db7d8555e12e781d7ddfa0850037a875f05fd` with `git archive` into a
temporary directory. All added probes ran only in that temporary copy; the
candidate worktree remained unchanged. The orchestrator persisted this report
from the reviewer's completed findings because the reviewer was instructed not
to write repository files.

## P1 findings

### 1. Released-claim authority accepts scalar fields

Active claims validate that `escalation_triggers`, `defect_signatures`, and
`compound_refs` are lists of non-empty strings. Explicitly linked released
claims do not apply the same shape contract. A released claim with all three
fields represented as scalars closed successfully and persisted the coerced
authority into the unit.

Observed: `SCALAR_RELEASED 0 persisted=True`.

Stable signature:
`defect:released-claim-scalar-authority-shape-accepted:12a9795c8b117218`.

### 2. Claim-ref symlink escapes the canonical claim store

The lexical reference is required to look like
`agents/runtime/task_claims/CLAIM-*.json`, but after symlink resolution the
code checks only repository containment. A lexical claim path symlinked to
`shadow/CLAIM-*.json` inside the repository was accepted and its authority was
persisted.

Observed:
`CLAIM_SYMLINK 0 target=shadow/CLAIM-released-symlink.json persisted=True`.

Stable signature:
`defect:claim-ref-symlink-escapes-canonical-claim-store:09782265a699dc29`.

### 3. Unit-spec symlink alias passes exact identity

Claim `unit_spec` validation compares resolved targets rather than requiring
the one canonical repository-relative unit path. A differently named symlink
to the canonical unit therefore passed exact claim identity and allowed
authority persistence.

Observed: `UNIT_SPEC_SYMLINK 0 persisted=True`.

Stable signature:
`defect:unit-spec-symlink-alias-accepted-as-canonical-id:8f8644f6caac78e7`.

### 4. Missing primary-relative worktree falls back to a linked-root shadow

When a relative claim worktree does not exist under the Git primary checkout,
resolution falls back to the current linked root. A shadow symlink below the
linked root that resolves to the current root selected an otherwise unrelated
claim and merged its authority.

Observed:
`RELATIVE_SHADOW None ['CLAIM-shadow-relative']`, with the primary target
absent and the linked-root shadow resolving successfully.

Stable signature:
`defect:relative-worktree-falls-back-to-linked-root-shad:a9421e5faf4c59df`.

### 5. Frontmatter identity can contradict the canonical filesystem path

`_canonical_identity(path, meta)` does not validate its metadata against the
path. A unit stored under `.../TASK-AR-645/UNIT-TASK-AR-645-001.md` but declaring
`task_id: TASK-AR-999`, combined with a claim also declaring task 999, closed
successfully and persisted authority.

Observed: `META_TASK_CONTRADICTION 0 persisted=True`.

Stable signature:
`defect:work-frontmatter-identity-contradicts-canonical:bb011854a4cc3ca2`.

## Independent verification

```text
claim/identity selection: 27 passed, 854 deselected
tests/test_closure_gate.py + tests/test_compound_records.py: 881 passed
temporary archive only: yes
candidate repository writes: none
```

## Required repair boundary

Apply one canonical authority contract to active and released claims: exact
field shapes, exact store/path identity after resolution, exact canonical unit
specification, primary-only relative worktree anchoring, and path-derived work
identity validation. Add failure-first tests for every finding and for failed
closeout non-mutation before requesting another W4 sequence.

