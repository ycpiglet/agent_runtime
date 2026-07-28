---
title: TASK-AR-644 UNIT-001 CI Sanitization Follow-up W4a
date: 2026-07-29
status: passed
signal: pass
score: 98
verdict: READY_FOR_INDEPENDENT_W4B_RECHECK
task_id: TASK-AR-644
unit_id: UNIT-TASK-AR-644-001
verified_head: 31c382b2352fb6059c3b1dfd1c6e7bc008820a8d
verified_by: codex-root-v080-ci-followup
verifier_role: orchestrator-self-review
tags: [w4a, ci-followup, sanitization, packaging, checkpoint]
---

# TASK-AR-644 UNIT-001 CI Sanitization Follow-up W4a

## Verdict

**PASS — ready for independent W4b recheck at exact implementation HEAD
`31c382b2352fb6059c3b1dfd1c6e7bc008820a8d`.**

## Failure and Root Cause

PR #368 run `30384121064` reached the public sanitization step after the test
suite. Python 3.10 failed because the sanitizer treated the new packaged
`agents/runtime/session_checkpoints/.gitignore` directory marker as host-local
checkpoint state. Matrix fail-fast then canceled Python 3.11 after 2,355 tests
passed and canceled Python 3.12 mid-suite.

The implementation had correctly excluded checkpoint contents, but the public
sanitizer had no exact exception for the safe empty-directory marker.

## Repair

- Allow only the exact packaged path
  `agents/runtime/session_checkpoints/.gitignore`.
- Keep every other file under `agents/runtime/session_checkpoints/` forbidden.
- Add a regression that accepts the marker and rejects `latest.json`.
- Add `python -m agent_runtime.cli sanitize --root . --check` to both unit and
  task verification contracts.

## Verification

```text
PYTHONPATH=src python -m pytest tests/test_inventory_sync_sanitize.py \
  -k sanitize -q
# 121 passed

PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
# findings=0

PYTHONPATH=src python -m agent_runtime.cli publish-check --root . --check
# findings=0

python scripts/verify_wheel_dotfiles.py --check
# pass; findings=0

PYTHONPATH=src python -m pytest -q
# 2358 passed, 3 skipped, 4 pre-existing UI escape warnings
```

The official five-command unit and task verifiers also passed:

- `reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729025018.json`
- `reviews/VERIFY-2026-07-29-task-ar-644-20260729025243.json`

## Boundaries

No consumer repository, per-user settings, version, tag, package, or release
state was changed. Independent W4b must recheck the exact repair head before
the PR is updated.
