---
title: Wiki Page View
date: 2026-06-18
signal: pass
score: 100
tags: [llm-wiki, wiki-ui, console, mini-graph, hash-routing]
---

# Wiki Page View

## Bottom Line

The console now has a human-browsable Wiki view backed by the deterministic
`/api/wiki/page` envelope. It supports `#/wiki` and `#/wiki/<entity-id>` hash
routes, renders the summary, typed relations, backlinks, metadata, and a bounded
local mini-graph.

## Signal

| Check | Result |
| --- | --- |
| UI console regression | pass, `155` tests |
| Wiki/knowledge regression | pass, `58` tests |
| Knowledge graph check | pass, `findings=[]` |
| Wiki UI asset guards | pass, ASCII JS block, `node --check`, token-only CSS |

## Scope

- Added a Records -> Wiki nav destination and `view-wiki` page shell.
- Added hash routing for `#/wiki` and `#/wiki/<entity-id>`.
- Added deterministic wiki page rendering from `/api/wiki/page/<id>`.
- Rendered page body, relations, backlinks, metadata, and a local mini-graph.
- Added click navigation for relation/backlink rows and mini-graph nodes.
- Added console tests for view registration, routing markers, JS ASCII/node
  validity, and token-only CSS.

## Boundary

Search and Ask remain the next unit. This view accepts direct entity IDs and
internal relation/backlink navigation, but it does not yet add `/api/wiki/search`
or `/api/wiki/ask`.

## Next

- Add deterministic `/api/wiki/search` and `/api/wiki/ask`.
- Wire the shared search/ask bar into this Wiki view.
- Expand the mini-graph lens if the next visual pass needs typed edge controls.
