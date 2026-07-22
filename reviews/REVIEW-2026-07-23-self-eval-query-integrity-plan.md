---
title: Self-Eval Query Integrity Recovery Plan
date: 2026-07-23
signal: needs-fix
score: 92
tags: [planning, self-eval, git-query, data-integrity, github-318]
---

# Self-Eval Query Integrity Recovery Plan

## Bottom Line

TASK-AR-613 independent W4b found that `scripts/self_eval_metrics.py`
directly reuses `release_cadence_trigger._git` but does not clear or inspect
the helper's structured query-error accumulator. If a Git query exhausts all
three attempts, self-eval converts the missing result to zero or empty data and
still emits `status: pass`. GitHub issue 318 records the defect.

TASK-AR-613 is intentionally limited to release-cadence and release-auto
consumers and explicitly stops before modifying unrelated status consumers.
This plan therefore registers the self-eval remediation as a separate work
item rather than expanding the active unit in place.

## Evidence

- A tagged fixture with a non-zero comparison window reports normally when all
  Git queries answer.
- Forcing `git rev-list --no-merges --count` to return rc 128 on all three
  attempts leaves self-eval at `status=pass`, reports `commit_count=0`, and
  emits no `git_query_errors`.
- The shared helper has already recorded the exhausted failure, so the defect
  is in self-eval's report lifecycle and error propagation rather than retry
  execution.
- Independent reports:
  `reviews/W4B-2026-07-23-TASK-AR-613.md` and
  `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-613-SKEPTIC.md`.

## Decision

Register one narrow P0 unit that clears query state at report start, treats any
exhausted query as an unevaluated/error report, preserves sanitized structured
evidence, and prints a deterministic loud CLI diagnostic without introducing
mutations. Cover every direct shared-helper query used by self-eval, including
baseline resolution and ref timestamps.

## Scope Boundary

- Do not alter fixed-metric formulas or WORK-SCHEMA collection semantics.
- Do not change release cadence thresholds, release-auto decisions, or semantic
  version policy.
- Preserve a genuinely untagged repository's documented no-baseline behavior.
- Do not redesign the shared Git helper API unless the focused consumer fix
  cannot provide truthful lifecycle isolation.

## Verification

- Failure-first tests reproduce pass/zero collapse for each direct query.
- Exhausted queries produce error/unevaluated status with sanitized structured
  evidence and no collected metrics derived from partial Git data.
- Successful and genuinely untagged fixtures preserve existing output.
- Self-eval, cadence, semantic-version, host-lock, and taskset gates pass before
  independent W4b.
