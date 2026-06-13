---
id: TASK-AR-537
display_id: TASK-AR-537
task_uid: 85813f55-1aca-4dde-81cc-40e347376c34
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5500
owner: lead_engineer
task_set_id: TASKSET-AR-WORK-STORE-RESTRUCTURE
tags:
  - work-store
  - index
  - performance
  - cache
---

# TASK-AR-537 - Derived read-index/cache + repo performance config

## Goal

- Keep the agent read surface small and fast as the store grows toward thousands of files: formalize a manifest-first read path now, and spec a derived search index to switch on later — without ever making the index the source of truth (markdown stays canonical).

## Scope

- Formalize the generated JSON manifest(s) (board/classification/catalog) as *the* surface agents read instead of globbing hundreds of markdown files; document the contract.
- Spec a derived **SQLite/FTS5** index, rebuilt from markdown via mtime+hash, to be enabled only past ~10k files / when cross-corpus full-text query is needed. Markdown remains SSoT.
- Set repo performance config: `git config feature.manyFiles true`, `core.untrackedCache`, `core.fsmonitor`; add VS Code `files.watcherExclude` for `.git`/`.venv`/large dirs.

## Acceptance Criteria

- A documented manifest-first read contract exists; agents read one index instead of globbing.
- A deferred-but-specified SQLite/FTS5 design with a mtime+hash rebuild trigger and a ~10k-file switch-on threshold.
- Performance git/editor config applied and documented.

## Dependency / Footprint

- depends_on: TASK-AR-533 (board lanes), TASK-AR-534 (reviews index) — consumes their layout.
- target_files: `scripts/work_index.py` (new), `.git/config`/docs, `agents/project/*` read-surface doc, `.vscode/settings.json`. Disjoint from console modules.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md` (ripgrep ~75k files sub-sec; git status scales with file count, feature.manyFiles @10k+; VS Code 8,192 watchers; SQLite/FTS5 as derived cache, never SSoT).
