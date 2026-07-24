---
id: RETRO-2026-07-24-work-frontmatter-scalar-integrity
title: Work frontmatter scalar integrity retrospective
kind: retrospective
status: completed
signal: pass
date: 2026-07-24
task_id: TASK-AR-622
task_set_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
---

# Work Frontmatter Scalar Integrity Retrospective

## What worked

- Failure-first lifecycle tests proved the original silent rewrite instead of
  relying on parser-visible round trips.
- Independent and skeptical verification found two real edge classes before
  merge: hash-first values with noncanonical list indentation, and incomplete
  nested flow delimiters.
- Byte-for-byte tree comparison and a child-execution marker made the
  fail-before-write contract measurable.

## What changed

- Raw frontmatter is inspected before parsing on verify and close.
- Plain scalar hashes fail closed; quoted values and syntactically complete
  flow values may retain genuine trailing comments.
- Flow safety now uses balanced bracket, brace, quote, and escape state instead
  of first/last-character heuristics.
- Registration coverage explicitly includes hash-bearing provenance,
  contextual values, and the existing versioned encoding.

## Carry-forward rule

For data-integrity guards, test the smallest empty-prefix form, alternate valid
indentation, malformed-but-delimited forms, and observable side effects. A
passing parser round trip is insufficient when the parser may already have
discarded source text.
