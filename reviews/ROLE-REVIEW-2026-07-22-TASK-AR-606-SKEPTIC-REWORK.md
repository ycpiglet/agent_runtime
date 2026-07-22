---
title: TASK-AR-606 Security and Cross-Platform Skeptic Rework Review
date: 2026-07-22
signal: fail
task_id: TASK-AR-606
verified_head: 7da8a0adfbf4a950b18518245cbd77bbc6035f45
verified_by: codex-task-ar-606-skeptic-20260722-rework
worker: codex-root-task-ar-606
role: skeptic
verdict: REJECT
tags: [task-ar-606, skeptic, rework, security, cross-platform, git-hooks, fifo]
---

# TASK-AR-606 Security and Cross-Platform Skeptic Rework Review

## Verdict

**REJECT** at exact HEAD
`7da8a0adfbf4a950b18518245cbd77bbc6035f45`.

The two original skeptic findings are substantially corrected: stable linked
ancestors and multi-link hooks are rejected, the check and chmod use one open
descriptor, and a missing or non-regular POSIX hook now fails installation
before Git configuration is changed. However, opening the final hook remains a
potentially blocking operation for a FIFO or similar special file. That can
hang both the imperative installer and the watch-only bootstrap before either
can report failure or return its promised status, so the security and
cross-platform boundary is not yet complete.

## Blocking Finding

### [P1] A POSIX FIFO hook can block forever before the regular-file check

`_open_pre_commit_fd()` constructs the final-entry flags as:

```python
hook_flags = os.O_RDONLY | os.O_NOFOLLOW | close_on_exec
hook_fd = os.open(PRE_COMMIT_HOOK.name, hook_flags, dir_fd=hooks_fd)
metadata = os.fstat(hook_fd)
```

The final `pre-commit` entry is opened before `fstat()` determines whether it
is regular. On POSIX, opening a FIFO read-only without `O_NONBLOCK` waits for a
writer. The current feature check does not require `O_NONBLOCK`, and the final
open flags do not include it. Consequently, a checkout containing
`.githooks/pre-commit` as a FIFO can prevent all of these calls from returning:

- `is_pre_commit_executable()`
- `repair_pre_commit_executable()`
- `lock_merge_driver.install()`
- `bootstrap_dev_env.check_hooks_path()` and therefore bootstrap `main()`

The `OSError` handlers do not cover this state because the blocking `open()`
has not failed. This also means the bootstrap's source-level `return 0`
watch-only contract is not enough: the process may never reach it.

Required rework: open the final entry with a non-blocking POSIX strategy (for
example, require and add `O_NONBLOCK` to the final-entry flags), then reject it
after descriptor-bound `fstat()` when it is not regular. Add a native-POSIX
`mkfifo` regression executed with a bounded timeout that proves helper checks
return false promptly, installer returns nonzero without configuring Git, and
bootstrap emits `FIX` and exits zero promptly.

## Original Finding Recheck

### Linked ancestors, multiple names, and replacement consistency

The original linked-path/hardlink finding is resolved for the declared stable
and replacement cases:

- `.githooks` is opened with `O_DIRECTORY | O_NOFOLLOW`; a non-directory or
  linked directory fails closed.
- The final hook is opened relative to that directory descriptor with
  `O_NOFOLLOW`.
- A missing hook or a final directory returns unavailable without `fchmod`.
- `fstat()` requires a regular inode and `st_nlink == 1`, rejecting an already
  multi-linked hook.
- `fstat()` and `fchmod()` operate on the same final-entry descriptor, so a
  path replacement does not redirect chmod to the replacement entry.

A controlled call-boundary probe observed `fchmod` only for a regular,
single-link descriptor. Simulated non-directory `.githooks`, missing hook,
hook directory, and multi-link hook all returned false with zero `fchmod`
calls. The same probe showed that the final open flags do not contain
`O_NONBLOCK`, which is the remaining blocker above.

### Missing and non-regular installer status

