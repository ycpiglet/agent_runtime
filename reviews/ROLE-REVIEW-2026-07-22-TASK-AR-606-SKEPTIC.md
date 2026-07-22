---
title: TASK-AR-606 Security and Cross-Platform Skeptic Review
date: 2026-07-22
signal: fail
task_id: TASK-AR-606
verified_head: 2deb47498e95679503c6a1735b4e3e05f9d485c3
verified_by: codex-task-ar-606-skeptic-20260722
worker: codex-root-task-ar-606
role: skeptic
verdict: REJECT
tags: [task-ar-606, skeptic, security, cross-platform, git-hooks, chmod]
---

# TASK-AR-606 Security and Cross-Platform Skeptic Review

## Verdict

**REJECT** at exact HEAD
`2deb47498e95679503c6a1735b4e3e05f9d485c3`.

The normal executable-bit repair, Git metadata, hook-body preservation,
Windows branch, bootstrap watch-only behavior, host lock, and live/template
parity are correct. However, the claimed checkout-containment boundary is not
enforced for a linked `.githooks` ancestor, a hard-linked hook, or replacement
between `lstat()` and `chmod()`. A POSIX install with a missing hook also
configures the unusable hook path and returns success. These are blocking for
a security/cross-platform task whose helper explicitly promises not to chmod
outside the checkout and whose acceptance requires an executable hook after
installation.

## Blocking Findings

### [P1] Linked ancestors and hardlinks can redirect chmod outside the checkout

`repair_pre_commit_executable()` performs this sequence in
`scripts/lock_merge_driver.py` and its template mirror:

```text
hook = repo_root / ".githooks" / "pre-commit"
mode = hook.lstat().st_mode
verify final entry is regular
hook.chmod(desired)
```

`lstat()` protects only the final path component. It follows a linked
`.githooks` ancestor before inspecting `pre-commit`. A disposable direct probe
created this layout, intercepted `chmod` before any external mode was changed,
and observed:

```text
repo/.githooks -> junction to <temp>/outside
<temp>/outside/pre-commit = regular file

HOOK_LSTAT_REGULAR=True
HOOK_LEXICAL=<temp>/repo/.githooks/pre-commit
HOOK_RESOLVED=<temp>/outside/pre-commit
REPAIR_CHANGED=True
CHMOD_CALLS=1
CHMOD_RESOLVED_OUTSIDE=True
```

The probe used a Windows junction with `posix=True` to exercise the exact
platform-independent path algorithm; a POSIX symlinked ancestor has the same
lookup semantics. The native Windows branch normally avoids chmod and is not
itself vulnerable to this mutation.

A separate real-filesystem probe created `repo/.githooks/pre-commit` as a hard
link to a file outside `repo`. The final entry passed `S_ISREG`,
`os.path.samefile(hook, outside)` was true, and the repair entered its chmod
call with `changed=True`. On POSIX, chmod changes the shared inode and therefore
the outside name as well.

There is also a time-of-check/time-of-use window: after `lstat()` accepts a
regular entry, that entry or an ancestor can be exchanged before
`Path.chmod()`. Local inspection confirmed the runtime signature is
`Path.chmod(self, mode, *, follow_symlinks=True)`, and the implementation does
not bind the check and change to one file descriptor. A replacement symlink is
therefore followed by default.

The stable final-entry protections do work: a directory was rejected by a
direct probe with zero chmod calls, and the `S_ISLNK` branch returns false. They
do not cover ancestor links, hardlinks, or the race.

Required rework: use a descriptor-based POSIX operation that opens the hook
without following links, validates the opened inode as regular, and applies
`fchmod` to that same descriptor. Reject linked path ancestors and either
reject multi-link hook inodes or explicitly establish an equivalent hardlink
containment policy. Add adversarial regressions for an ancestor symlink,
hardlink, and check/change replacement.

### [P1] Missing POSIX hook is reported as a successful install

A disposable Git repository with no `.githooks/pre-commit` produced:

```text
repair_pre_commit_executable(..., posix=True) = False
is_pre_commit_executable(..., posix=True) = False
install(..., posix=True) return code = 0
core.hooksPath = .githooks
output = lock-merge-driver: installed ...; pre-commit executable repair unavailable
```

