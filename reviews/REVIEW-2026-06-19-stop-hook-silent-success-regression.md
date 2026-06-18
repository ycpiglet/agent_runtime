---
title: Stop Hook Silent Success Regression
date: 2026-06-19
signal: pass
score: 100
tags: [stop-hook, hooks, closeout, regression]
---

# Stop Hook Silent Success Regression

## Bottom Line

The three registered Stop hooks were still emitting `{}` on approve/bypass
paths even though the current Codex Stop contract for this repo is block-only
JSON: non-blocking paths must produce zero stdout, and block paths emit the
JSON envelope.

## Cause

- `scripts/stop_hook_owner_governance.py`
- `scripts/stop_hook_dirty_intake.py`
- `scripts/stop_hook_closure_gate.py`

Each wrapper returned exit `0` but printed `{}` for successful or bypassed Stop
checks. That shape is valid JSON syntax, but it is not the accepted Stop hook
payload for this runtime, so Codex displayed `hook returned invalid stop hook
JSON output`.

The active dirty/owner blocks seen in the same session had a separate cause:
`TASK-AR-594` claim metadata and a UI/UX report were not yet preserved. Those
files were committed first in `4516a65` so the hook-output regression could be
verified independently.

## Fix

- Keep block paths unchanged: emit `{"decision":"block", ...}`.
- Make approve, bypass, and best-effort approve paths silent.
- Mirror the owner-governance and closure wrapper changes into the host-project
  template scripts.
- Update regression tests to assert zero-byte stdout for question-only and
  best-effort approve paths.

## Verification

- `python -m pytest tests/test_stop_hook_owner_governance.py tests/test_stop_hook_session_scope.py tests/test_closure_gate.py tests/test_dirty_intake.py -q`
  - Result: `42 passed`.
- `python -m py_compile scripts/stop_hook_owner_governance.py scripts/stop_hook_dirty_intake.py scripts/stop_hook_closure_gate.py src/agent_runtime/templates/project/scripts/stop_hook_owner_governance.py src/agent_runtime/templates/project/scripts/stop_hook_closure_gate.py`
  - Result: pass.
- Direct question-only Stop hook run:
  - owner stdout length: `0`
  - dirty stdout length: `0`
  - closure stdout length: `0`
- Direct dirty-intake block run:
  - Result: valid Stop JSON with `decision: block`.
