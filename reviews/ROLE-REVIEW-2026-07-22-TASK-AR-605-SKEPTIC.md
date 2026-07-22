---
title: TASK-AR-605 High-Risk Skeptic Review
date: 2026-07-22
signal: fail
task_id: TASK-AR-605
verified_head: c9e07d4e16721d5ab119cd6e8e6ac3a1f1c5091a
verified_by: codex-task-ar-605-skeptic-20260722
worker: codex-root-task-ar-605
role: skeptic
verdict: REJECT
tags: [task-ar-605, skeptic, high-risk, session-dashboard, generated-host]
---

# TASK-AR-605 High-Risk Skeptic Review

## Verdict

**REJECT** at exact HEAD
`c9e07d4e16721d5ab119cd6e8e6ac3a1f1c5091a`.

The normal clean-host fallback, parity, timeout budget, and read-only behavior
are correct, but three malformed/error boundaries can still escape the W0
fallback and terminate `session_dashboard.py` with exit code 1. This violates
the unit acceptance that fallback failures degrade explicitly and the module's
always-exit-0 contract.

## Blocking Findings

### [P1] Invalid UTF-8 claim JSON escapes the fallback

`_active_claim_count` catches `OSError` and `json.JSONDecodeError`, but
`Path.read_text(encoding="utf-8")` can raise `UnicodeDecodeError`. A clean host
containing this claim file was executed end to end:

```text
agents/runtime/task_claims/CLAIM-bad.json =
  b'{"status":"claimed","bad":"\xff"}'
```

Observed:

```text
returncode=1
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff ...
```

The same snapshot remained byte-for-byte unchanged, so the read-only boundary
held, but the SessionStart hook would be failed/preempted instead of receiving
an explicit note.

### [P1] Structurally valid inflight JSON can raise during count coercion

The fallback validates that the inflight payload and `summary` are dicts, but
then performs an unguarded `int()` conversion for `claimless`. A shipped-script
stub returning the following valid JSON reproduced an end-to-end failure:

```json
{"summary":{"divergent_tasks":0,"branches_with_divergence":0,"claimless":"abc"}}
```

Observed:

```text
returncode=1
ValueError: invalid literal for int() with base 10: 'abc'
```

Invalid JSON text and a non-dict JSON payload degrade correctly; the typed
count boundary does not.

### [P1] Unexpected fallback exceptions are not contained

`_fallback_worktrees` and `_fallback_inflight` catch only timeout and OS-level
exceptions. Injecting `RuntimeError` from either subprocess call escapes. An
exception raised by `_active_claim_count` also escapes `_fallback_w0_section`.
The richer root path is wrapped, but exceptions raised while evaluating the
fallback from that handler are not caught by the same `except` block.

The module promises that every section “NEVER raises”; the fallback needs a
last-resort containment boundary that returns structured notes instead.

## Passing Adversarial Boundaries

- A clean generated host contains no `scripts/work.py`; neither the template
  tree nor host lock contains it.
- Normal clean-host execution returns `source: fallback`, counts active claims
  and worktrees, returns inflight counts, exits 0, and changes no file bytes.
- Partial valid-UTF-8 JSON, malformed JSON syntax, and non-dict claim payloads
  are ignored with explicit notes while valid active claims remain counted.
- The fallback active set exactly matches `work.ACTIVE_CLAIM_STATUSES`:
  `assigned`, `claimed`, `in_progress`, `review`, `waiting_review`, `working`.
- Non-git roots, a missing inflight script, subprocess non-zero exit, ordinary
  invalid JSON, a non-dict inflight payload, and explicit inflight error data
  degrade to notes without raising.
- Worktree/inflight `TimeoutExpired` and `OSError` degrade to notes.
- Broken and invalid-JSON inflight scripts exited 0 end to end and remained
  read-only.
- Repository execution preserved the richer `source: work` path.
- Live and template dashboard files are byte-identical; the host lock is
  current.
- Both dashboard hooks are 35 seconds. This exceeds the documented worst-case
  serial internal budget of 30 seconds: fallback W0 `5s * 2`, update `10s`,
  and SCM `10s`.
- `--quiet` suppresses a clean dashboard and still prints when notes, active
  work, updates, counts, timeout, or section errors require attention.

## Independent Commands And Results

- `python -m pytest tests/test_session_dashboard.py -q`
  -> `20 passed in 7.69s`
- `python scripts/taskset_work_gate.py --check`
  -> pass, findings 0
- `python scripts/work_item_classifier.py --check`
  -> pass, findings 0
- `python scripts/regen_host_lock_if_needed.py --check`
  -> pass, host lock current
- `git diff --no-index --exit-code -- scripts/session_dashboard.py src/agent_runtime/templates/project/scripts/session_dashboard.py`
  -> pass
- `git diff --check 84370d7..c9e07d4`
  -> pass

An additional direct helper matrix covered active/inactive claims, malformed
claim files, git timeout/OS error/non-zero/valid output, and inflight
timeout/OS error/non-zero/invalid JSON/non-dict/error/valid output. Disposable
clean-host subprocesses then verified the actual return code and before/after
file hashes for the failure cases above.

## Failure-First And W4a Ancestry

Commit `8d4a5941e78c238d74f258b32a201b51768882cf` was independently extracted to a
disposable directory. Its clean-template regression failed as expected because
W0 returned `status: error` instead of `status: ok` when `work.py` was absent.

The implementation/evidence lineage is linear:

```text
8d4a594 failure-first clean-host test
  -> c4fa181 clean-host fallback implementation
  -> c9e07d4 unit W4a evidence
```

`reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722222914.json` records 20
passing focused tests and a current host lock. The task record itself does not
yet contain task-level W4a metadata or evidence; only the unit is verified.

## Required Rework

- Treat `UnicodeError` while reading claim records as a malformed-file note.
- Validate/coerce all inflight count fields defensively; type/value failures
  must return an invalid-payload note.
- Add a final exception boundary around each fallback component or the complete
  `_fallback_w0_section`, preserving explicit ASCII-safe diagnostics and exit 0.
- Add end-to-end clean-template regressions for invalid UTF-8 claims,
  wrong-typed inflight counts, and unexpected helper exceptions.
- Refresh W4a on the corrected exact HEAD, including task-level evidence if the
  task is being closed, then repeat independent and skeptic review.

No implementation, test, index, or claim file was modified during this review.
