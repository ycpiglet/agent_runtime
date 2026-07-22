---
title: TASK-AR-606 Rework Independent W4b Verification
date: 2026-07-22
signal: fail
verdict: REJECT
task_id: TASK-AR-606
verified_head: 7da8a0adfbf4a950b18518245cbd77bbc6035f45
verified_by: codex-task-ar-606-rework-independent-auditor-20260722
worker: codex-root-task-ar-606
tags: [w4b, rework, independent-verification, git-hooks, posix, security, github-295]
---

# TASK-AR-606 Rework Independent W4b Verification

## Verdict

**REJECT** at exact HEAD
`7da8a0adfbf4a950b18518245cbd77bbc6035f45`.

The rework correctly closes the four findings recorded against the first W4b:
linked `.githooks` is rejected, stable multi-link hook inodes are rejected,
`fstat` and `fchmod` operate on the same final-entry descriptor, and POSIX
installation validates activation before writing Git configuration. All
descriptor close paths inspected by this auditor are balanced.

One blocking non-regular-path defect remains. The final hook is opened with
`O_RDONLY | O_NOFOLLOW | O_CLOEXEC`, without `O_NONBLOCK`, before `fstat`
determines its file type. A user-created FIFO with no writer therefore blocks
inside `open()` indefinitely instead of being rejected. The same ordering can
block on device nodes whose open waits for readiness. This affects both the
imperative installer and bootstrap readiness checks and prevents W4b approval.

## Validation Results

| Metric | Threshold | Measured result | Status |
| --- | --- | --- | --- |
| Exact source state | requested HEAD and clean tree | `7da8a0adfbf4a950b18518245cbd77bbc6035f45`; clean before report | pass |
| Current focused suite | all focused regressions pass | `23 passed, 1 skipped in 8.70s` | pass |
| Host lock | generated-host lock current | check returned zero | pass |
| Hook modes | root and template are `100755` | both entries are `100755` | pass |
| Hook bodies | starting blob IDs preserved | root `c07feb35...`; template `acfc2360...`; both unchanged | pass |
| Live/template parity | driver copies byte-identical | both SHA-256 `ba5d0e27b5b674352a7151604de2cd0d7ccd71e022217c9c36a48b7acbf80b69` | pass |
| Failure-first provenance | all four security regressions fail before fix | commit `c027783`: 4 failed | pass |
| Linked `.githooks` | never follow directory entry | directory open uses `O_DIRECTORY | O_NOFOLLOW`; linked-open failure returns unavailable | pass |
| Stable hardlink/multi-link | refuse `st_nlink != 1` | repair/readiness false; no fchmod; all FDs closed | pass |
| Same-FD containment | validate and mutate the opened hook inode | `fstat(202)` and `fchmod(202, 0755)` observed; no path chmod | pass |
| POSIX idempotency | exactly one repair | first true, second false; one `fchmod`; mode `0755` | pass |
| FD lifecycle | close every acquired FD on success and failure | directory-open, hook-open, fstat, rejection, success, and fchmod-error paths balanced | pass |
| Config-before-validation | unsafe POSIX hooks never invoke Git config | linked, missing, directory, socket, device, multi-link, and chmod-error models: zero config calls | pass |
| Non-regular open safety | reject without blocking before type validation | final `open` omits `O_NONBLOCK`; FIFO model remained blocked before `fstat` | **fail** |
| Latest W4a lineage | task/unit evidence pass on implementation lineage | both passed; implementation `e49fce8` is final HEAD's direct parent | pass |

## Blocking Finding

### [P1] FIFO or blocking device can hang before non-regular rejection

`scripts/lock_merge_driver.py:67-75` constructs these flags and opens the final
entry before inspecting it:

```python
directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | close_on_exec
hook_flags = os.O_RDONLY | os.O_NOFOLLOW | close_on_exec
hooks_fd = os.open(..., directory_flags)
hook_fd = os.open(PRE_COMMIT_HOOK.name, hook_flags, dir_fd=hooks_fd)
```

