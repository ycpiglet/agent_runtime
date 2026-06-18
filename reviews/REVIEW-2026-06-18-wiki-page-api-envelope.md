---
title: Wiki Page API Envelope
date: 2026-06-18
signal: pass
score: 100
tags: [llm-wiki, wiki-api, knowledge-digest, mini-graph, read-only-api]
---

# Wiki Page API Envelope

## Bottom Line

The console now exposes a deterministic wiki page API over the expanded
knowledge graph. `/api/wiki/page?id=<entity>` and `/api/wiki/page/<entity>`
return a read-only page envelope with digest summary, metadata, resolved
relations, backlinks, and a local minigraph.

## Signal

| Check | Result |
| --- | --- |
| Wiki page API tests | pass, `4` tests |
| Related graph/digest regression | pass, `37` tests |
| Knowledge graph check | pass, `findings=[]` |
| Owner doc format | pass |

## Scope

- Added `ui_state.build_wiki_page()` with schema
  `agent-runtime-wiki-page/v1`.
- Reused `scripts/knowledge_graph.py` and `scripts/knowledge_digest.py`.
- Added `/api/wiki/page` and `/api/wiki/page/<id>` read-only routes.
- Filtered relations/backlinks to resolved graph nodes only, so the UI can
  render links without dead endpoints.
- Added tests for envelope shape, missing entity handling, route success, and
  404 behavior.

## Boundary

This does not yet render the 2-column wiki page in the browser. It provides the
stable deterministic API that the next UI unit can consume.

## Next

- Build the Wiki page view and hash route against this API.
- Add search/ask routes after the page view has a place to display results.
