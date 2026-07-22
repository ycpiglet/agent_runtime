---
title: TASK-AR-609 Dispatch T3 Replan
date: 2026-07-23
signal: pass
score: 100
task_id: TASK-AR-609
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
review_type: dispatch-replan
trigger: t2-plan-assumption-drift
baseline_sha: fdc2948c92bf21c9d3bda5366a5a270a4c1e903f
reviewed_by: codex-root
tags: [t3, plan-assumptions, github-300, classifier, work-store]
---

# TASK-AR-609 Dispatch T3 Replan

## Bottom Line

- T2 correctly refused dispatch after TASK-AR-608 changed the root/template
  frontmatter parser, its focused test, and the host lock.
- The drift is understood and does not invalidate TASK-AR-609's intended
  classifier-only scope.
- Dispatch may resume after recording the anchors below at merged main
  `fdc2948c92bf21c9d3bda5366a5a270a4c1e903f`.

## Drift Reviewed

T2 reported hash changes in:

- `scripts/backlog_board.py`
- `src/agent_runtime/templates/project/scripts/backlog_board.py`
- `tests/test_backlog_board_tasksets.py`
- `tests/fixtures/host/agent_runtime.lock.json`

These changes are the approved TASK-AR-608 result. They preserve quoted hash
markers and legacy plain-scalar comment boundaries. TASK-AR-609 consumes the
same metadata reader, so the merged parser is the correct new planning
baseline rather than an incompatible dependency.

## Current Reproduction

- GitHub issue 300 remains open at T3 review time.
- `scripts/work_item_classifier.py::_initiative_records()` and its template
  mirror still read every Markdown file under `agents/project/initiatives/`.
- The collector does not inspect `kind` or `type` and resolves identity only as
  `id` then filename stem; it does not use canonical `work_id`.
- A taskset record stored in that mixed directory can therefore be emitted as
  both an initiative and a taskset without producing a classifier finding.

## Revalidated Scope

- Add failure-first mixed initiative/taskset fixtures and a cross-level
  duplicate oracle.
- Filter initiative collection to canonical `kind: initiative`, accepting the
  existing `type` compatibility alias only when `kind` is absent.
- Resolve initiative identity deterministically as `id`, then `work_id`, then
  filename stem.
- Mirror the code and tests across root/template surfaces and regenerate the
  host lock and generated classifier views.

## Boundaries

- Do not move canonical records between directories.
- Do not change taskset/task/unit numbering or hierarchy semantics.
- Do not replace the frontmatter parser or introduce a new YAML dependency.
- The separately observed work-item frontmatter serialization loss around
  unquoted hash markers is an intake item, not TASK-AR-609 implementation
  scope. TASK-AR-609 lifecycle text will avoid ambiguous unquoted hash values.

## Acceptance And Verification

- Taskset records never populate the initiative level.
- Legitimate initiative records keep stable IDs, titles, status, and ordering.
- The `id`/`work_id`/filename fallback is covered explicitly.
- Mixed fixtures contain no ID duplicated across initiative and taskset
  levels.
- Run:
  - `python -m pytest tests/test_work_item_classifier.py tests/test_template_work_item_classifier.py -q`
  - `python scripts/work_item_classifier.py --write --check`
  - `python scripts/regen_host_lock_if_needed.py --check`

## T3 Decision

Re-record the design, lifecycle flow, parser dependency, classifier root and
template copies, both classifier test files, the parser regression file, and
the host lock. Claim creation must then repeat T2 and may proceed only with
zero drift findings.
