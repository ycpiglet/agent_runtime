---
schema_version: agent-runtime-review/v1
id: SKEPTIC-2026-08-02-task-ar-654-canonical-authority-final
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
review_kind: skeptic
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 4, P2: 0}
created_at: 2026-08-02
reviewer: codex-task-ar-654-canonical-consistency-review
candidate_commit: c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9
candidate_tree: 433ba54cbcdce0e9a61af102b611a3ec10eb4003
tags: [task-ar-654, skeptic, consistency, canonical-authority, fail-closed]
---

# TASK-AR-654 canonical authority final skeptic review

## Verdict

`REVISE — P0: 0, P1: 4, P2: 0.`

Candidate `c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9` (tree
`433ba54cbcdce0e9a61af102b611a3ec10eb4003`) does not satisfy the four
requested data-integrity boundaries. All adversarial fixtures were created
under temporary directories; the candidate worktree was not used as fixture
state. This is a software-quality consistency review, not a security
assessment.

## P1 findings

### P1-1 — Active claim entries and the active claim-store directory may be symlinks

`scripts/closure_gate.py:266-295` accepts `task_claims` based on `is_dir()`,
globs entries, validates JSON identity/shape, and appends the payload without
checking that either the store directory or entry is a direct canonical path.

Temporary results:

- Normal direct claim: `reason=None`, selected `CLAIM-active`; accepted as
  expected.
- Entry `agents/runtime/task_claims/CLAIM-active.json` symlinked to
  `shadow/CLAIM-active.json`: `reason=None`, selected `CLAIM-active`, and its
  defect signature was merged.
- Entire `agents/runtime/task_claims` directory symlinked to
  `elsewhere/claims`: `reason=None`, selected `CLAIM-active`, and its defect
  signature was merged.

Both symlink variants must instead produce a bounded integrity finding and no
trusted claim context. Validate the unresolved lexical store and entry as
direct non-symlinks and require their resolved paths to equal their canonical
locations before reading authority.

### P1-2 — A unit claim's `unit_spec` need not be a non-empty string

`scripts/closure_gate.py:307-336` computes
`str(claim.get("unit_spec") or "").strip()`. Both `unit_spec: ""` and
`unit_spec: []` therefore enter the fallback through `unit_id`, bypassing the
new canonical `unit_spec` comparison.

For both values, the temporary unit claim returned `reason=None`, selected
`CLAIM-active`, and merged the claim-only defect signature. A normal canonical
non-empty string was also accepted, while the maintained noncanonical
unit-spec/symlink regression passed. Unit claims must require `unit_spec` to
be an actual non-empty string equal to the canonical repository-relative unit
path; falsey or container values must not use the legacy fallback.

### P1-3 — Present TASK/UNIT identity fields accept empty and container values

`scripts/closure_gate.py:364-390` converts each identity value with
`str(meta.get(field) or "")` and validates it only when the converted value is
truthy. This conflates an omitted field with a present invalid value.

Temporary results:

- On a canonical UNIT path, setting each of `kind`, `work_id`, `id`,
  `display_id`, `task_id`, `unit_id`, and `parent_id` individually to either
  `""` or `[]` still returned the normal canonical identity
  `(TASK-AR-645, UNIT-TASK-AR-645-001, UNIT-TASK-AR-645-001)`.
- On a canonical TASK path, setting each of `kind`, `work_id`, `id`,
  `display_id`, and `task_id` individually to `[]` still returned the normal
  canonical identity `(TASK-AR-645, "", TASK-AR-645)`.
- Fully canonical scalar metadata remained accepted, as expected.

When any canonical identity key is present, require `isinstance(value, str)`,
a non-empty stripped value, and equality to the path-derived identity. In
particular, `[]` must fail closed rather than behave as omission.

### P1-4 — Conflicting UNIT `unit_id` skips its active claim and can close the wrong identity

`scripts/work.py:1515-1522` chooses `resolved_id` from frontmatter before the
path stem. `close_work` passes that metadata-derived value to active-claim
resolution at `scripts/work.py:2919-2928`; `_claim_authority_for_close` then
accepts an empty context at `scripts/work.py:2523-2538` when no work item
exists for the conflicting identifier.

In the temporary close fixture, the canonical path was
`.../TASK-AR-645/UNIT-TASK-AR-645-001.md`, its frontmatter declared
`unit_id: UNIT-TASK-AR-999-001`, and a valid active claim remained bound to
the canonical `UNIT-TASK-AR-645-001`. Verification evidence was aligned to
the conflicting value solely to isolate authority selection. Exact result:

```text
returncode=0
work-close: closed
unit_completed=true
claim_status=claimed
```

The close therefore skipped the active claim's repeated-failure authority and
mutated the canonical 645 unit while reporting the conflicting 999 identity.
Close authority must derive `resolved_id` from the canonical path, validate
all present frontmatter identities against it, and fail before mutation on a
conflict.

## Checks and results

| Check | Result |
| --- | --- |
| `git rev-parse HEAD` | `c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9` |
| `git rev-parse HEAD^{tree}` | `433ba54cbcdce0e9a61af102b611a3ec10eb4003` |
| Temporary direct/symlink/shape/identity/close probe | Four requested boundaries reproduced as failures; normal canonical active claim accepted |
| `pytest -q tests/test_closure_gate.py tests/test_compound_records.py` | `890 passed in 54.82s` |
| Focused maintained normal/rejection checks | `4 passed in 0.49s` |

The four focused maintained checks were the canonical task-context normal
case plus existing rejection cases for a released-claim symlink, a unit-spec
symlink alias, and a contradictory unit `task_id`. Their passing results show
that the candidate preserves those named behaviors, but the suite does not
cover the four combinations above.

## Release decision

Do not release, merge, or close TASK-AR-654 on this candidate. Add
failure-first tests for both active-claim symlink forms, empty/container
`unit_spec`, present non-string/empty TASK and UNIT identity values, and the
conflicting-`unit_id` close path. Require failed-close byte/state
non-mutation, then repair and request fresh independent review.
