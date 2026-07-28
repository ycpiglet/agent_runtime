---
title: TASK-AR-644 W0 T3 Replan
date: 2026-07-29
signal: pass
score: 96
priority: P0
tags: [task-ar-644, w0, t3-replan, hooks, continuity, cross-platform]
---

# TASK-AR-644 W0 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-644-001` as one bounded implementation unit.
The registered continuity defect remains present, but the focused suite cannot
see it: the tests pass while the shipped Codex hook file invokes Windows
`.cmd` shims on POSIX, lacks `commandWindows`, and has no compact checkpoint
or rebootstrap event.

The unit will add one packaged Python hook dispatcher, make tracked Codex hooks
portable, install the equivalent Claude lifecycle hooks only through the
existing explicit owner-run installer, persist bounded derived checkpoint
state around compaction, inject a compact host/work/resume summary at
`SessionStart`, and make stale hook contracts visible in doctor and bootstrap
checks.

The baseline is Agent Runtime `main` at `8fdc8521`.

## Failure-First Evidence

The recorded focused suite passes despite the defect:

```text
python -m pytest tests/test_bootstrap_dev_env.py \
  tests/test_session_resume_check.py \
  tests/test_interrupted_run_detector.py \
  tests/test_doctor.py \
  tests/test_template_smoke.py -q
42 passed
```

The packaged `.codex/hooks.json` has zero `commandWindows` fields. Its
`SessionStart` and `UserPromptSubmit` paths include `.cmd` commands, and this
representative POSIX execution fails:

```text
bash -lc 'scripts\update_notify_hook.cmd'
bash: scriptsupdate_notify_hook.cmd: command not found
exit 127
```

The development repository hook file is also machine-specific: it contains
hard-coded `C:\Users\...\Python310\python.exe` paths and `.cmd` commands.
Neither hook file registers `PreCompact` or `PostCompact`. The shipped
`session_start_hook.py` is not wired into Codex and still implements a
project-specific scheduling/collaboration cockpit rather than a generic
consumer continuity contract. Doctor nevertheless reports a synchronized
host as healthy, which is a false negative.

## Verified Client Contract

Current official client documentation confirms the required lifecycle surface:

- Codex project hooks live in `.codex/hooks.json` for trusted repositories,
  support `commandWindows`, and expose `SessionStart`, `PreCompact`, and
  `PostCompact`.
- Codex starts all matching command hooks concurrently, so ordered continuity
  work must live behind one dispatcher rather than several sibling hooks.
- `SessionStart` can return `hookSpecificOutput.additionalContext`; plain
  `PreCompact` and `PostCompact` stdout is not context injection.
- Claude Code supports the same three lifecycle events, including manual and
  automatic compaction matchers.

Sources:

- <https://learn.chatgpt.com/docs/hooks>
- <https://code.claude.com/docs/en/hooks>

Hook trust is client-owned state. Runtime doctor can validate tracked
configuration but cannot claim that Codex has reviewed or trusted a changed
hook file; the result must include the manual `/hooks` review reminder.

## Portable Dispatcher Contract

Add `agent_runtime.hook_runtime` as the only command surface referenced by
tracked hooks:

- POSIX: `python3 -m agent_runtime.hook_runtime <mode>`
- Windows: `py -3 -m agent_runtime.hook_runtime <mode>`

The dispatcher reads hook JSON from stdin, resolves the Git root from the
event `cwd` with a bounded fallback, and invokes only fixed allowlisted host
scripts through `sys.executable`. It forwards the original input and preserves
blocking semantics for prompt and stop gates. Advisory start and compact
modes fail open with valid hook JSON and a visible diagnostic.

Required modes are:

- `session-start`
- `pre-compact`
- `post-compact`
- `prompt-submit`
- `stop-owner`
- `stop-closure`
- development-repository-only `stop-dirty` and `posttool-owner-doc`

## Continuity Contract

`session_start_hook.py` becomes an exact root/template mirror and a generic,
bounded re-entry point:

1. read the client event payload and identify the host root;
2. run baseline and claim-reaper work in deterministic order;
3. collect dashboard, interruption, resume, and a minimal legacy compound
   lookup with bounded time and output;
4. include host context presence/path, active work, resume/pointer state, and
   compact checkpoint state in `additionalContext`;
5. always exit zero because it is an advisory start hook.

`session_compact_hook.py` becomes an exact root/template mirror:

- `pre-compact` atomically writes a bounded derived JSON checkpoint under
  `agents/runtime/session_checkpoints/`;
- the checkpoint contains only session identity, pointer/task/claim and Git
  state, never prompt, transcript, or secret content;
- `post-compact` records a fresh rebootstrap marker;
- neither phase commits, pushes, edits canonical work items, or blocks the
  client;
- the next `SessionStart` with source `compact` reads the checkpoint and
  performs the actual context reinjection.

Compound lookup in this unit is deliberately minimal and read-only.
TASK-AR-645 owns task-linked compound and scribe redesign.

## Install and Doctor Contract

The template `install_hooks.py` remains an explicit owner-run operation. It may
register `SessionStart`, `PreCompact`, `PostCompact`, and
`UserPromptSubmit` in a caller-selected Claude settings fixture using the
current interpreter, but this unit must not edit real per-user settings.

Doctor and bootstrap checks must report:

- missing or malformed `.codex/hooks.json`;
- absent required events or dispatcher modes;
- absent `commandWindows`;
- stale `.cmd`, bare relative script, or hard-coded drive commands;
- missing dispatcher target scripts;
- a Codex `/hooks` trust-review reminder when the tracked contract is valid.

## Scope Amendment

The registered targets remain primary, with these necessary shared surfaces
added:

- `src/agent_runtime/hook_runtime.py`
- root/template mirrors of `session_start_hook.py`,
  `session_compact_hook.py`, and `session_resume_check.py`
- root tracked `.codex/hooks.json`
- `scripts/bootstrap_dev_env.py`
- packaged runtime asset registry and direct hook references in template
  `AGENTS.md` / `CLAUDE.md`
- focused lifecycle, doctor, bootstrap, install, template, and packaging tests

This is not authorization for consumer-repository mutation, automatic
per-user settings edits, prompt/transcript persistence, automatic Git commits,
TASK-AR-645 compound/scribe redesign, TASK-AR-646 model routing, TASK-AR-647
Allimbot native events, release, version bump, tag, publish, or deployment.

## Verification

- `python -m pytest tests/test_session_continuity_hooks.py tests/test_bootstrap_dev_env.py tests/test_session_resume_check.py tests/test_interrupted_run_detector.py tests/test_doctor.py tests/test_template_smoke.py -q`
- affected hook, dashboard, update-notify, stop-governance, Allimbot, and wheel
  packaging tests
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`
- `python -m pytest -q`
- root/template mirror checks for shared continuity scripts
- simulated Linux and Windows command selection plus manual/automatic compact
  and restart logs
- independent W4b against the exact implementation head

## W2 Decision

Dispatch one `worker_standard` implementation agent after this review and the
refreshed T3 assumption snapshot are committed. Reserve W4b for a different
agent instance and require adversarial POSIX, Windows-command, malformed-hook,
missing-script, compact-resume, bounded-output, and clean-host verification
before claim release.