The original false-success installer finding is resolved. On POSIX, repair and
readiness validation happen before any Git configuration. Missing, linked,
non-regular, multi-link, or still non-executable hooks return status 1 and do
not set `core.hooksPath`. The focused missing-hook and directory-hook tests
cover both the exit code and the absence of configuration.

## Cross-Platform and Contract Matrix

| Boundary | Result | Evidence |
| --- | --- | --- |
| `.githooks` is not a real directory | pass | `O_DIRECTORY | O_NOFOLLOW`; controlled `NotADirectoryError` path returned false with no `fchmod` |
| hook has multiple names | pass | `st_nlink != 1` is rejected; hardlink regression passes |
| hook is missing or a directory | pass | helpers return false; installer returns 1 before configuration |
| check/change file consistency | pass | `fstat` and `fchmod` use the same open hook fd |
| special-file open cannot wait | **fail** | final `O_RDONLY` open lacks `O_NONBLOCK`; no FIFO regression |
| Windows mode behavior | pass | `posix=False` returns repair=false/readiness=true without filesystem open or chmod |
| bootstrap always returns 0 | conditional fail | explicit `return 0` and normal/failure tests pass, but FIFO can prevent reaching it |

## Independent Verification

```console
python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
# 23 passed, 1 skipped in 12.10s

python scripts/regen_host_lock_if_needed.py --check
# host fixture lock is up to date

git ls-files -s .githooks/pre-commit \
  src/agent_runtime/templates/project/.githooks/pre-commit
# both 100755

git diff --no-index --exit-code -- scripts/lock_merge_driver.py \
  src/agent_runtime/templates/project/scripts/lock_merge_driver.py
# exit 0; both SHA-256 BA5D0E27...80B69

python scripts/taskset_work_gate.py --check
# pass; findings=0

python scripts/work_item_classifier.py --check
# pass; findings=0

python scripts/bootstrap_dev_env.py --check
# environment ready; exit 0
```

The one skip is the native POSIX executable-mode integration on this Windows
review host. Platform-neutral tests and explicit boundary probes still ran;
the missing FIFO case requires the native-POSIX timeout regression described
above.

## Failure-First Provenance

Commit `c027783d0151cf56b1c01ef68ce2887007045365` was exported to a disposable
directory and its four rework regressions were run against the pre-fix code:

```text
test_install_rejects_missing_posix_hook_before_configuring        FAILED
test_install_rejects_non_regular_posix_hook_before_configuring    FAILED
test_executable_repair_refuses_linked_hooks_directory             FAILED
test_executable_repair_refuses_multi_link_hook                    FAILED

4 failed in 1.42s
```

At the reviewed HEAD the same focused suite passes, establishing causal
failure-first coverage for both original skeptic findings. It does not cover
the newly identified blocking-open boundary.

## Modes, Blobs, Parity, Lock, and W4a

- Both hook entries changed from `100644` to `100755` while retaining their
  original blob IDs: root `c07feb35ee84258ef6ecfee7575b1f697f932e7d` and
  template `acfc236075ab53871326e76b93a683a72cb15161`.
- Git reports `0 0` content changes for both hook paths, so hook bodies remain
  unchanged.
- Live and template `lock_merge_driver.py` are byte-identical with SHA-256
  `BA5D0E27B5B674352A7151604DE2CD0D7CCD71E022217C9C36A48B7ACBF80B69`.
- The generated host lock is current, and `git diff --check 1e82308..HEAD`
  passes.
- Latest unit evidence
  `VERIFY-2026-07-22-unit-task-ar-606-001-20260722233621.json` and task
  evidence `VERIFY-2026-07-22-task-ar-606-20260722233631.json` parse correctly,
  are referenced by their work records, and each records three passed commands
  with zero return codes, empty stderr, `23 passed, 1 skipped`, a current lock,
  and both `100755` entries.
- Fix commit `e49fce8` is an ancestor of the exact reviewed HEAD.

Only this rework skeptic report was created. Implementation, tests, hook files,
task/unit records, generated lock, branch state, and existing evidence were not
modified.
