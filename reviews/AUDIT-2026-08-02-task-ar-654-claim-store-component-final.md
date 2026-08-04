---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-claim-store-component-final
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
review_kind: independent-audit
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 2, P2: 1}
release_authorized: false
created_at: 2026-08-02
reviewer: codex-task-ar-654-claim-store-component-auditor
candidate_commit: 9c3119dd39ad6978a74c64f09aa40d43321de995
candidate_tree: 86630bc9f1bc9cf550c25f917d225253150140ff
tags: [task-ar-654, independent-audit, claim-store, path-integrity, fail-closed]
---

# TASK-AR-654 claim-store component final audit

## Verdict

`REVISE — P0: 0, P1: 2, P2: 1. Release authorized: false.`

Candidate `9c3119dd39ad6978a74c64f09aa40d43321de995` (tree
`86630bc9f1bc9cf550c25f917d225253150140ff`) repairs the reported broken-parent
symlink case, and the source and consumer-template implementations are
byte-identical. It still has two fail-open active-authority paths and one
unbounded resolution failure. All adversarial fixtures used temporary
directories; the candidate repository was not used as fixture state.

## P1 findings

### P1-1 — An unreadable direct claim store is treated as empty and permits close mutation

`scripts/closure_gate.py:273-303` validates component metadata and canonical
resolution, but line 304 enumerates entries with
`sorted(claims_dir.glob("CLAIM-*.json"))` outside an error-reporting boundary.
On the candidate's Python 3.10 runtime, `Path.glob()` suppresses the directory
enumeration `PermissionError` and presents an unreadable store as empty.

A temporary direct canonical store containing one valid active
repeated-failure claim was changed to mode `000`. Direct discovery produced:

```text
perm-task_claims: rows=0 findings=[]
```

Actual `scripts/work.py close` against an otherwise closeable unit then
produced:

```text
returncode=0
stdout=work-close: closed
stderr=
unit_mutated=True
claim_mutated=False
unit_status_completed=True
```

The active claim remained present and unchanged, but its only repeated-failure
authority was omitted and the unit was completed. This violates the
fail-closed authority contract before mutation. The byte-identical consumer
template has the same behavior.

### P1-2 — A missing intermediate direct parent is accepted as benign store absence

`scripts/closure_gate.py:278-281` returns empty claims and empty findings for a
`FileNotFoundError` at any checked component. It therefore does not distinguish
the intended compatibility case—an absent final `task_claims` store beneath
direct, non-aliased `agents/runtime` parents—from an absent intermediate
`runtime` component.

The temporary component matrix produced:

```text
absent-all: claims=0 findings=[] reason=None
partial-agents: claims=0 findings=[] reason=None
partial-runtime: claims=0 findings=[] reason=None
direct-empty-store: claims=0 findings=[] reason=None
```

Here `partial-agents` means direct `root/agents` exists while
`root/agents/runtime` is missing; `partial-runtime` means both direct parents
exist while only final `task_claims` is missing. Only the latter is the exact
compatibility boundary recorded in
`reviews/REVIEW-2026-08-02-task-ar-654-broken-parent-store-t3-replan.md:56-63`.

The maintained regression first moves the populated `runtime` directory,
including its active claim, to `shadow-runtime`. If the broken symlink is
omitted after that move, the candidate takes this clean intermediate-missing
branch and again exposes no active authority to work-close. A missing or moved
runtime hierarchy can therefore hide the same populated store that the broken
symlink repair was intended to protect.

## P2 finding

### P2-1 — A claim-entry symlink loop raises an unbounded traceback

`scripts/closure_gate.py:305-309` resolves each claim path before applying the
explicit `path.is_symlink()` rejection. On Python 3.10, a self-referential
symlink raises `RuntimeError`, which is not included in the existing
`except (FileNotFoundError, OSError)` clause.

With a direct store containing
`CLAIM-loop.json -> CLAIM-loop.json`, actual work-close produced:

```text
returncode=1
stdout=
traceback=True
unit_mutated=False
RuntimeError: Symlink loop from '.../task_claims/CLAIM-loop.json'
```

The command fails before mutation, but it does not return the bounded
`active-claim-integrity-invalid:CLAIM-loop.json` outcome used for other invalid
claim paths.

## Compatibility and negative-case matrix

The following temporary cases behaved correctly:

| Case | `_active_claims` finding | Public resolution |
| --- | --- | --- |
| final store absent beneath direct `agents/runtime` | none | `reason=None` |
| valid direct empty store | none | `reason=None` |
| broken symlink at `agents` | `active-claim-store-integrity-invalid` | `active-claim-context-invalid` |
| broken symlink at `runtime` | `active-claim-store-integrity-invalid` | `active-claim-context-invalid` |
| broken final `task_claims` symlink | `active-claim-store-integrity-invalid` | `active-claim-context-invalid` |
| existing symlink alias at any of those three components | `active-claim-store-integrity-invalid` | `active-claim-context-invalid` |
| regular-file component at any of those three locations | `active-claim-store-integrity-invalid` | `active-claim-context-invalid` |

Public callers normalize `root` with `Path.resolve()` before discovery.
Relative direct roots and absolute direct roots therefore behaved identically,
and a public root symlink alias normalized to its real root. Calling the private
`_active_claims()` helper directly with a lexical root alias reports a canonical
path mismatch, but there is no repository caller that bypasses the public root
normalization, so this is not a finding.

No separate race finding is raised. Directories and entries can change between
metadata checks and use, but an inode-stable traversal would be a broader
redesign. The unreadable-enumeration failure above is independently
reproducible without relying on timing.

## Maintained checks

The focused maintained regression and prior alias cases passed:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_compound_records.py::test_work_close_rejects_broken_claim_store_parent_without_mutation \
  tests/test_compound_records.py::test_work_close_rejects_claim_directory_symlink_outside_store_without_mutation \
  tests/test_compound_records.py::test_work_close_rejects_active_claim_symlink_outside_store_without_mutation \
  tests/test_compound_records.py::test_work_close_honors_claim_only_repeat_authority_without_mutation

4 passed in 0.50s
```

The new regression at `tests/test_compound_records.py:914-964` correctly checks
return code 1, the bounded `active-claim-context-invalid` finding, absence of a
success banner and traceback, and byte/state non-mutation for the broken
`runtime` symlink case. It does not cover unreadable enumeration, a missing
intermediate parent, or a claim-entry symlink loop.

## Required fixes

1. Treat only a missing final `task_claims` component beneath verified direct
   `agents/runtime` directories as the compatible absent-store case. A missing
   intermediate component must return
   `active-claim-store-integrity-invalid`.
2. Enumerate the store through an operation whose `OSError` is observable and
   convert enumeration/open failures into
   `active-claim-store-integrity-invalid`; do not let an unreadable store appear
   empty.
3. Reject claim-entry symlinks before resolution where possible and convert
   symlink-loop or other resolution failures, including `RuntimeError`, into a
   bounded per-entry integrity finding.
4. Add actual work-close regressions for all three findings. The two P1 cases
   must prove rejection before unit, claim, backlog, classification, or review
   index mutation; the P2 case must prove a bounded error without traceback.
5. Mirror the repaired implementation byte-for-byte into
   `src/agent_runtime/templates/project/scripts/closure_gate.py` and refresh
   managed lock metadata if its digest changes.

## Release decision

Do not release, merge, close the unit, or authorize claim release on this
candidate. Fresh machine verification and independent review are required on
the exact repaired commit.