The imperative installer therefore says `installed` and returns success while
the configured pre-commit hook is absent and cannot execute. This contradicts
the unit acceptance that POSIX Git executes the configured hook after
installation and makes automation unable to distinguish activation from a
degraded install by exit code.

This is distinct from bootstrap's documented watch-only behavior. Bootstrap
correctly reports a `FIX` line and exits zero; `lock_merge_driver.py --install`
is the imperative installer and has no always-zero contract.

Required rework: after repair, fail nonzero (or raise a handled installation
error) whenever a POSIX hook is missing, non-regular, or still not executable.
Do not print `installed` for that state. Add missing-hook and non-regular-hook
installer tests that assert both output and process status.

## Passing Security and Cross-Platform Cases

- Focused suite: `19 passed, 1 skipped in 13.54s`. The skipped test is the
  native POSIX chmod integration, expected on this Windows reviewer host.
- A simulated POSIX mode probe repaired `0640` to `0751`, preserving all
  original permission bits while adding `0111`. The first call returned true,
  readiness returned true, and a second call returned false with no second
  chmod call.
- Missing final hook, a final directory, and other non-regular final-entry mode
  checks return not-ready without invoking chmod at helper level.
- A forced `PermissionError` propagates from the repair helper and from the
  imperative installer. The installer had already configured
  `core.hooksPath=.githooks`, so failure is explicit but partially applied.
- Bootstrap catches the same `PermissionError`, reports `FIX ... pre-commit is
  not executable`, and preserves its documented exit-zero watch-only contract.
  A top-level synthetic failure-state run with two `FIX` lines also returned
  zero. The real `--check` command returned zero and reported the current
  environment ready.
- With `posix=False`, a patched `Path.chmod` that would fail if called was never
  invoked. Repair returned false, readiness returned true, and installer
  returned zero with `POSIX mode not required`.
- Both hook paths are tracked as `100755`:

  ```text
  100755 c07feb35ee84258ef6ecfee7575b1f697f932e7d .githooks/pre-commit
  100755 acfc236075ab53871326e76b93a683a72cb15161 src/agent_runtime/templates/project/.githooks/pre-commit
  ```

- Hook bodies are unchanged. The root blob remains
  `c07feb35ee84258ef6ecfee7575b1f697f932e7d`, and the template blob remains
  `acfc236075ab53871326e76b93a683a72cb15161` across `80e9633^` to the reviewed
  HEAD. Git reports only `100644 => 100755`, with `0 0` content changes.
- Live and template `lock_merge_driver.py` files are byte-identical.
- The generated-host lock is current. Taskset work gate and work-item
  classifier both passed with zero findings. `git diff --check` passed.

## Commands and Exact Results

```console
py -3.10 -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
# 19 passed, 1 skipped in 13.54s

py -3.10 scripts/regen_host_lock_if_needed.py --check
# OK: tests/fixtures/host/agent_runtime.lock.json is up to date

py -3.10 scripts/taskset_work_gate.py --check
# taskset-work-gate: pass; findings=0

py -3.10 scripts/work_item_classifier.py --check
# work-item-classifier: pass; findings=0

py -3.10 scripts/bootstrap_dev_env.py --check
# environment ready; exit 0

git ls-files -s .githooks/pre-commit \
  src/agent_runtime/templates/project/.githooks/pre-commit
# both 100755

git diff --no-index --exit-code -- scripts/lock_merge_driver.py \
  src/agent_runtime/templates/project/scripts/lock_merge_driver.py
# exit 0

git diff --check 1e82308..2deb47498e95679503c6a1735b4e3e05f9d485c3
# exit 0
```

The task and unit W4a records both report `19 passed, 1 skipped`, a current
host lock, and the two `100755` entries. Those records are internally
consistent but do not exercise the linked-ancestor, hardlink, race, or
missing-hook installer-status boundaries above.

## Residual Risks After Required Rework

- A Windows-only review cannot execute a native Linux Git hook end to end; the
  next rework verification should include a real POSIX filesystem and an
  actual commit that proves the repaired hook runs.
- If installer configuration remains non-transactional, a chmod failure can
  leave `core.hooksPath` enabled before the command exits nonzero. Either roll
  back or document the partial state precisely.
- Bootstrap must remain watch-only and exit zero even after installer failure
  semantics are tightened; its explicit `FIX` output is the intended signal.

Only this skeptic report was created. Implementation, tests, task/index/claim
records, hook files, and existing verification evidence were not modified.
