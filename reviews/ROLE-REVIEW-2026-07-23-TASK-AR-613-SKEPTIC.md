---
title: TASK-AR-613 Skeptic and Adversarial W4b
date: 2026-07-23
signal: fail
score: 62
task_id: TASK-AR-613
verified_head: 86f425c45edfc6210497f2bcd7a1cf4fb3a5c23c
verified_by: codex-task-ar-613-skeptic-20260723
worker: codex-root-task-ar-613
role: skeptic
verdict: REWORK
tags: [task-ar-613, skeptic, adversarial, release-cadence, release-auto, fail-open, redaction]
---

# TASK-AR-613 Skeptic and Adversarial W4b

## Findings

### [P0] Partial query failure remains fail-open when another metric triggers

At exact HEAD `86f425c45edfc6210497f2bcd7a1cf4fb3a5c23c`,
`build_report()` only converts query errors into `status=error` when the report
is not triggered. If another successful query crosses a threshold, the partial
report remains `status=watch` even though `_QUERY_ERRORS` proves that part of
the repository could not be evaluated.

An adversarial real-Git fixture used a valid baseline tag and 40 post-tag
commits. `describe`, subject log, `rev-list`, tag-time log, and breaking-change
log all returned real answers. Only the two later `diff` commands returned
unexpected rc 128 for all three attempts. The exact-head result was:

```text
cadence.status=watch
cadence.triggered=true
cadence.reason=<missing>
cadence.git_query_errors=2
```

Passing that same cadence module to release-auto produced:

```text
release_auto.result=executed
release_auto.mutated=false  # test default is dry-run
release_auto.git_query_errors=0
```

Thus release-auto did not merely turn the error into clean `not-triggered`; it
advanced to the executed path and discarded the query errors. In a non-dry-run
invocation, the same decision can reach tag/push execution from a partial view.
Failures in subject log, breaking log, tag-time log, or either diff can likewise
coexist with a commit/feature/day trigger from another successful metric and
can distort bump criticality.

Required rework: any exhausted cadence query must make the aggregate report
unevaluated regardless of other successful metrics. Set `status=error`,
`triggered=false`, clear finding/recommendations, preserve all structured query
errors, and make release-auto reject `status=error` independently of the
`triggered` flag. Add parameterized partial-failure tests for subject log,
rev-list, tag-time log, breaking log, and both diff queries where another
metric would otherwise trigger.

### [P1] The no-tag classifier accepts conflicting and wrong-status failures

`_expected_no_tag_result()` correctly restricts the command tuple to
`git describe --tags --abbrev=0`, but it does not require Git's no-tag return
code and accepts a broad marker found anywhere in concatenated stderr and
stdout. Two exact-head counterexamples were classified as quiet no-tag after
one call with no query-error evidence:

```text
rc=1
stderr="fatal: No names found; permission denied"
=> pass / no-baseline-tag

rc=128
stdout="No tags can describe placeholder"
stderr="fatal: detected dubious ownership"
=> pass / no-baseline-tag
```

The command boundary itself works: the same marker from `git rev-list`
receives three retries and an exhausted error. The known Git stderr
`fatal: No names found, cannot describe anything.` also remains a one-call
quiet result. The defect is that marker presence overrides incompatible status
or diagnostics on the describe command.

Required rework: require the expected no-tag status and a narrowly parsed,
non-conflicting stderr signature; do not use stdout as an alternative proof.
Unknown/localized/combined diagnostics should fail loud rather than quiet.
Add variants for the known Git messages, wrong return codes, extra fatal lines,
stdout-only markers, and the non-describe command boundary.

### [P1] Diagnostic redaction leaks multi-token and OSError secrets

URL userinfo, single-token `password`, `passwd`, `token`, `access-token`, and
`secret` assignments are redacted, and the sanitized payload is capped at 500
characters. However, `_SENSITIVE_ASSIGNMENT_RE` consumes only one
whitespace-delimited token. Exact-head probes produced:

```text
Authorization: Bearer auth-secret
=> Authorization=[REDACTED] auth-secret

token="two word-secret"
=> token=[REDACTED] word-secret"
```

In addition, exhausted `OSError` diagnostics bypass
`_sanitize_git_diagnostic()` entirely. This exact-head error was stored
verbatim after three attempts:

```text
OSError: authorization: Bearer os-secret https://u:p@example.invalid/x
```

