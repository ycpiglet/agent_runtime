---
id: TASK-AR-534
display_id: TASK-AR-534
task_uid: b81f8006-1e3c-4087-aece-d1bb5935e3b7
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5500
owner: lead_engineer
task_set_id: TASKSET-AR-WORK-STORE-RESTRUCTURE
tags:
  - work-store
  - reviews
  - date-shard
  - index
---

# TASK-AR-534 - Reviews date-shard + compacted index

## Goal

- Treat `reviews/` (402 files, 2.4MB, pure append, never transitions state) as a logs/events workload, not a state machine: date-shard into `reviews/YYYY-MM/` and maintain one compacted append-only `REVIEWS-INDEX.md`. This is the highest-value structural change (reviews grow unbounded). (GH dogfooding follow-up)

## Scope

- Generate `reviews/REVIEWS-INDEX.md` (id + type + date + title + 1-line + link per record) — index-first, no behavior change.
- Shard NEW records into `reviews/YYYY-MM/` going forward; provide a migration tool for existing files that **atomically rewrites references** (owner-docs.yml manifest paths, BACKLOG links, NEXT-SESSION-POINTER, cross-links) so nothing breaks.
- Bulk migration of the existing 402 is gated behind the reference-rewrite tool (do not move files until references follow).

## Acceptance Criteria

- `REVIEWS-INDEX.md` lists all review records and regenerates deterministically.
- New records land in `reviews/YYYY-MM/`; index resolves both old flat and new sharded paths.
- Migration of existing files updates every reference atomically (manifest + links) with a dry-run check.

## Dependency / Footprint

- depends_on: none (foundational).
- target_files: `reviews/**`, `reviews/REVIEWS-INDEX.md` (new), `scripts/reviews_index.py` (new), reference-rewrite touches `owner-docs.yml`/`BACKLOG.md` only during migration. Disjoint from 533/535/536 for the index step.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md` (logrotate/Athena/Postgres RANGE partitioning; git blob=hash so moving files does not shrink history; append-only + compaction).