The POSIX `open()` contract states that a read-only FIFO open with
`O_NONBLOCK` clear waits for a writer; device opens may likewise wait for the
device to become ready. See the authoritative
[POSIX `open()` specification](https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html).
The current `hook_flags` do not include `O_NONBLOCK`.

The auditor instrumented the exact helper with a POSIX syscall boundary whose
FIFO open follows that contract. After the final-entry open began, a bounded
observation found the worker still blocked and `fstat` had not run:

```text
FIFO_OPEN_BEFORE_FSTAT=BLOCKED thread_alive=true fstat_calls=0 O_NONBLOCK=false
FIFO_AFTER_WRITER_MODEL=REJECTED close_all=true
```

Once the modeled writer released the open, `fstat` correctly rejected the FIFO
and closed both FDs. The defect is therefore not the eventual `S_ISREG` check;
it is that a blocking special file can prevent that check from ever executing.

This is directly reachable by an ordinary POSIX checkout user through
`mkfifo .githooks/pre-commit`. It causes both
`repair_pre_commit_executable(..., posix=True)` and
`is_pre_commit_executable(..., posix=True)` to hang. Consequently:

- `lock_merge_driver.py --install` can hang before returning its intended
  nonzero unsafe-hook result;
- `bootstrap_dev_env.py --check` can hang despite being a read-only readiness
  command;
- the existing non-regular installer regression covers a directory but not a
  FIFO, socket, or device open that may block before `fstat`.

Required rework:

1. Make the final-entry open non-blocking, including a feature check that fails
   closed when the required flag is unavailable. Consider `O_NOCTTY` as well
   so opening a terminal device cannot acquire it as a controlling terminal.
2. Add a native POSIX FIFO regression with no writer and a bounded subprocess
   timeout. It must return nonzero promptly, leave `core.hooksPath` unset, and
   leave the FIFO unchanged.
3. Add a filesystem UNIX-socket case and document or test the intended device
   handling. The type check must be reached without waiting for peer/device
   readiness.
4. Retain the existing `dir_fd + O_NOFOLLOW`, `st_nlink == 1`, same-FD
   `fstat/fchmod`, and fail-before-config behavior.

## Passing Descriptor And Installer Boundaries

The current helper was exercised under an independently instrumented POSIX
syscall layer. For a regular `0644` hook, the observed operations were:

```text
directory open -> fd 101
relative pre-commit open(dir_fd=101) -> fd 202
close(101)
fstat(202)
fchmod(202, 0755)
close(202)
```

The second repair repeated the two opens and `fstat(202)` but issued no second
`fchmod`; readiness inspected the same opened hook descriptor and closed it.
The combined measurement was:

```text
SAME_FD_IDEMPOTENT=PASS fstat_fd=202 fchmod_fd=202 mode=0755 close_all=true
OPEN_FLAGS directory=0xf hook=0xd hook_nonblock=false
```

The directory descriptor uses `O_DIRECTORY | O_NOFOLLOW`, and the final hook
is opened relative to it with `O_NOFOLLOW`. This prevents a stable linked
`.githooks` entry or final symlink from being followed. The returned hook
descriptor remains bound to its inode across pathname replacement, and both
metadata inspection and chmod use that descriptor. A stable hardlink is
rejected by `metadata.st_nlink != 1` before chmod.

Close-path instrumentation produced the following exact outcomes:

```text
CLOSE_PATH_DIRECTORY_OPEN=PASS closes=[]
CLOSE_PATH_HOOK_OPEN=PASS closes=[101]
CLOSE_PATH_FSTAT=PASS closes=[101, 202]
CLOSE_PATH_FCHMOD=PASS closes=[101, 202]
```

Regular success, idempotent no-op, non-regular rejection, and multi-link
rejection also closed both acquired descriptors. A forced `fchmod`
`PermissionError` propagated to the installer, which returned 1 without any
Git config call and still closed the hook descriptor.

The installer ordering at `scripts/lock_merge_driver.py:193-224` now performs
repair and readiness validation before defining and invoking `_cfg`. Under the
instrumented boundary, linked ancestor, missing final entry, directory, FIFO,
socket, character device, block device, multi-link inode, and fchmod error all
returned 1 with zero configuration calls once their opens were permitted to
return. Thus the previous partial-configuration issue is fixed; the blocking
open finding is the remaining exception to prompt failure.