These values flow into cadence output and release-auto human/JSON evidence.
The implemented 500-character cap applies only to the sanitized diagnostic
payload; the surrounding `exit N: ` prefix makes the complete `error` field
slightly longer, which is acceptable if documented but should be tested
explicitly.

Required rework: redact the entire sensitive assignment through the diagnostic
line boundary, including quoted or bearer/basic multi-token values; sanitize
`OSError` text and any other recorded exception/command field through the same
bounded function. Add stderr and stdout cases for every named key, mixed-case
authorization schemes, quoted whitespace, multiple secrets per line, multiple
URLs, and exact length bounds.

### [P2] Mixed retry provenance can retain a stale return code

`last_returncode` is not reset when an `OSError` follows an earlier non-zero
process result. The exact sequence rc 7, `OSError`, `OSError` exhausted after
three attempts with this contradictory record:

```json
{
  "error": "OSError: spawn token=final-secret",
  "returncode": 7
}
```

Pure positive, negative, and OSError exhaustion each use three attempts;
one failure followed by success recovers on attempt two without a stored
error. The retry counts are correct, but mixed-type evidence does not truthfully
describe the final failure.

Required rework: reset return-code provenance on exceptions and preferably
record failure kind and attempt count explicitly. Add mixed-order sequences
for positive/negative return codes and OSError.

## Verdict

**REWORK** at exact HEAD
`86f425c45edfc6210497f2bcd7a1cf4fb3a5c23c`.

The primary task path retries a simple unexpected non-zero result and correctly
routes an all-query failure to release-auto trigger-error. Those happy-path
fixes do not close partial-query fail-open behavior, overly broad no-tag
classification, or diagnostic confidentiality. The P0 release decision
counterexample alone blocks approval.

## Passing Retry and Classification Boundaries

The following boundaries behaved as intended:

| Case | Attempts | Exhausted record / recovery |
| --- | ---: | --- |
| unexpected positive rc | 3 | stores final positive return code and bounded sanitized diagnostic |
| negative rc | 3 | stores negative return code and signal diagnostic |
| OSError only | 3 | stores returncode null, but exception text is unsanitized |
| any one failure then success | 2 | returns successful stdout and stores no query error |
| known describe no-tag response | 1 | quiet `no-baseline-tag`, no query error |
| no-tag text on non-describe command | 3 | exhausted query error |

The failure-first commit
`524a75ab` was exported to a disposable directory and the three new regressions
were run against the pre-fix implementation. All three failed causally:

```text
test_transient_nonzero_git_failure_recovers_without_error       FAILED
test_exhausted_unexpected_nonzero_git_failure_is_error          FAILED
test_unexpected_nonzero_cadence_query_halts_release_auto_loud   FAILED
3 failed in 23.29s
```

## Focused, Parity, Lock, and W4a Evidence

The registered focused suite passes its current assertions:

```text
python -m pytest tests/test_release_cadence_trigger.py \
  tests/test_release_auto_noncritical.py -q
58 passed
```

Those assertions do not include the findings above. Passing the suite therefore
does not change the REWORK verdict.

At the exact reviewed commit:

- Root and template `release_cadence_trigger.py` have the same Git blob
  `e904cca15314654be634bbbd56f85659ffdc939b`.
- An isolated archive of the exact commit passed
  `python scripts/regen_host_lock_if_needed.py --check`.
- The exact host-lock blob is
  `a710edd382299fb10ae6ee73952cd26e7009d67b`.
- Cadence thresholds remain commits 40, features 5, and days 14.
- Root/template parity and host lock are therefore genuine passing evidence,
  not causes of this rejection.

The latest W4a JSON records parse correctly, point to their canonical task/unit
paths, identify worker `codex-root-task-ar-613`, and contain three zero-return
commands with empty stderr:

- Task evidence
  `VERIFY-2026-07-23-task-ar-613-20260723014533.json`: focused `58 passed in
  256.39s`, host lock current, taskset gate findings 0.
- Unit evidence
  `VERIFY-2026-07-23-unit-task-ar-613-001-20260723015000.json`: focused
  `58 passed in 253.33s`, host lock current, taskset gate findings 0.

The W4a records truthfully report the commands they ran, but their test matrix
is incomplete against the adversarial boundaries above.

## Review Scope and Mutation Boundary

This report preserves the first-pass REWORK finding history for exact HEAD
`86f425c4`. Only this report was created by the reviewer. Production files,
tests, evidence, task/unit records, runtime state, and `reviews/INDEX.md` were
not modified by this review.
