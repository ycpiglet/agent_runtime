---
title: TASK-AR-606 Security and Cross-Platform Skeptic Rework 2 Review
date: 2026-07-22
signal: pass
score: 99
task_id: TASK-AR-606
verified_head: 92a07e583c96c2fa79ee651eb1ed7fab60a659b1
verified_by: codex-task-ar-606-skeptic-20260722-rework2
worker: codex-root-task-ar-606
role: skeptic
verdict: APPROVE
tags: [task-ar-606, skeptic, rework2, security, cross-platform, git-hooks, fifo]
---

# TASK-AR-606 Security and Cross-Platform Skeptic Rework 2 Review

## Verdict

**APPROVE** at exact HEAD
`92a07e583c96c2fa79ee651eb1ed7fab60a659b1`.

The previous FIFO/open-wait blocker is closed. The secure POSIX path now
requires `O_NONBLOCK` support and includes it in the final hook open flags
before descriptor-bound `fstat()`. A special file can therefore be classified
and rejected without waiting for another process. The earlier linked-directory,
multi-link, missing/non-regular, same-descriptor, Windows no-op, and bootstrap
watch-only protections remain intact. No blocking security, cross-platform,
scope, parity, or evidence finding remains.

## Previous Blocker Resolution

`_open_pre_commit_fd()` now fails closed unless all of `O_DIRECTORY`,
`O_NOFOLLOW`, `O_NONBLOCK`, and `fchmod` are available. It opens the final hook
with:

```python
os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | close_on_exec
```

It then applies `fstat()` and accepts only a regular inode with exactly one
name. The mode change still uses `fchmod()` on that same opened descriptor.
For a FIFO, `O_NONBLOCK` prevents the read-only open from waiting for a writer;
`fstat()` recognizes the non-regular inode and closes it without `fchmod`.

Commit `a6e7038` adds both a source-level nonblocking flag regression and a
native-POSIX FIFO regression. The FIFO test creates the special file with
`mkfifo`, invokes repair in a subprocess with a two-second timeout, and requires
an immediate `False` result. It is correctly skipped where POSIX FIFOs are not
available.

## Boundary Recheck Matrix

| Boundary | Result | Evidence |
| --- | --- | --- |
| `.githooks` is not a real directory | pass | directory open retains `O_DIRECTORY | O_NOFOLLOW`; non-directory path fails before hook open |
| linked `.githooks` directory | pass | `O_NOFOLLOW` rejects the linked ancestor; regression remains green |
| hook has multiple names | pass | `st_nlink != 1` is rejected; hardlink regression remains green |
| hook is missing or a directory | pass | helper returns unavailable; POSIX installer returns 1 before Git configuration |
| special hook file | pass | final open uses `O_NONBLOCK`; FIFO is rejected without `fchmod` or writer wait |
| check/change file consistency | pass | `fstat` and `fchmod` use the same hook fd |
| Windows behavior | pass | `posix=False` returns repair=false/readiness=true without opening or chmodding a path |
| bootstrap watch-only status | pass | normal check exits 0; synthetic WARN/FIX state also reaches and returns 0 |

A controlled call-boundary probe observed these exact results:

```text
regular:    nonblock=true, fstat_fd=11, fchmod_fd=11
directory:  nonblock=true, fchmod_calls=0
fifo:       nonblock=true, fchmod_calls=0
multi-link: nonblock=true, fchmod_calls=0
missing:    nonblock=true, fchmod_calls=0
Windows:    repair=false, readiness=true, filesystem open not reached
```

This confirms both actual flag composition and descriptor identity rather than
relying only on the source-inspection regression.

## Independent Verification

```console
python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
# 24 passed, 2 skipped in 5.28s

python scripts/regen_host_lock_if_needed.py --check
# host fixture lock is up to date

git ls-files -s .githooks/pre-commit \
  src/agent_runtime/templates/project/.githooks/pre-commit
# both 100755

git diff --no-index --exit-code -- scripts/lock_merge_driver.py \
  src/agent_runtime/templates/project/scripts/lock_merge_driver.py
# exit 0; both SHA-256 900FD9D1...A4D34

python scripts/taskset_work_gate.py --check
# pass; findings=0

python scripts/work_item_classifier.py --check
# pass; findings=0

python scripts/bootstrap_dev_env.py --check
# environment ready; exit 0
```

The two skips are the real POSIX chmod integration and native POSIX FIFO test
on this Windows reviewer host. Their platform-neutral contracts were exercised
independently at the function boundary, while the committed native tests will
run on a POSIX test host.

## Failure-First Provenance

Commit `a6e70387` was exported to a disposable directory and its two special-file
regressions were run against the pre-fix implementation on this Windows host:

```text
test_posix_hook_open_requests_nonblocking_mode              FAILED
test_executable_repair_rejects_fifo_without_blocking        SKIPPED

1 failed, 1 skipped in 0.70s
```

The failure is causal: the pre-fix `_open_pre_commit_fd()` contained no
`O_NONBLOCK`. At the reviewed HEAD the same source regression passes, the full
focused suite is green, and the native FIFO regression is present with a hard
timeout.

## Modes, Blobs, Parity, Lock, and W4a

- Both hook entries are `100755` while preserving their starting blobs:
  root `c07feb35ee84258ef6ecfee7575b1f697f932e7d` and template
  `acfc236075ab53871326e76b93a683a72cb15161`.
- Git reports `0 0` content changes for both hook paths, confirming their
  bodies were not changed.
- Live and template `lock_merge_driver.py` are byte-identical with SHA-256
  `900FD9D1742C97AA73928E8E3C4C9508668EC749D2AE635F64BB436190AA4D34`.
- The generated host lock is current, and `git diff --check 1e82308..HEAD`
  passes.
- Latest unit evidence
  `VERIFY-2026-07-22-unit-task-ar-606-001-20260722234951.json` and task
  evidence `VERIFY-2026-07-22-task-ar-606-20260722234957.json` parse correctly,
  are referenced by their canonical work records, and each records three
  passed commands with zero return codes, empty stderr, `24 passed, 2 skipped`,
  a current host lock, and both `100755` entries.
- Fix commit `f081383` and the latest W4a evidence commit are ancestors of the
  exact reviewed HEAD.

## Non-Blocking Residual

This independent run occurred on Windows, so it could not execute a real FIFO
or POSIX chmod. The committed native test is appropriately timeout-bounded,
and the implementation's actual flag composition and rejection branches were
independently exercised. A POSIX CI run remains the strongest end-to-end
confirmation but is not a blocker for this review.

Only this rework2 skeptic report was created. Implementation, tests, hook
files, task/unit records, generated lock, branch state, and existing evidence
were not modified.
