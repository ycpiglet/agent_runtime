---
title: TASK-AR-617 Parser Compatibility T3 Replan
date: 2026-07-23
signal: pass
score: 98
task_id: TASK-AR-617
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
review_type: dispatch-replan
trigger: failure-first-scope-discovery
baseline_sha: 63bf37f9
failure_first_commit: 28906fd4
reviewed_by: codex-root
tags: [t3, plan-assumptions, work-cli, frontmatter, data-integrity]
---

# TASK-AR-617 Parser Compatibility T3 Replan

## Bottom Line

The committed failure-first matrix reproduced silent truncation at all three
required lifecycle boundaries. A robust fix for values containing a literal
hash plus both quote styles cannot be expressed by `scripts/work.py` alone:
the established reader currently strips quote delimiters but does not decode
escaped JSON-style double-quoted strings.

The task may continue only with a narrow parser compatibility amendment. The
comment scanner, work schema, and general YAML dependency boundary remain
unchanged.

## Failure-First Evidence

At commit `28906fd4`, these tests fail with the parsed value reduced to text
before the hash marker:

- registration: task summary, unit context, and unit acceptance list;
- verification rewrite: quoted scalar and quoted list item;
- close rewrite: quoted scalar containing both quote styles.

The initial quoted fixture parses correctly before verify/close, proving the
loss occurs during `_frontmatter` re-emission rather than fixture setup.

## Required Compatibility Surface

- `scripts/work.py` emits unsafe strings as deterministic JSON double-quoted
  scalars carrying a reserved work-scalar marker, with Unicode preserved.
- `scripts/backlog_board.py::parse_scalar` decodes only valid marker-bearing
  JSON strings and otherwise retains current compatibility behavior.
- `parse_header_block` uses the same scalar decoder for block-list items so
  scalar and list values have one round-trip contract.
- The generated-host parser mirror remains byte-identical and the host lock is
  refreshed.

## Boundaries

- Do not modify `strip_comment`; TASK-AR-608 already established quote-aware
  comment boundaries.
- Do not add PyYAML or replace the lightweight parser.
- Do not reinterpret existing single-quoted, unquoted, flow-list, malformed,
  or ordinary scalar inputs.
- Do not quote every existing safe value; limit serialization churn to values
  whose raw form is not round-trip safe.
- Keep TASK-AR-618 selector behavior out of this task.

## Revised Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py -q`
- `python scripts/work_schema_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`
- root/template parsers both pass the same marker scalar/list and legacy
  compatibility matrix; the files remain intentionally different outside the
  shared frontmatter surface.

## T3 Decision

Amend the task, unit, and active claim footprint with the root/template parser,
its focused regressions, and the generated-host lock. Re-record the T0/T3
assumption anchors before implementation resumes.
