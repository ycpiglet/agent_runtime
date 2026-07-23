---
id: RETRO-2026-07-23-july-upstream-intake-closeout
title: July upstream intake closeout and v0.7.0 release retro
kind: retro
status: complete
date: 2026-07-23
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
---

# July upstream intake closeout and v0.7.0 release retro

## Outcome

The intake taskset completed and v0.7.0 was published from verified main. The
release itself stayed correct through two internal closeout defects because
publication stopped at explicit gates and external state was read back after
each mutation.

## What worked

- Candidate and post-merge matrices covered Python 3.10, 3.11, and 3.12.
- The annotated tag object, peeled commit, GitHub release body, visibility, and
  issue states were all independently read back.
- Failed W4a evidence was retained rather than overwritten.
- Technical and skeptical W4b perspectives found different classes of risk;
  the stricter HOLD decision controlled closeout until both blockers cleared.
- Named taskset completion exposed stale lifecycle metadata before W6.

## What failed or slowed the work

- `work.py verify` delegated caret-bearing commands through the Windows shell;
  TASK-AR-621 now owns the cross-platform execution contract.
- New taskset registration required an exhaustive test expectation update,
  causing one preventable full-suite rerun.
- Legacy unquoted `#` scalars were already truncated before lifecycle rewrite;
  TASK-AR-622 now explicitly requires fail-closed detection or reviewed
  migration, not merely parser-visible round trips.
- A CRLF-to-LF normalization changed an automatic T0 digest immediately;
  T3 re-anchoring restored dispatch readiness.
- The full Windows pytest run took 11-14 minutes, amplifying every avoidable
  metadata failure.

## Decisions carried forward

- Keep release publication evidence immutable and separate from closeout
  metadata evidence.
- Run taskset-registration focused expectations before the full suite.
- Treat raw frontmatter bytes and parser-visible metadata as separate integrity
  layers in TASK-AR-622.
- Recheck assumption digests after the first committed normalization boundary.
- Continue using exact-head independent W4b and adopt the stricter judgment
  when reviewers disagree.

## Follow-ups

- `TASK-AR-621` — Windows verification command argument preservation.
- `TASK-AR-622` — lossless/fail-closed work frontmatter scalar integrity.

