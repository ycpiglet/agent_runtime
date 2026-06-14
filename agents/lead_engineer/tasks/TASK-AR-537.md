---
id: TASK-AR-537
display_id: TASK-AR-537
task_uid: 85813f55-1aca-4dde-81cc-40e347376c34
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
started_at: 2026-06-14T10:52:00+09:00
updated_at: 2026-06-14T11:00:00+09:00
completed_at: 2026-06-14T11:00:00+09:00
status: completed
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

## Completion Evidence

- `agents/project/READ-SURFACE-CONTRACT.md`: names the 6 canonical generated manifests agents read instead of globbing; documents the git perf config and the deferred SQLite/FTS5 design (mtime+hash rebuild, disposable cache, ~10k threshold).
- `scripts/work_index.py` + `tests/test_work_index.py`: `--check` verifies the read-surface manifests exist (exit 1 if any missing) + reports corpus size (820 md) + FTS recommendation; 3 tests.
- `.vscode/settings.json`: `files.watcherExclude` for `.git`/`.venv`/`.worktrees`/caches. Git perf config applied locally: `feature.manyFiles=true`, `core.untrackedCache=true`, `core.fsmonitor=true`.
- Scope decision: corpus ~820 md (8% of 10k) → SQLite/FTS5 specified but DEFERRED (no vaporware; grep confirms no half-built DB).

## Verification Results

- W4a: `work_index.py --check` findings=0; 3 tests pass; governance gate exit 0.
- W4b (independent, verifier != worker): APPROVE — `reviews/W4B-2026-06-14-TASK-AR-537.md`. All 6 criteria PASS (contract documented, check non-vacuous incl. empty-dir exit 1, deferred SQLite concrete, perf config applied, tests real, defer judged sound).
