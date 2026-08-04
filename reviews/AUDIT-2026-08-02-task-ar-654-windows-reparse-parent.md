---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-windows-reparse-parent
title: TASK-AR-654 Windows reparse-parent independent audit
date: 2026-08-02
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: independent-audit
reviewer: codex-independent-task-ar-654-windows-reparse-parent-audit
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: 9c3119dd39ad6978a74c64f09aa40d43321de995
candidate_tree: 86630bc9f1bc9cf550c25f917d225253150140ff
independence_status: independent
implementation_reviewed: true
release_authorized: false
created_at: 2026-08-02T13:55:00+09:00
tags: [task-ar-654, independent-audit, claim-store, windows, reparse-point, junction, fail-closed, revise]
---

# TASK-AR-654 Windows reparse-parent independent audit

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

Exact candidate
`9c3119dd39ad6978a74c64f09aa40d43321de995`, tree
`86630bc9f1bc9cf550c25f917d225253150140ff`, correctly repairs the reported
broken parent-symlink bypass on POSIX, preserves valid direct no-claim hosts,
and keeps source, consumer template, and host-lock state aligned. It retains
one platform-specific form of the same fail-open defect: a broken Windows
directory junction in a parent component is not identified by the retained
`st_mode` value.

This was a bounded software-quality and data-integrity audit. All behavioral
fixtures were created in temporary directories. No task, unit, claim,
generated view, index, Compound, external system, or repository file was
changed during probing. This report is the audit's only repository change; no
commit was created.

## P1-1 — A broken Windows junction parent is treated as an absent store

`scripts/closure_gate.py::_active_claims()` calls `component.lstat()` for
`agents`, `agents/runtime`, and `agents/runtime/task_claims`, but retains only
`st_mode`. It rejects `stat.S_ISLNK(mode)` and non-directories. A missing
component returns an empty claim set with no integrity finding.

That distinction is sufficient for POSIX symbolic links. It is not sufficient
for Windows directory junctions. In the supported CPython range, `lstat()`
opens name-surrogate reparse points without following them, but only an actual
symbolic link receives `S_IFLNK`. A directory junction retains directory mode;
its alias identity is exposed through `st_file_attributes` and
`st_reparse_tag`, including `IO_REPARSE_TAG_MOUNT_POINT`. `Path.is_junction()`
was added only in Python 3.12, while this package supports Python 3.10 and
newer.

Consequently, a broken junction at `agents/runtime` follows this control flow:

1. `lstat(agents/runtime)` succeeds on the reparse point and reports a
   directory mode, so the `S_ISLNK`/`S_ISDIR` guard accepts it.
2. `lstat(agents/runtime/task_claims)` cannot traverse the broken junction and
   raises `FileNotFoundError`.
3. The missing-component branch returns `([], [])`, interpreting the aliased
   store as a valid no-claim host.
4. Actual `work close` may then proceed without the hidden active claim's
   repeated-failure authority.

The audit modeled the documented Windows result by returning
`S_IFDIR | 0o777` for the broken parent reparse point and allowing descendant
`lstat()` to raise `FileNotFoundError`. Candidate `_active_claims()` returned:

```text
([], [])
```

The same model must instead return:

```text
([], ['active-claim-store-integrity-invalid'])
```

Primary semantic references:

- Python 3.10 `os.lstat()` and Windows reparse metadata:
  <https://docs.python.org/3.10/library/os.html#os.lstat>
- Python 3.10 `stat.IO_REPARSE_TAG_MOUNT_POINT`:
  <https://docs.python.org/3.10/library/stat.html>
- CPython 3.10 Windows stat conversion, which assigns `S_IFLNK` only to the
  symbolic-link reparse tag and retains other name-surrogate identity in
  reparse metadata:
  <https://github.com/python/cpython/blob/v3.10.20/Python/fileutils.c>
- `Path.is_junction()` availability from Python 3.12:
  <https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.is_junction>

This is P1 because it reproduces the repaired fail-open authority loss on a
supported runtime/platform shape and can allow closeout mutation without the
canonical active claim. The repository's test matrix runs on Ubuntu for
Python 3.10, 3.11, and 3.12, so the committed POSIX symlink regression cannot
detect this Windows representation difference.

## Positive compatibility and parity evidence

The POSIX implementation and committed regression otherwise satisfy the
narrow contract:

- The committed actual-close regression moved a populated
  `agents/runtime` directory aside, installed a broken directory symlink, and
  observed bounded `closeout:active-claim-context-invalid` refusal before
  unit, hidden claim, backlog, classification, or review-index mutation.
- Existing active claim-file, final claim-directory, and linked released-claim
  symlink cases also refused without mutation.
- A temporary component matrix accepted all four direct no-claim depths:
  missing `agents`, missing `runtime`, missing `task_claims`, and an empty
  direct `task_claims` directory.
- The same matrix rejected file, live-symlink, and broken-symlink shapes at
  each of `agents`, `agents/runtime`, and `agents/runtime/task_claims`, always
  with `active-claim-store-integrity-invalid`.
- Actual `work close` returned `0` for both compatibility controls beneath
  direct parents: an absent final `task_claims` store and an empty direct final
  store.
- `scripts/closure_gate.py` and
  `src/agent_runtime/templates/project/scripts/closure_gate.py` were
  byte-identical with SHA-256
  `2443bcf0526ce9372c2ef3723496745dfe2e26420a25793417df8f10b8e4b1e7`.
- The host lock recorded that same managed-file digest.
- `python scripts/template_mirror_gate.py --check` passed with
  `expected=84 common=84 identical=81 intentional=3 findings=0`.
- `python scripts/regen_host_lock_if_needed.py --check` reported the host lock
  current.

Focused replay evidence:

```text
tests/test_compound_records.py selected symlink/no-claim cases: 5 passed
tests/test_closure_gate.py multiple-active-claim control: 1 passed
temporary POSIX component matrix: 13 passed
temporary actual-close no-claim controls: 2 passed
source/template byte comparison: identical
tracked worktree after probing: clean
```

These results show that the P1 is not a regression in ordinary no-claim-host
compatibility or template packaging. It is specifically the loss of Windows
name-surrogate identity when `_active_claims()` discards the rest of the
`lstat()` result.

## Required repair and recommended regression

Retain the full `lstat()` result and reject name-surrogate reparse aliases
before descending. For the supported Python 3.10+ range, inspect
`st_file_attributes`/`st_reparse_tag` and reject at least
`IO_REPARSE_TAG_SYMLINK` and `IO_REPARSE_TAG_MOUNT_POINT`; do not rely solely
on `Path.is_junction()`, which is unavailable before Python 3.12. Preserve the
current direct-directory and genuinely missing-store behavior.

Add a cross-platform unit regression that models an existing parent with
`S_IFDIR` plus `IO_REPARSE_TAG_MOUNT_POINT`, followed by descendant
`FileNotFoundError`, and requires
`active-claim-store-integrity-invalid`. Also add a Windows integration
regression using `mklink /J`: populate the canonical active store, move it
aside, replace `agents/runtime` with a junction whose target is then removed,
run actual `work close`, and assert bounded refusal before unit, hidden claim,
backlog, classification, or review-index mutation. Keep explicit positive
controls for a direct missing final store and an empty direct final store.

## Release decision

Candidate `9c3119dd39ad6978a74c64f09aa40d43321de995` is not release-authorized.
Repair the Windows reparse-parent branch, add the recommended regression, and
request a fresh independent review on one exact post-repair candidate.
