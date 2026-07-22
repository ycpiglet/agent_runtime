---
title: Work CLI Metadata Integrity Registration
date: 2026-07-23
signal: pass
score: 97
review_type: work-registration-design
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
reviewed_by: codex-root
tags: [work-registration, work-cli, data-integrity, selector]
---

# Work CLI Metadata Integrity Design

## Bottom Line

Two independently reproduced `scripts/work.py` defects must be resolved before
the v0.7.0 current-head release preflight:

1. `_frontmatter` emits string and list values without protecting literal hash
   markers. A later parse treats the marker as a comment, so `work verify` or
   `work close` can silently truncate canonical metadata.
2. `_candidate_work_paths` expands an exact task ID into both the task record
   and every unit below it. Generic task-level commands therefore reject an
   otherwise unique exact task ID as ambiguous.

These are separate implementation tasks in one integrity taskset. Neither is
folded into completed parser or dispatcher work.

## Evidence

- TASK-AR-608 verification and closeout reproduced lifecycle metadata loss when
  a scalar contained a literal issue marker; the workflow temporarily used
  words such as `issue 298` to avoid a second destructive rewrite.
- `reviews/REVIEW-2026-07-23-task-ar-609-dispatch-t3-replan.md` explicitly
  records the serialization loss as deferred intake.
- `reviews/W4B-2026-07-19-TASK-AR-594-RECHECK.md` records that
  `work.py verify TASK-AR-594` resolves both the task and unit and exits with
  `work-verify:ambiguous`.
- TASK-AR-612 reproduced the same selector behavior: its exact task path was
  required while its unit ID remained directly verifiable.

## Decomposition

### Task 1 - Round-trip-safe frontmatter serialization

- Preserve exact string/list scalar values through registration and lifecycle
  rewrites, beginning with literal hash markers and quote-bearing values.
- Keep deterministic key/list ordering and the established lightweight parser;
  do not introduce a general YAML dependency.
- Cover initial registration plus at least one verification and close rewrite
  so the fix is proven at real mutation boundaries.

### Task 2 - Exact work-item selector precedence

- Make an exact task ID select its canonical task record, not its descendant
  units; make an exact unit ID continue to select only that unit.
- Preserve explicit-path resolution and fail closed when canonical records are
  genuinely duplicated or absent.
- Exercise all generic consumers of `_load_work_item` whose behavior can be
  affected: verify, close, assign, and criteria.

## Boundaries

- Do not change `backlog_board.strip_comment` or reopen the completed quoted
  comment scanner task unless failure-first evidence proves parser drift.
- Do not redesign work hierarchy, unit inheritance, or command semantics.
- Do not repair already truncated historical prose as part of implementation;
  retain it as provenance and record any recovery separately.
- Do not start TASK-AR-602 release execution until both tasks pass W4a, an
  independent W4b, PR CI, post-merge main CI, and W5/W6 cleanup.

## Acceptance And Verification

- Literal hash and quote-bearing metadata round-trip byte-for-byte as parsed
  values across registration, verification, and close rewrites.
- Task IDs, unit IDs, and explicit paths resolve deterministically without
  parent-child false ambiguity.
- Real duplicate canonical records still produce a bounded ambiguity error.
- Focused work CLI modules, work-schema checks, and the full suite pass before
  release handoff.

## Decision

Register `TASKSET-AR-WORK-CLI-INTEGRITY` through `scripts/work.py new` with two
worker-ready tasks and one smallest executable unit per task. T0 anchors must
include this design record, `scripts/work.py`, dispatcher flow scripts, and all
declared test targets.
