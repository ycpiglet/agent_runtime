---
id: REVIEW-2026-07-24-task-ar-622-frontmatter-scalar-contract
title: TASK-AR-622 frontmatter scalar integrity contract
kind: implementation-review
status: approved
date: 2026-07-24
task_id: TASK-AR-622
task_set_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
decision: fail-closed-before-lifecycle-rewrite
---

# TASK-AR-622 Frontmatter Scalar Integrity Contract

## Problem

The lightweight work-item parser treats every unquoted `#` as the beginning of
a comment. A legacy value such as `origin_ref: github:#274` or
`context: Preserve issue #274` is therefore truncated before `work verify` or
`work close` can rewrite its frontmatter.

## Decision

Registration continues to encode YAML-significant scalars with the existing
versioned scalar prefix. Before parsing a work item for `verify` or `close`,
the lifecycle loader scans only the raw frontmatter header and:

- rejects a top-level plain scalar whose unquoted `#` would be stripped;
- rejects a plain scalar list item under the same condition;
- permits quoted or complete flow-style values followed by a genuine YAML
  comment;
- ignores Markdown body hashes and full-line frontmatter comments.

The command reports the work path, key, and source line, then exits before
running verification commands or writing evidence, closeout metadata, indexes,
or boards.

## Migration boundary

The detector does not guess whether discarded text was data or a comment and
does not reconstruct a suffix. A reviewed migration must quote or re-encode
the complete intended value before the lifecycle command is retried. No
historical bulk rewrite is part of this task.

## Evidence

Failure-first regressions demonstrate that the previous implementation ran
verification and completed closeout while silently discarding the suffix.
Focused tests cover registration round trips, safe quoted values, safe trailing
comments, unsafe scalar values, unsafe list items, and byte-for-byte
non-mutation on refusal.
