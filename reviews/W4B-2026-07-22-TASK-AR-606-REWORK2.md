---
title: TASK-AR-606 Rework2 Independent W4b Verification
date: 2026-07-22
signal: pass
verdict: APPROVE
task_id: TASK-AR-606
verified_head: 92a07e583c96c2fa79ee651eb1ed7fab60a659b1
verified_by: codex-task-ar-606-rework2-independent-auditor-20260722
worker: codex-root-task-ar-606
tags: [w4b, rework2, independent-verification, git-hooks, posix, fifo, security, github-295]
---

# TASK-AR-606 Rework2 Independent W4b Verification

## Verdict

**APPROVE** at exact HEAD
`92a07e583c96c2fa79ee651eb1ed7fab60a659b1`.

No blocking finding remains. The final hook open now requires and uses
`O_NONBLOCK`, closing the FIFO wait identified by the prior REWORK W4b. A
native POSIX regression creates a real FIFO and executes the repair helper in a
subprocess with a two-second timeout. The earlier linked-ancestor, multi-link,
same-descriptor, descriptor-close, fail-before-config, Windows, mode, content,
and template-parity boundaries remain intact.

## Validation Results

| Metric | Threshold | Measured result | Status |
| --- | --- | --- | --- |
| Exact source state | requested HEAD and clean tree | `92a07e583c96c2fa79ee651eb1ed7fab60a659b1`; clean before report | pass |
| Current focused suite | exact expected result | `24 passed, 2 skipped in 5.58s` | pass |
| FIFO feature gate | fail closed without `O_NONBLOCK` | no open call; repair/readiness false | pass |
| FIFO open flags | final descriptor open is non-blocking | hook flags `0x1d`; `O_NONBLOCK` present | pass |
| Native POSIX regression | real FIFO, bounded subprocess | `mkfifo`, subprocess `timeout=2`, expected output `False` | pass by code audit; skipped on Windows |
| Linked `.githooks` | never follow linked directory entry | `O_DIRECTORY | O_NOFOLLOW`; install rejected; zero config calls | pass |
| Stable multi-link hook | reject `st_nlink != 1` | no fchmod; install rejected; zero config calls | pass |
| Same-FD containment | inspect and chmod one opened inode | `fstat(202)` and `fchmod(202, 0755)` | pass |
| POSIX idempotency | exactly one mode repair | first true, second false; one fchmod; final `0755` | pass |
| FD lifecycle | close every acquired descriptor | open, fstat, rejection, success, and fchmod-error paths balanced | pass |
| Config-before-validation | unsafe hook never writes Git config | linked, missing, directory, FIFO, socket, multi-link, chmod-error: zero config calls | pass |
| Windows behavior | no POSIX filesystem operation | repair false; readiness true; no OS attribute access | pass |
| Host lock | generated-host lock current | check returned zero | pass |
| Hook modes | root and template are `100755` | both entries are `100755` | pass |
| Hook bodies | starting blob IDs preserved | root `c07feb35...`; template `acfc2360...`; unchanged | pass |
| Live/template parity | driver copies byte-identical | both SHA-256 `900fd9d1742c97aa73928e8e3c4c9508668ec749d2ae635f64bb436190aa4d34` | pass |
| Failure-first provenance | new requirement fails before fix | commit `a6e7038`: 1 failed, 1 skipped | pass |
| Latest W4a lineage | task/unit evidence pass on direct implementation lineage | both passed; `f081383` is final HEAD's direct parent | pass |

## FIFO Blocking Remediation

`scripts/lock_merge_driver.py` and its template mirror now require
`O_NONBLOCK` alongside `O_DIRECTORY`, `O_NOFOLLOW`, and `fchmod`. If any
required facility is unavailable, `_open_pre_commit_fd()` returns unavailable
before attempting a filesystem open. Independent instrumentation removed only
`O_NONBLOCK` from a POSIX syscall boundary and observed:

```text
MISSING_O_NONBLOCK=FAIL_CLOSED open_calls=0
```

With all facilities present, the final hook flags changed from the rejected
revision's `0x0d` to `0x1d`:

```text
OPEN_FLAGS directory=0xf hook=0x1d hook_nonblock=true
```

Thus a FIFO can be opened without waiting for a writer and then rejected by
descriptor-bound `fstat`. The independent FIFO syscall model required
`O_NONBLOCK` before allowing its hook open to return; current repair and
installer behavior reached `fstat`, rejected the FIFO, issued no fchmod, closed
both descriptors, returned failure, and made zero Git configuration calls.

The committed native regression is stronger than a source-only flag check. On
POSIX it:

1. creates `.githooks/pre-commit` with `os.mkfifo`;
2. runs the real current helper in a separate Python process;
3. enforces `timeout=2` on that process;
4. requires a successful process whose exact output is `False`.

This Windows verifier cannot execute `os.mkfifo`; the test is one of the two
reported skips. Its platform guard, real FIFO creation, real helper invocation,
bounded timeout, and asserted outcome were inspected directly. The additional
syscall-boundary measurement verifies that the current implementation passes
the non-blocking flag to the exact final-entry open rather than merely
mentioning the constant in unrelated source.

## Preserved Descriptor And Installer Boundaries

For a regular single-link `0644` hook, independent syscall instrumentation
observed this sequence:

```text
open .githooks with O_DIRECTORY|O_NOFOLLOW -> fd 101
open pre-commit relative to fd 101 with O_NOFOLLOW|O_NONBLOCK -> fd 202
close fd 101
fstat fd 202
fchmod fd 202 to 0755
close fd 202
```

