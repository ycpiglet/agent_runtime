---
id: REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration
title: Register work frontmatter scalar integrity defect
kind: planning
status: registered
date: 2026-07-23
owner: lead-engineer
---

# Work frontmatter scalar integrity defect

## Current objective

Prevent work lifecycle rewrites from losing literal `#` content in scalar
metadata while keeping TASK-AR-602 closeout repair narrowly scoped.

## Observed fact

The independent skeptical W4b report
`reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md` found that
`scripts/work.py verify` rewrote two previously registered work records after
their unquoted scalar values had been parsed as YAML comments:

- TASK-AR-602 `origin_ref` lost issue IDs `#274,#279,#280,#285,#287,#289,#290`
  and PR `#277`;
- UNIT-TASK-AR-602-001 lost the same `origin_ref` suffix and reduced its
  context from the full release rationale to `GitHub`.

The public v0.7.0 tag, release, CI, and issues remain correct. The defect is in
internal provenance preservation and blocks closeout integration until the
current records are restored.

## Decision

- Register the serializer/parser contract defect as its own
  initiative/taskset/task/unit before implementation.
- Do not implement the general serializer fix inside TASK-AR-602.
- Restore the two current work records from the pre-rewrite main version using
  explicitly quoted scalars, retain W4a fields/evidence, and confirm a
  serialize round trip does not truncate them.
- Synchronize the exhaustive taskset expectation created by registration; this
  bookkeeping is not implementation of the follow-up.
- Require the skeptical auditor to recheck the repair before releasing the
  TASK-AR-602 worker claim.

## Boundaries

- Follow-up implementation owns `scripts/work.py` and focused work
  registration/verification tests.
- TASK-AR-602 may change only its task/unit scalar quoting and provenance text,
  the new registration records, exhaustive taskset expectation, evidence
  index, and closeout documentation/state.
- Historical failed and passing verification evidence remains immutable.

## Next actions

1. Register the follow-up with a T0 assumption snapshot.
2. Restore and quote TASK-AR-602 provenance/context.
3. Run focused round-trip, schema, taskset, and governance checks.
4. Request skeptical W4b recheck and proceed only if HOLD is lifted.

