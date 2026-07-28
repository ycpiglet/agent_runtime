---
id: RETRO-2026-07-29-task-ar-645-compound-scribe
title: TASK-AR-645 compound and Scribe retrospective
kind: retrospective
status: completed
signal: pass
date: 2026-07-29
task_id: TASK-AR-645
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
---

# TASK-AR-645 Compound and Scribe Retrospective

## Outcome

TASK-AR-645 is complete in two independently verified units. Unit 001 added
immutable task-linked compound records, deterministic defect signatures,
claim-time lookup, and linked closeout validation. Unit 002 added generic
Markdown/JSON state adapters, a bounded generated Scribe projection, and
read-only Doctor/SessionStart reporting with substantial-closeout enforcement.
PRs for both units passed the supported Python matrix before merge. Consumer
repositories, package versions, tags, and releases were not changed.

## What Worked

- T2 assumption checks stopped both units after intervening merges; bounded T3
  reviews re-anchored them without widening implementation scope.
- Independent W4b fixed each implementation head and exercised adversarial
  linkage, path safety, privacy, freshness, atomicity, and clean-wheel cases.
- One generic adapter API covered Agent Runtime, Bean Wiki, Allimbot,
  Autofolio, and JSON fixtures without embedding product-specific headings.
- The new Scribe guard correctly blocked substantial closeout while the live
  Agent Runtime state was overdue and its projection was missing. An explicit
  projection write produced a fresh 3,742-byte, ten-item derived record without
  modifying `STATUS.md`.
- The failed source-layout verification remained immutable and discoverable,
  while a compound record captured the reusable `PYTHONPATH=src` lesson.

## Friction and Corrections

- The first Unit 002 verification invoked the source-layout CLI without
  `PYTHONPATH=src`. The command metadata was corrected and a later canonical
  run passed; both records remain preserved.
- `work verify` appends every attempt to `evidence_refs`, but `work close`
  rejects the item when any referenced attempt failed. A normal
  failed-then-passed lifecycle therefore still requires manual metadata
  normalization. W6 followed the established TASK-AR-600 convention: retain
  the failed JSON and generated index entry, move its link to a clearly marked
  superseded-attempt section, and keep only current passing evidence in the
  active closeout list.
- The repository had no live Scribe projection before exercising its own new
  gate. W6 generated the declared `generated` asset explicitly and then
  rechecked digest freshness before closure.
- `work close` refreshed `BACKLOG-BOARD.md`, work-item classification, and the
  evidence index but left `ARCHIVE-INDEX.md` at 293 completed tasks while the
  board reported 294. W6 ran the canonical backlog generator to restore
  board/archive parity and record TASK-AR-645 in the archive.
- Repository auto-merge is disabled. PR #374 was merged only after all required
  checks were green and the exact head was re-read as clean and mergeable.

## Durable Rules

1. Source-layout CLI verification commands must declare `PYTHONPATH=src`
   unless the package is intentionally installed in the verification
   environment.
2. Failed verification evidence is immutable history; a later pass supersedes
   its active closeout role but never deletes or rewrites it.
3. `work verify` and `work close` need one shared active-versus-historical
   evidence contract. TASK-AR-651 must include a no-manual-edit
   fail-then-pass-then-close lifecycle regression before the release candidate
   can be called ready.
4. W6 closeout smoke must prove all derived views, including
   `ARCHIVE-INDEX.md`, are regenerated from the completed canonical work item.
5. Scribe projection generation must remain explicit. Doctor, SessionStart,
   ordinary status checks, and closure reads must never edit canonical host
   state or regenerate the projection implicitly.
6. Consumer pilots must configure or select their own host-owned sources while
   reusing the same bounded projection and freshness contract.

## Evidence

- Unit 001 W4b:
  `reviews/W4B-2026-07-29-unit-task-ar-645-001.md`
- Unit 002 W4b:
  `reviews/W4B-2026-07-29-unit-task-ar-645-002.md`
- Unit 002 failed verification:
  `reviews/VERIFY-2026-07-29-unit-task-ar-645-002-20260729054357.json`
- Unit 002 passing verification:
  `reviews/VERIFY-2026-07-29-unit-task-ar-645-002-20260729054503.json`
- Parent verification:
  `reviews/VERIFY-2026-07-29-task-ar-645-20260729054620.json`
- Compound record:
  `agents/project/knowledge/compounds/records/COMPOUND-20260729-054610-source-layout-cli-verification-must-declare-pyth-b7ebc6c5875c.json`
- Unit 002 PR: `#374`; merge:
  `b6b0bdb5a816ac76da3c121674dedab42b9164eb`