## Registered Commands And Integrity Results

```console
python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
# 23 passed, 1 skipped in 8.70s

python scripts/regen_host_lock_if_needed.py --check
# OK: tests/fixtures/host/agent_runtime.lock.json is up to date

git ls-files -s .githooks/pre-commit src/agent_runtime/templates/project/.githooks/pre-commit
# 100755 c07feb35ee84258ef6ecfee7575b1f697f932e7d .githooks/pre-commit
# 100755 acfc236075ab53871326e76b93a683a72cb15161 src/agent_runtime/templates/project/.githooks/pre-commit
```

The desktop default `C:\Python314\python.exe` lacks pytest, so the literal
registered test command was executed after placing the available Python 3.10
validation interpreter first on `PATH`. The single skip is the real POSIX chmod
integration on this Windows host. Windows Python also lacks `O_DIRECTORY`,
`O_NOFOLLOW`, descriptor-relative `open`, and `fchmod`; the focused linked and
multi-link tests therefore exercise the helper's fail-closed unsupported-API
path here. The separate syscall instrumentation above was necessary to audit
the intended POSIX path.

Both hook index blobs exactly equal their values at `88e7dfa^`, proving hook
bodies remain unchanged. The live and template drivers have identical bytes,
and the regenerated host lock is current.

## Failure-First Reproduction

Commit `c027783d0151cf56b1c01ef68ce2887007045365` was exported to a
disposable directory. Its four security regressions were run against the
pre-rework implementation:

```console
python -m pytest \
  tests/test_lock_merge_driver.py::test_install_rejects_missing_posix_hook_before_configuring \
  tests/test_lock_merge_driver.py::test_install_rejects_non_regular_posix_hook_before_configuring \
  tests/test_lock_merge_driver.py::test_executable_repair_refuses_linked_hooks_directory \
  tests/test_lock_merge_driver.py::test_executable_repair_refuses_multi_link_hook -q
# 4 failed in 1.73s
```

The two installer tests observed return code 0 and premature hook-path
configuration; the linked ancestor and hardlink tests observed a true repair
result. These are causal failures and confirm that `e49fce8` is genuine rework
rather than test-only relabeling. The disposable export was removed.

## W4a Evidence And Lineage

The latest evidence records were parsed independently:

- `reviews/VERIFY-2026-07-22-task-ar-606-20260722233631.json`
- `reviews/VERIFY-2026-07-22-unit-task-ar-606-001-20260722233621.json`

Both record `status: passed`, the three registered commands with zero return
codes, `23 passed, 1 skipped`, a current host lock, and the expected two
`100755` hook entries. Git ancestry confirms implementation commit
`e49fce82545426eefee4f487b11b3005e51a793c` is the direct parent of final W4a
HEAD `7da8a0adfbf4a950b18518245cbd77bbc6035f45`. Both records identify worker
`codex-root-task-ar-606`, distinct from this verifier.

## Review History And Scope

The original `reviews/W4B-2026-07-22-TASK-AR-606.md` APPROVE record and
`reviews/ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC.md` REJECT record remain
unchanged as historical evidence. This report evaluates only the new exact
HEAD and does not overwrite either conclusion.

The rework implementation is confined to the live/template driver pair,
focused regression file, and regenerated host lock; W4a updates task/unit
evidence and the review index. Hook content and additional hook policy remain
outside the change, respecting the unit stop boundary.

## Residual Risks After Required Rework

- Native Linux/macOS execution remains necessary to prove a repaired hook runs
  during an actual Git commit and that FIFO/socket cases return promptly.
- Same-FD `fstat/fchmod` prevents final-path replacement from redirecting
  chmod after open. It does not make namespace containment fully atomic against
  a hostile concurrent directory rename or a new hardlink created between the
  link-count check and fchmod. That stronger threat model should be stated or
  addressed separately if required.
- This W4b ran the focused task suite and direct adversarial syscall models,
  not the complete package suite. The blocking finding arises before the type
  check and is not covered by the current tests.
