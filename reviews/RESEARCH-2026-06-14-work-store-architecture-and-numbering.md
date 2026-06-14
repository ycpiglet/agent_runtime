---
type: research
id: RESEARCH-2026-06-14-work-store-architecture-and-numbering
audience: owner
status: complete
tags: [research, work-store, archival, numbering, performance, dogfooding]
---

# Work Store Architecture, Archival, Numbering & Performance — Research Synthesis

Backs `TASKSET-AR-WORK-STORE-RESTRUCTURE` (TASK-AR-533..538). Sourced from
multi-agent web research (primary docs) + repo measurement.

## Repo measurement (2026-06-14)

- Tasks: 196 files; 182 completed (93%), 12 planned, 1 worker_ready, 1 in_progress.
- Board `BACKLOG-BOARD.md`: 317 lines; "Archived Task Files" ~187 lines (~59%), archive total ~69%.
- Reviews: 402 files, 2.4MB, append-only, never transition state.
- Numbering buckets: 200s=92, 300s=67, 500s=33, timestamp-form=4. No 100s/400s.
- `work_item_classifier.py` already documents: stable IDs UUID/timestamp; ordinal `1.1.1.1` dynamic; gaps are "a generated view, not canonical identity."

## 1. Store architecture — single store + status field (NOT directory-per-state)

- Linear/Jira/GitHub Issues+Projects/Plane: one issue store, `status` is a field; boards/sprints/roadmaps are views/filters. Plane (verified at source): one issues table, state is an FK, Cycles/Modules are join tables not containers.
- Hierarchy = parent pointer (`parentId`), not nested folders. File-based: taskwarrior (SQLite + status field), tissue (closing *adds a line* to keep git history), git-bug (git objects). dstask (dir-per-state) is the outlier and only to skip loading; Backlog.md moves files only at the terminal `completed/`+`archive/` step.
- **Recommendation:** keep the flat tasks dir + `status:` + `parent_id:` (already correct). Do not add trash/candidate/waiting/in-progress/done directories. Kind is a field; units nesting under `tasks/units/` is fine.

## 2. Lifecycle & archival — git makes moves cheap-but-pointless; shrink the working set, not history

- Git is content-addressable (blob = hash); `git mv` to `archive/` does NOT remove history or shrink the repo (Pro Git, Git Internals). What slows things is working-tree file COUNT (GitHub fsmonitor); git's answer is sparse-checkout.
- Real archival: Linear auto-archives on status==closed + age, still searchable, sorted last; Jira hides until restored. Append-only logs date-shard (`YYYY-MM/`): logrotate `-%Y%m%d`, Athena `year=/month=/day=`, Postgres RANGE partitions. Append-only + compaction/snapshot = Kafka log compaction, LSM SSTables, event-sourcing snapshots.
- **Recommendation:** TASK store — keep status in place, exclude completed from the active view, keep an archive index (moving gives zero git benefit at 196). REVIEWS store — date-shard `reviews/YYYY-MM/` + one compacted index (highest-value change; reviews are logs, not a state machine).

## 3. Performance with thousands of markdown files

- ripgrep: sub-second on the Linux kernel tree (~75k files); bites only at millions.
- git status scales with file COUNT: fine ~10k, sluggish 50k+; `feature.manyFiles` (untracked cache + fsmonitor + index-v4) recommended at 10,000+; Scalar handles 3.5M.
- Single FS dir (ext4 HTree): fine to ~10k. Editor bites earliest: VS Code default inotify 8,192 watchers (raise it; set `files.watcherExclude`); Obsidian graph freezes ~2,000 dense links.
- **Recommendation (ordered):** (1) manifest-first reads (board/classification/catalog JSON) so agents read one file, not hundreds; set `feature.manyFiles`+`core.untrackedCache`+`core.fsmonitor`. (2) date-shard reviews + claims before ~5-10k. (3) only past ~10k add a derived SQLite/FTS5 index rebuilt from markdown via mtime+hash — never SSoT.

## 4. ID allocation — gaps are inherent; make the human number a derived view

- Postgres docs: sequences "cannot be used to obtain gapless sequences"; aborts leave gaps. MySQL/InnoDB: rolled-back auto-increment values are lost. Hand-allocating 200/300/500 blocks *manufactures* gaps.
- Systems that "solved" it separated an opaque immutable key from a derived display number: Linear (UUID `id` + human `identifier` ENG-123), Jira (immutable internal id; key is mutable, old keys redirect), Stripe (opaque `ch_…` + separate sequential invoice `number`).
- Coordination-free stable keys: UUIDv7/ULID embed a ms timestamp → collision-free + time-sortable with zero coordination (RFC 9562 §5.7 prefers v7); Snowflake/Instagram/Discord partition by worker-id.
- **Recommendation:** declare the classifier ordinal (`N.N.N.N`) the official human number; treat `TASK-AR-NNN` gaps as cosmetic; upgrade `task_uid` v4→v7/ULID; demote the reservation ledger to optional vanity reservation. Allocate `TASK-AR-NNN` contiguously (533.. this initiative).

## 5. Aggregated pointer/notice — curate attention, don't dump

- Linear separates Triage (shared intake, excluded from views until accept/decline/snooze), Inbox (personal subscribed), and backlog. Jira: ranked backlog vs current-sprint board. GitHub Projects: saved views = perspectives without duplicating data. GTD: small Next Actions + large Someday/Maybe. Notion rollups show count + representatives + "see all N". Shneiderman (1996): "overview first, zoom and filter, details-on-demand"; Nielsen progressive disclosure.
- **Recommendation:** board = Triage / Active (full detail) / Rollups (counts+pointers); move the ~69% archived dump to a generated `ARCHIVE-INDEX.md`, show only count+link on the board.

## Proposed task breakdown → registered

533 board lanes + archive manifest · 534 reviews date-shard + index · 535 classifier ordinal canonical + numbering policy · 536 UUIDv7/ULID + reservation demote · 537 read-index/cache + perf config · 538 triage status + needs-attention lane.

## Sources

Linear docs (custom-views, triage, project-graph), Jira/Atlassian (sequences, keys), GitHub (fsmonitor, Projects), Plane source, Postgres/MySQL manuals (sequence gaps), RFC 9562 (UUIDv7), ULID spec, Pro Git (Git Internals), ripgrep benchmarks, Shneiderman 1996, Nielsen (progressive disclosure), taskwarrior/dstask/tissue/Backlog.md docs.
