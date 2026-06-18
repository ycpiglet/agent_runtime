---
title: Wiki Search And Ask
date: 2026-06-18
signal: pass
score: 100
tags: [llm-wiki, wiki-search, wiki-ask, console, deterministic-first]
---

# Wiki Search And Ask

## Bottom Line

`TASK-AR-593` now has deterministic Wiki search and evidence-first ask
surfaces. The console exposes `/api/wiki/search` and `/api/wiki/ask`, and the
Wiki view has a shared search/ask bar whose results link back into wiki entity
pages.

## Signal

| Check | Result |
| --- | --- |
| Wiki search/ask API + page API | pass, `8` tests |
| UI console regression | pass, `155` tests |
| Knowledge graph/digest/ask/lint regression | pass, `62` tests |
| Python compile | pass |
| Diff whitespace check | pass |

## Scope

- Added `ui_state.build_wiki_search()` and `ui_state.build_wiki_ask()`.
- Added `/api/wiki/search?q=` and `/api/wiki/ask?q=&llm=0|1`.
- Added ranked search results with `{id, kind, title, snippet, score}`.
- Added evidence-first ask results with `{query, evidence, cited, answer,
  llm_used}`.
- Added explicit LLM opt-in behavior that degrades to evidence-only when no
  provider is configured.
- Added Wiki view search/ask controls and clickable result/evidence rows.

## Boundary

This is W4a self-verification. `TASK-AR-593` is ready for W4b independent
verification, claim release, merge, and generated board/status refresh; it is
not yet marked completed.

## Next

- Run W4b independent verification against this branch.
- Release `CLAIM-20260618-233054-task-ar-593-6287` with verifier evidence.
- Merge and regenerate board/index/status surfaces from the released state.
