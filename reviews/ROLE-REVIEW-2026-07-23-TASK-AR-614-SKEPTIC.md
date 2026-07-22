---
title: TASK-AR-614 Skeptic and Adversarial W4b
date: 2026-07-23
signal: pass
score: 98
task_id: TASK-AR-614
verified_head: 92ac39c937fe77138b40b58fd33ca5b6967f0e79
verified_by: codex-task-ar-614-skeptic-20260723
worker: codex-root-task-ar-614
role: skeptic
verdict: APPROVE
tags: [task-ar-614, skeptic, adversarial, self-eval, git-query, data-integrity]
---

# TASK-AR-614 Skeptic and Adversarial W4b

## Findings

No blocking or non-blocking implementation finding was reproduced at exact
HEAD `92ac39c937fe77138b40b58fd33ca5b6967f0e79`.

## Verdict

**APPROVE** at exact HEAD
`92ac39c937fe77138b40b58fd33ca5b6967f0e79`.

Every exhausted direct Git query now invalidates the aggregate self-eval
report, partial metrics are not exposed as collected, shared error state is
isolated between reports, and the watch-only CLI remains loud but non-blocking
and non-mutating.

## Shared Helper and State Isolation

The skeptic loaded self-eval and cadence as a private module pair and verified
the actual object boundaries:

- `self_eval_metrics._git is cadence._git`;
- `self_eval_metrics._latest_tag is cadence._latest_tag`; and
- `_git.__globals__["_QUERY_ERRORS"] is cadence._QUERY_ERRORS`.

Thus self-eval clears and inspects the same list that the reused cadence helper
mutates; there is no shadow accumulator or imported stale alias.

A two-report probe started with two exhausted queries. The first report held an
outer-list copy containing both structured errors. A subsequent successful
report cleared the shared cadence list and returned without
`git_query_errors`, while the first report's serialized error evidence remained
unchanged. Appending a later error to the shared list also did not contaminate
the first report. Stale errors injected before a successful evaluation were
cleared at report start.

## Query and Reference Failure Matrix

The registered parameterized regression covers every direct query family:

| Query kind | Exhaustion result |
| --- | --- |
| latest-tag baseline | error/unevaluated after 3 attempts |
| non-merge subjects | error/unevaluated after 3 attempts |
| non-merge commit count | error/unevaluated after 3 attempts |
| merge count | error/unevaluated after 3 attempts |
| from-tag age timestamp | error/unevaluated after 3 attempts |
| from-ref ISO timestamp | error/unevaluated after 3 attempts |
| to-ref ISO timestamp | error/unevaluated after 3 attempts |

Independent real-Git probes supplied explicit invalid refs. An invalid
`from_ref` preserved five exhausted query errors; an invalid `to_ref` preserved
four. Both reports had `status=error`, `evaluation=unevaluated`, and
`fixed_metrics=null`, and every error recorded three attempts.

The deterministic no-tag boundary remains strict. Git's exact recognized
no-tag stderr returned a quiet `no-baseline-tag` pass after one attempt and no
error evidence. Adding a second fatal diagnostic caused three attempts and a
loud query-error report instead of a quiet pass.

## Partial Metrics and Window Integrity

One-query failures are covered for all seven query kinds. A separate probe
failed both commit-count queries simultaneously while all other queries
returned valid data. The resulting report preserved two errors but contained:

- `fixed_metrics=null`;
- no metric with `status=collected`;
- no top-level `commit_count` or `merge_commit_count`; and
- no partial metric line in console output.

The from/to timestamp boundary was tested independently in three forms:
from-only failure, to-only failure, and simultaneous failure. In every case the
report returned error before `_work_schema_metrics()` was called. Therefore a
failed lower or upper bound cannot become an accidental open interval and
cannot admit out-of-window WORK-SCHEMA records.

## Evidence Sanitization and Console Contract

Adversarial command and diagnostic data included URL userinfo, bearer-style
authorization, quoted multi-word tokens, multiple secrets, and more than 900
trailing characters. The structured `command` and `error` fields:

- contained none of the supplied secret values;
- were each bounded to at most 500 characters;
- retained `returncode=128`; and
- retained `attempts=3`.

For a two-error report, `_print_report()` emitted both sanitized commands and
errors, printed `returncode=128 attempts=3` twice, declared
`self-eval: ERROR git-query-error`, and did not print any partial metric. The
output finished with the watch-only mutation boundary.

## Watch-Only CLI Boundary

The skeptic invoked the real script against a disposable tagged repository
with an invalid explicit `to_ref` and `--check`. It returned exit code 0 while
printing the loud query-error and attempt evidence. The repository HEAD and
`git status --porcelain --untracked-files=all` output were identical before and
after execution. No tag, commit, tracked file, or untracked file was created.

## Failure-First Causality

Commit `28eddd5a` contains the nine new regression cases before the production
fix. An exact archive of that commit was run in a disposable OS temporary
directory. All nine failed:

```text
7 query-kind cases: report remained status=pass
1 isolation case: stale _QUERY_ERRORS remained present
1 console case: commit_count=0 printed instead of loud error
9 failed in 8.55s
```

The archive was automatically removed. At the reviewed HEAD the same three
test nodes expand to nine cases and pass:

```text
9 passed in 3.75s
```

This establishes causal failure-first provenance rather than tests that would
also pass against the old fail-open behavior.

## Compatibility, W4a, and Independent Verification

The complete registered suite exercises existing successful self-eval,
WORK-SCHEMA collection, release-cadence, and semantic-version behavior. The
skeptic reran it independently:

```text
python -m pytest tests/test_self_eval_metrics.py \
  tests/test_release_cadence_trigger.py tests/test_semver_bump_property.py -q
73 passed in 207.19s (0:03:27)

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

python scripts/taskset_work_gate.py --check
taskset-work-gate: pass
findings=0
```

Both committed W4a JSON records parse correctly, report `status: passed`, name
worker `codex-root-task-ar-614`, and contain three commands with return code 0
and empty stderr:

- task evidence
  `VERIFY-2026-07-23-task-ar-614-20260723043608.json`: 73 passed, host lock
  current, taskset gate findings 0;
- unit evidence
  `VERIFY-2026-07-23-unit-task-ar-614-001-20260723043928.json`: 73 passed,
  host lock current, taskset gate findings 0.

The independent results agree with W4a and preserve all registered compatibility
and integrity boundaries.

## Review Mutation Boundary

This skeptic review created only
`reviews/ROLE-REVIEW-2026-07-23-TASK-AR-614-SKEPTIC.md`. It did not modify
production code, tests, task/unit records, W4a evidence, `reviews/INDEX.md`, or
runtime state.
