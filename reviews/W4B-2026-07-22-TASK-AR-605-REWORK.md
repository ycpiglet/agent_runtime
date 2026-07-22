---
title: TASK-AR-605 Rework Independent W4b Verification
date: 2026-07-22
signal: pass
verdict: APPROVE
task_id: TASK-AR-605
verified_head: f14de85109c61d17cc715ffc145d6943993bdc95
verified_by: codex-task-ar-605-independent-auditor-rework-20260722
tags: [w4b, independent-verification, rework, session-dashboard, generated-host, github-294]
---

# TASK-AR-605 Rework Independent W4b Verification

## Verdict

**APPROVE** at exact HEAD
`f14de85109c61d17cc715ffc145d6943993bdc95`.

The initial W4b approval at `c9e07d4` and the subsequent skeptic REJECT remain
historical evidence for that old HEAD. This rework independently resolves all
three skeptic findings: invalid UTF-8 claim input, wrong-typed inflight counts,
and unexpected fallback-helper exceptions. A last-resort W0 containment layer
also preserves structured output and main exit 0 if the fallback itself fails.

## Validation Results

| Metric | Threshold | Measured result | Status |
| --- | --- | --- | --- |
| Exact source state | requested HEAD and clean tree | `f14de851...`; clean before report | pass |
| Rework focused suite | all 25 tests pass | `25 passed in 10.65s` | pass |
| Host lock | generated-host lock current | check returned zero | pass |
| Invalid UTF-8 clean host | structured note, rc0, read-only | `UnicodeDecodeError` note; rc 0; 37 file hashes and Git clean state unchanged | pass |
| Wrong-typed inflight clean host | invalid-count note, rc0, read-only | empty counts plus `invalid count payload`; rc 0; 32 file hashes and Git clean state unchanged | pass |
| Unexpected helper exceptions | all three components contained | 3/3 RuntimeError injections returned structured notes; no message leakage | pass |
| Last-resort fallback | structured error object and main exit 0 | status error, source fallback, RuntimeError class note, rc 0 | pass |
| Repository behavior | retain richer work API path | source work, status ok, claims/worktrees/inflight present, notes empty | pass |
| Live/template parity | dashboard copies byte-identical | exact byte comparison passed | pass |
| Failure-first provenance | all new skeptic regressions fail before fix | commit `a96bf25`: 5 failed | pass |
| W4a evidence | task and unit reports each record 25 tests and lock | 2/2 passed; implementation `3fe720a` is final HEAD's direct parent | pass |

## Registered Commands

```console
python -m pytest tests/test_session_dashboard.py -q
# 25 passed in 10.65s

python scripts/regen_host_lock_if_needed.py --check
# OK: tests/fixtures/host/agent_runtime.lock.json is up to date

git diff --no-index --exit-code -- scripts/session_dashboard.py src/agent_runtime/templates/project/scripts/session_dashboard.py
# exit 0; byte-identical
```

## Clean-Host Adversarial Runs

Two disposable, fully committed Git hosts contained the template dashboard and
no `scripts/work.py`. The actual template CLI was executed with JSON output and
a bounded SCM timeout.

### Invalid UTF-8 claim

The host contained a claim with byte `0xff` in its JSON content. The command
returned rc 0 and W0 reported `status=ok`, `source=fallback`, one worktree, zero
active claims, and an explicit `UnicodeDecodeError` claim-ignore note. The
shipped inflight subprocess also failed on that malformed claim and was exposed
as a second nonzero-subprocess note instead of escaping. All 37 file hashes and
Git clean state were identical before and after execution.

### Wrong-typed inflight count

The host inflight script returned valid JSON with `claimless: "abc"`. The
dashboard returned rc 0 with `status=ok`, `source=fallback`, one worktree,
`inflight: unavailable`, empty inflight counts, and an explicit
`invalid count payload` note. All 32 file hashes and Git clean state were
unchanged.

## Helper Exception Containment

Each fallback component was independently replaced with a
`RuntimeError("SHOULD-NOT-LEAK")`, while the other components returned healthy
data:

| Component | Result |
| --- | --- |
| `_active_claim_count` | status ok; `claim scan unexpected RuntimeError` |
| `_fallback_worktrees` | status ok; worktrees null; `worktree scan unexpected RuntimeError` |
| `_fallback_inflight` | status ok; inflight unavailable; `inflight scan unexpected RuntimeError` |

All three returned structured W0 data, and none exposed the injected exception
message. Only the exception class was retained in the note.

For the final containment boundary, both the richer work path and
`_fallback_w0_section` were forced to raise. `build_w0_section` returned a
controlled object with `status=error`, `source=fallback`, empty counts, and
`w0 fallback unavailable: RuntimeError`. Feeding that object through the real
JSON main path still returned rc 0 without leaking the injected message.

## Repository Path

The real CLI was independently run against the final TASK-AR-605 worktree. It
returned rc 0 in 0.969 seconds with `source=work`, `status=ok`, one active claim,
two worktrees, zero divergent tasks, and no notes. Git status remained clean.
This confirms the new containment does not replace the richer repository path.

## Failure-First Reproduction

Commit `a96bf25` was exported to a disposable directory. The three new test
functions were executed, collecting five cases because helper containment is
parameterized across three components:

```console
python -m pytest \
  tests/test_session_dashboard.py::test_w0_fallback_contains_unexpected_component_exceptions \
  tests/test_session_dashboard.py::test_clean_template_invalid_utf8_claim_degrades_read_only \
  tests/test_session_dashboard.py::test_clean_template_wrong_typed_inflight_counts_degrade_read_only -q
# 5 failed in 1.65s
```

The three RuntimeErrors escaped, the invalid UTF-8 host exited 1 with
`UnicodeDecodeError`, and the wrong-count host exited 1 with `ValueError`.
This exactly reproduces the skeptic findings. The disposable export was
removed afterward.

## W4a Evidence And Lineage

The latest task and unit evidence files were independently parsed:

- `reviews/VERIFY-2026-07-22-task-ar-605-20260722224220.json`
- `reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722224206.json`

Both contain `status: passed`, two zero-returncode commands, `25 passed`, and a
current host-lock result. Git ancestry confirms rework implementation HEAD
`3fe720ac12007681241077d66845355301cd36e1` is the direct parent of final
evidence HEAD `f14de85109c61d17cc715ffc145d6943993bdc95`.

## Findings

- No unresolved correctness, malformed-input, exception-containment,
  mutation-safety, parity, scope, or evidence finding remains at the verified
  HEAD.
- The fix remains bounded to the root/template dashboard pair, focused tests,
  host lock, and refreshed task/unit verification evidence.
- Inflight counts reject booleans, negative values, fractional floats, and
  non-coercible or overflowing values before summary construction.

## Residual Risks

- The final containment catches ordinary `Exception` subclasses, not process
  control signals such as `KeyboardInterrupt` or `SystemExit`. Those are not
  ordinary malformed host state and remain outside this fallback contract.
- Integer-like string count values are intentionally normalized with `int()`;
  future schema tightening may prefer JSON numbers only.
- This independent W4b ran the requested focused suite and direct adversarial
  executions rather than the full package suite. Every modified surface and
  all three skeptic failure paths were exercised directly.
