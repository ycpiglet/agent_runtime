---
type: w4b-independent-verification
title: TASK-AR-598 rework independent verification
task_id: TASK-AR-598
unit_id: UNIT-TASK-AR-598-001
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
claim_id: CLAIM-20260719-122612-task-ar-598-session-resume
status: approved
signal: pass
worker_agent_id: codex-root-task-ar-598
verifier_agent_id: codex-independent-verifier-task-ar-598-rework-20260719
verifier_role: independent-w4b
branch: codex/task-ar-598-session-resume
base_commit: fc55fc54f1571be47e9914e7960025932edad613
report_only_commit: d020ee63c8a736493710a243d0c7957426d9ff75
implementation_commit: da1a180b17e24bb1bda90214df8d4a3c0d57ea13
w4a_commit: cf8cedd4052ae0bbbf8c22d0e5bd39095e0315b0
w4a_evidence: reviews/VERIFY-2026-07-19-unit-task-ar-598-001-20260719124202.json
supersedes: reviews/W4B-2026-07-19-TASK-AR-598.md
verified_at: 2026-07-19T12:47:51+09:00
findings: []
---

# W4b Independent Verification — TASK-AR-598 Rework

## Verdict

**APPROVE final product state `da1a180`.** The reworked session resume check is
filesystem-report-only, rejects unsafe message identifiers before constructing
or reading a claim path, preserves JSON and strict-mode behavior on unexpected
exceptions, and retains the required `SessionStart` integration.

This report supersedes `reviews/W4B-2026-07-19-TASK-AR-598.md`. That earlier
approval covered implementation `3066f3c`; a skeptic subsequently reproduced
real path-traversal deletion through its mutating recovery path. It must not be
used as release evidence. Commit `d020ee6` removed the mutating CLI, and final
hardening commit `da1a180` additionally bounded claim reads by rejecting unsafe
message IDs.

No open security or release-blocking finding remains in the final product
state. W4 independence is preserved: W4a was recorded by
`codex-root-task-ar-598`; this W4b was performed by
`codex-independent-verifier-task-ar-598-rework-20260719`.

## Threat model and final controls

The protected assets are files outside `agents/runtime/claims`, plus all
runtime state that a `SessionStart` hook must only observe. The untrusted input
is message frontmatter, especially its `id`, as well as arbitrary CLI input and
malformed runtime files.

- `--fix`, the checkpoint subcommand, `_apply_fix`, `append_checkpoint`, and
  the call to `message_queue.recover_stale_claim` are absent from the final
  script.
- The CLI parser exposes only audit configuration and `--strict`; unknown
  mutation-shaped input is rejected by `argparse` before audit execution.
- `_SAFE_MESSAGE_ID_RE` requires `MSG-[A-Za-z0-9._-]+` as a full match. Both
  slash types, drive prefixes, colons, and other traversal syntax are excluded.
- An unsafe ID is reported as `invalid-message-id` and control continues before
  any candidate claim path existence check or `_read_claim` call.
- The default audit contains no filesystem write/delete primitives. Its only
  state-changing operation is stdout/stderr encoding configuration, which does
  not touch repository state.

## Measured acceptance gates

| Metric | Threshold | Measured value | Status |
|---|---:|---:|---|
| Removed mutation interfaces present in source | 0 | 0/5 tokens | PASS |
| Default audit return code | `0` | `0` | PASS |
| Temp-tree content hash changes after default audit | 0 | 0 | PASS |
| Unknown mutation-shaped CLI return codes | all `2` | `[2, 2, 2]` | PASS |
| Temp-tree content hash changes after unknown CLI calls | 0 | 0 | PASS |
| Claim reads for traversal message ID | 0 | 0 | PASS |
| Traversal finding reason | `invalid-message-id` | `invalid-message-id` | PASS |
| External sentinel deletion or byte change | none | exists; SHA-256 unchanged | PASS |
| Unexpected exception, default JSON | parseable, rc `0` | parseable, rc `0` | PASS |
| Unexpected exception, strict JSON | parseable, rc `1` | parseable, rc `1` | PASS |
| Clean report, strict JSON | `clean: true`, rc `0` | `clean: true`, rc `0` | PASS |
| Exact `SessionStart` order | 5/5 | 5/5 | PASS |
| Targeted security/contract tests | 4/4 | 4 passed | PASS |
| Focused plus atomic suite | 12/12 | 12 passed | PASS |
| Malformed actual `*.claim` fixture | pass | pass | PASS |
| Host fixture lock | current | current | PASS |
| Taskset work gate findings | 0 | 0 | PASS |
| Diff whitespace errors | 0 | 0 | PASS |