The second repair opened and inspected the same way but issued no second
fchmod. Readiness also used the opened final-entry descriptor and closed it.
The exact aggregate result was:

```text
SAME_FD_IDEMPOTENT=PASS fstat_fd=202 fchmod_fd=202 mode=0755 close_all=true
```

This preserves the previous rework's containment properties:

- a stable linked `.githooks` entry is rejected by the directory open;
- the final entry is opened relative to that directory descriptor with
  `O_NOFOLLOW`;
- a stable hardlink/multi-link inode is rejected by `st_nlink != 1`;
- pathname replacement after final open cannot redirect the same-FD fchmod;
- directory-open failure acquires no FD, hook-open failure closes the directory
  FD, and fstat/fchmod failures close both acquired descriptors.

The independently measured failure close paths were:

```text
CLOSE_PATH_DIRECTORY_OPEN=PASS closes=[]
CLOSE_PATH_HOOK_OPEN=PASS closes=[101]
CLOSE_PATH_FSTAT=PASS closes=[101, 202]
CLOSE_PATH_FCHMOD=PASS closes=[101, 202]
```

Installer ordering also remains correct. Linked ancestor, missing hook,
directory hook, FIFO, filesystem socket, multi-link hook, and forced fchmod
failure all returned 1 under the instrumented boundary without invoking the
Git configuration subprocess. The Windows `posix=False` branch returned
repair false and readiness true without touching any POSIX OS facility.

## Registered Commands And Integrity Results

```console
python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
# 24 passed, 2 skipped in 5.58s

python scripts/regen_host_lock_if_needed.py --check
# OK: tests/fixtures/host/agent_runtime.lock.json is up to date

git ls-files -s .githooks/pre-commit src/agent_runtime/templates/project/.githooks/pre-commit
# 100755 c07feb35ee84258ef6ecfee7575b1f697f932e7d .githooks/pre-commit
# 100755 acfc236075ab53871326e76b93a683a72cb15161 src/agent_runtime/templates/project/.githooks/pre-commit
```

The desktop default `C:\Python314\python.exe` does not have pytest installed,
so the literal registered test command was run after placing the available
Python 3.10 validation interpreter first on `PATH`. The two skips are the real
POSIX executable/commit integration and the new real POSIX FIFO regression,
both expected on Windows.

Both current hook blob IDs exactly equal their corresponding values at
`88e7dfa^`, proving that the hook bodies remain unchanged. The root and
template drivers have identical bytes, and the regenerated host lock is
current. `git diff --check d190118..92a07e5` also returned zero.

## Failure-First Reproduction

Commit `a6e70387ed11df7e3006355376105915096c5a69` was exported to a
disposable directory and its two new FIFO-focused tests were run against the
pre-fix implementation:

```console
python -m pytest \
  tests/test_lock_merge_driver.py::test_posix_hook_open_requests_nonblocking_mode \
  tests/test_lock_merge_driver.py::test_executable_repair_rejects_fifo_without_blocking -q
# 1 failed, 1 skipped in 0.77s
```

The source-level requirement failed because the old helper did not contain
`O_NONBLOCK`; the real FIFO test was skipped on Windows as declared. Commit
`f081383` adds both the required feature gate and the actual hook-open flag, so
the failure-first history is causal. The disposable export was removed.

## W4a Evidence And Lineage

The latest evidence records were parsed independently:

- `reviews/VERIFY-2026-07-22-task-ar-606-20260722234957.json`
- `reviews/VERIFY-2026-07-22-unit-task-ar-606-001-20260722234951.json`

Both contain `status: passed`, all three registered commands with zero return
codes, `24 passed, 2 skipped`, a current host lock, and the exact two `100755`
hook entries. Git ancestry confirms implementation commit
`f081383ce32579e54bbdb974eaa0b12c63467e6e` is the direct parent of final W4a
HEAD `92a07e583c96c2fa79ee651eb1ed7fab60a659b1`. Both evidence files identify
worker `codex-root-task-ar-606`, distinct from this verifier.

## Findings And Review History

- No unresolved correctness, blocking-I/O, cross-platform, descriptor-safety,
  content-integrity, parity, scope, or evidence finding remains at this HEAD.
- The rework2 implementation is confined to the live/template driver pair and
  regenerated host lock; its failure-first change adds only the focused FIFO
  regressions. W4a updates task/unit evidence and the review index.
- Hook contents and additional hook policy remain unchanged, respecting the
  unit stop boundary.
- The original W4b APPROVE, both skeptic REJECT records, and the first REWORK
  W4b REJECT remain unchanged as historical evidence. This report supersedes
  them only for exact HEAD `92a07e5`.

## Residual Risks

- Native POSIX execution remains the strongest confirmation for the two
  platform-specific tests. Their implementation is present and bounded, but
  this independent Windows run reported them as skips.
- `O_NONBLOCK` resolves the ordinary-user FIFO denial-of-service case and asks
  supporting devices not to wait for readiness. Exotic device-node open
  semantics are platform/driver-specific and are not covered by the focused
  suite; creating such nodes in a checkout normally requires elevated rights.
- Same-FD inspection and chmod prevent final-path replacement from redirecting
  the mode change. As noted in the prior review, they do not provide a fully
  atomic namespace guarantee against a privileged concurrent directory rename
  or hardlink creation between inspection and fchmod.
- This W4b ran the task-focused suite and direct adversarial syscall models,
  not the complete package suite. Every declared TASK-AR-606 acceptance and
  previously blocking reproduction was nevertheless exercised directly.
