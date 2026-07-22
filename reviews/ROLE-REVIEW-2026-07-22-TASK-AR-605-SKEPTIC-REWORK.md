---
title: TASK-AR-605 High-Risk Skeptic Rework Review
date: 2026-07-22
signal: pass
task_id: TASK-AR-605
verified_head: f14de85109c61d17cc715ffc145d6943993bdc95
verified_by: codex-task-ar-605-skeptic-rework1-20260722
worker: codex-root-task-ar-605
role: skeptic
verdict: APPROVE
supersedes: reviews/ROLE-REVIEW-2026-07-22-TASK-AR-605-SKEPTIC.md
tags: [task-ar-605, skeptic, rework, high-risk, session-dashboard, generated-host]
---

# TASK-AR-605 High-Risk Skeptic Rework Review

## Verdict

**APPROVE** at exact HEAD
`f14de85109c61d17cc715ffc145d6943993bdc95`.

The three blockers from the review at `c9e07d4` are resolved. Invalid UTF-8
claim data, malformed inflight count values, and unexpected exceptions from
all three W0 fallback helpers now degrade to explicit structured notes without
escaping. A last-resort W0 boundary also contains failure of the complete
fallback. End-to-end generated-host executions returned zero and preserved
every snapshotted file byte.

## Previous REJECT Findings Rechecked

| Previous blocker | Exact rework evidence | Result |
| --- | --- | --- |
| Invalid UTF-8 claim escaped with `UnicodeDecodeError` | A copied-template clean host containing `b'{"status":"claimed","bad":"\xff"}'` returned `rc=0`, `active_claims=0`, and `claim ignored: CLAIM-bad.json (UnicodeDecodeError)`; before/after snapshots were equal | resolved |
| Wrong-typed inflight count escaped from `int()` | Clean-host payload with `claimless: "abc"` returned `rc=0`, `inflight: unavailable`, empty counts, and `invalid count payload`; snapshot unchanged | resolved |
| Unexpected helper exception escaped fallback | Injected `RuntimeError` independently into `_active_claim_count`, `_fallback_worktrees`, and `_fallback_inflight`; every `_fallback_w0_section` call returned `status=ok`, `source=fallback`, and an `unexpected RuntimeError` note | resolved |

The complete fallback was also replaced with a raising `RuntimeError` while the
repository work path failed. `build_w0_section` returned `status=error`,
`source=fallback`, and `w0 fallback unavailable: RuntimeError`. The same path
through `main()` rendered the diagnostic and returned zero.

## Malformed Count Matrix

Both the validator and actual copied-template subprocess were exercised. The
following JSON-derived count states never raised:

| Input state | W0 behavior |
| --- | --- |
| non-numeric string (`claimless: "abc"`) | unavailable, `{}`, explicit invalid-count note |
| negative (`divergent_tasks: -1`) | unavailable, `{}`, explicit invalid-count note |
| boolean (`claimless: true`) | unavailable, `{}`, explicit invalid-count note |
| fractional (`branches_with_divergence: 1.5`) | unavailable, `{}`, explicit invalid-count note |
| missing `summary` count object | unavailable, `{}`, explicit invalid-count note |
| present summary with omitted individual keys | accepted and normalized to four zero-valued integer keys |

All six copied-template runs returned zero and were byte-for-byte read-only.
An explicit inflight error payload carrying a wrong-typed summary also returned
the error note and empty counts without raising.

## Repeated Adversarial Matrix

The earlier attack matrix was repeated and extended to 32 direct/E2E checks:

- The fallback active set exactly equals `work.ACTIVE_CLAIM_STATUSES`:
  `assigned`, `claimed`, `in_progress`, `review`, `waiting_review`, and
  `working`. Six active records were counted; inactive data was excluded.
- Partial valid-UTF-8 JSON and a non-dict claim payload were ignored with
  `JSONDecodeError` and `invalid payload` notes while a valid claim remained
  counted. The actual copied-template command returned zero and was read-only.
- Worktree timeout, `OSError`, non-zero return, and valid two-worktree output
  all produced the expected bounded result.
- Inflight timeout, `OSError`, non-zero return, invalid JSON, non-dict JSON,
  explicit error data, and valid data all produced the expected result.
- Copied-template hosts with a non-zero inflight script, invalid JSON output,
  and non-dict JSON output all returned zero, emitted an explicit note, and
  preserved every file byte.
- Repository execution retained the richer `status=ok`, `source=work` path.
- A clean fallback dashboard was suppressed by `--quiet`; adding a fallback
  note caused output to be emitted. Both calls returned zero.

The live and template dashboard copies are byte-identical. Both SessionStart
dashboard hooks remain 35 seconds, exceeding the asserted 30-second serial
internal budget (two 5-second W0 subprocesses, 10-second update operation, and
10-second SCM operation). The generated-host lock is current and contains the
dashboard and inflight scripts but not repository-only `scripts/work.py`.

## Independent Commands And Results

```console
py -3.10 -m pytest tests/test_session_dashboard.py -q
# 25 passed in 8.19s

py -3.10 scripts/taskset_work_gate.py --check
# taskset-work-gate: pass; findings=0

py -3.10 scripts/work_item_classifier.py --check
# work-item-classifier: pass; findings=0

py -3.10 scripts/regen_host_lock_if_needed.py --check
# OK: tests/fixtures/host/agent_runtime.lock.json is up to date

git diff --no-index -- scripts/session_dashboard.py \
  src/agent_runtime/templates/project/scripts/session_dashboard.py
# exit 0

git diff --check 84370d7..f14de85109c61d17cc715ffc145d6943993bdc95
# exit 0
```

The current shell's unqualified `python` resolved to `C:\Python314`, which has
no pytest installation, so this independent rerun used the configured Python
3.10 runtime (`py -3.10`). This is an audit-environment resolution difference,
not a test failure. The refreshed W4a records independently preserve the
worker's literal registered-command results:

- task evidence
  `reviews/VERIFY-2026-07-22-task-ar-605-20260722224220.json`:
  `25 passed in 10.40s`, host lock current;
- unit evidence
  `reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722224206.json`:
  `25 passed in 10.32s`, host lock current.

Both records have `status=passed`, `signal=pass`, two zero-returncode commands,
and are referenced by their respective task/unit records at the verified HEAD.

## Failure-First And Rework Lineage

Commit `a96bf25ee6a01177b53cd82e0116110ff621ba8b` was exported to a
disposable directory. Running the three newly added test nodes reproduced
exactly five failures:

```text
3 failed parameters: unexpected RuntimeError from each fallback helper
1 failed test: invalid UTF-8 clean-host claim, actual return code 1
1 failed test: wrong-typed inflight count, actual return code 1
5 failed in 2.16s
```

The ancestry checks both returned zero:

```text
a96bf25 failure-first malformed-boundary tests
  -> 3fe720a malformed fallback containment fix
  -> f14de85 refreshed task + unit W4a evidence
```

This demonstrates failure-first provenance for all three original REJECT
categories, followed by the fix and refreshed evidence on the exact reviewed
HEAD.

## Residual Risk

No blocking correctness, exit-code, mutation-safety, quiet-mode, parity, lock,
timeout, or evidence issue remains in the reviewed scope. The fallback still
duplicates the active-status vocabulary because a generated host intentionally
does not ship `work.py`; the equality check protects the current vocabulary,
but a future status addition must update both copies. The hook retains five
seconds of slack above the documented internal timeout budget.

Only this rework skeptic report was created by this review. Implementation,
tests, host lock, task/index/claim records, and the prior REJECT report were not
modified.