## Independent attack probe

The verifier created an isolated host tree containing:

- a claimed inbox message with ID
  `MSG-x/../../../outside/VICTIM`;
- an external-to-claims sentinel at `agents/outside/VICTIM.claim`;
- a binary marker; and
- empty runtime claims state.

The complete directory/file/content SHA-256 was measured before and after the
default JSON audit and after three mutation-shaped invocations (`--fix`, the
old `checkpoint` form, and `--repair`). The script module was then loaded with
`message_queue._read_claim` instrumented to count claim reads.

```json
{
  "product_commit": "cf8cedd4052ae0bbbf8c22d0e5bd39095e0315b0",
  "default_rc": 0,
  "default_json_parseable": true,
  "default_reports_invalid_message_id": true,
  "malformed_claim_warning": true,
  "tree_hash_unchanged": true,
  "file_count_before": 4,
  "file_count_after": 4,
  "unknown_mutation_rcs": [2, 2, 2],
  "victim_hash_unchanged": true,
  "claim_read_calls_for_malicious_id": 0,
  "malicious_reason": "invalid-message-id",
  "exception_default_rc": 0,
  "exception_strict_rc": 1,
  "exception_default_json_parseable": true,
  "exception_strict_json_parseable": true,
  "clean_strict_rc": 0,
  "clean_strict_clean": true,
  "hook_exact_order": true,
  "hook_count": 5
}
```

The source-token check also found none of `--fix`, `append_checkpoint`,
`_apply_fix`, `recover_stale_claim`, or `add_subparsers` in the final script.

## Repository verification evidence

Targeted cases covered malformed real claims, removed mutation interfaces,
unexpected JSON exceptions, and traversal IDs:

```text
py -3.10 -m pytest \
  tests/test_session_resume_check.py::test_malformed_inputs_never_break_session_start \
  tests/test_session_resume_check.py::test_mutating_recovery_interfaces_are_not_exposed \
  tests/test_session_resume_check.py::test_unexpected_failure_preserves_json_and_strict_contract \
  tests/test_session_resume_check.py::test_claim_scan_rejects_path_traversal_message_id \
  -q -p no:cacheprovider
4 passed in 0.73s
```

Full focused regression, including nine session-resume tests and three atomic
orchestrator-write tests:

```text
py -3.10 -m pytest tests/test_session_resume_check.py tests/test_orchestrator_atomic_writes.py -q -p no:cacheprovider
12 passed in 1.53s

py -3.10 scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

py -3.10 scripts/taskset_work_gate.py --check --task-set-id TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
taskset-work-gate: pass; findings=0

git diff --check fc55fc5..cf8cedd
PASS (no output)
```

W4a evidence
`reviews/VERIFY-2026-07-19-unit-task-ar-598-001-20260719124202.json` records the
same 12-test suite and current lock against final hardening `da1a180`.

## Required hook order

1. `scripts\\update_notify_hook.cmd`
2. `python scripts/session_dashboard.py --root .`
3. `python scripts/claim_reaper_hook.py --root .`
4. `python scripts/interrupted_run_detector.py --root .`
5. `python scripts/session_resume_check.py --root .`

## Residual risk

The safe-ID boundary is local to this auditor; `message_queue._msg_id_from_path`
still returns frontmatter IDs without validation. This is acceptable here
because the auditor validates immediately and exposes no recovery mutation,
but future code must not bypass `_SAFE_MESSAGE_ID_RE` before deriving a claim
path. The regression test that forbids `_read_claim` for a traversal ID should
remain a release gate.

The verifier made no code, release, claim, board, index, or registry changes.
This REWORK evidence file is the only verifier-authored change.
