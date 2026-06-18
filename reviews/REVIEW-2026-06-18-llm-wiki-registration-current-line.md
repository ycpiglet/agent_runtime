---
title: LLM-Wiki Registration Current-Line Integration
date: 2026-06-18
signal: pass
score: 100
tags: [llm-wiki, registration, backlog, graph, wiki]
---

# LLM-Wiki Registration Current-Line Integration

## Bottom Line

`TASKSET-AR-LLM-WIKI` is now registered in the current line instead of living
only on the preserved `claude/llm-wiki` branch. The current registry uses order
`624` to avoid the newer design-system taskset orders `618` through `623`.

## Signal

| Check | Result |
| --- | --- |
| `python scripts/backlog_board.py --write` | pass, board regenerated |
| `python scripts/work_item_classifier.py --write` | pass, classification regenerated |
| `python scripts/entity_catalog.py --write` | pass, catalog includes LLM-Wiki records |
| `python scripts/evidence_index_generator.py --write` | pass |
| `rg TASKSET-AR-LLM-WIKI ...` | pass, board/classification/catalog/pointer surface the taskset |

## Scope

- Added `INIT-AR-LLM-WIKI` and task records `TASK-AR-590` through `TASK-AR-596`.
- Marked `TASK-AR-590`, `TASK-AR-591`, and `TASK-AR-592` completed because the
  current line already contains corpus expansion, wiki page API, and wiki page
  view evidence.
- Kept `TASK-AR-593` through `TASK-AR-596` planned so the remaining search/ask,
  graph-lens refinement, nav hub, and lint/closeout work stays visible.
- Updated `TASKSET-DEFINITIONS.json`, generated board/classification/catalog
  surfaces, `STATUS.md`, and `NEXT-SESSION-POINTER.yml`.

## Boundary

This integrates registration and current-line truth only. It does not mutate the
preserved `claude/llm-wiki` branch, does not claim the full taskset is complete,
and does not implement the remaining `/api/wiki/search` or `/api/wiki/ask`
unit.

## Next

Start `TASK-AR-593` from the current records: deterministic wiki search + ask
API, then the shared Wiki search/ask UI.
