---
type: initiative
id: INIT-AR-WORK-STORE-RESTRUCTURE
status: planned
owner: lead_engineer
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
priority: High
task_sets:
  - TASKSET-AR-WORK-STORE-RESTRUCTURE
---

# Work Store Restructure Initiative

## Purpose

Address the Owner's concern that the backlog board accumulates an ever-growing
archive and that tasks/reviews pile up. Research (Linear, Jira, GitHub Projects,
Plane, taskwarrior, dstask, Backlog.md; Postgres/MySQL sequence semantics; git
internals) shows the real problems are narrow and the fixes are targeted.

## Decision

- **Do NOT partition by lifecycle into directories.** Every mature system uses
  one store + a `status` field + views; hierarchy is a parent pointer, kind is a
  field. In git, moving files to `archive/` does not shrink history (blobs are
  hash-keyed) and adds per-transition cost. Our task store already follows the
  correct model.
- **The two real problems:** (a) the board inlines the archive (~69% of it), and
  (b) `reviews/` (402 files) grows unbounded as append-only logs. Fix (a) with an
  extracted archive manifest + attention lanes; fix (b) with date-sharding + a
  compacted index.
- **The numbering "quantum jump" is already solved** by `work_item_classifier.py`
  (stable UUID/timestamp key + dynamic `N.N.N.N` ordinal). Declare the ordinal
  canonical and treat `TASK-AR-NNN` gaps as cosmetic (Jira keys / Stripe invoice
  numbers do exactly this); upgrade the stable key to UUIDv7/ULID for
  coordination-free multi-agent minting. This initiative allocates 533.. contiguously
  to demonstrate the fix.
- **Performance:** at ~1,100 files, git/ripgrep are fine. Stay manifest-first;
  set `feature.manyFiles`/fsmonitor; defer a derived SQLite/FTS5 index until ~10k
  files. Markdown stays the source of truth.

## Scope

- Board attention-lanes + archive manifest extraction (TASK-AR-533).
- Reviews date-shard + compacted index (TASK-AR-534).
- Classifier ordinal as canonical human ID + numbering policy (TASK-AR-535).
- UUIDv7/ULID stable key + reservation ledger demotion (TASK-AR-536).
- Derived read-index/cache + repo performance config (TASK-AR-537).
- Triage/intake status + needs-attention lane (TASK-AR-538).

## Out Of Scope

- Lifecycle-state directories / moving files on every transition.
- Making any derived index (SQLite/FTS5) the source of truth.
- Bulk-moving the existing 402 reviews before the reference-rewrite tool exists.

## Source

- `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md`.
- Owner concern raised 2026-06-14 (archive accumulation, domains/state-machine,
  memory/search performance, aggregated pointer notice, numbering quantum-jump).
