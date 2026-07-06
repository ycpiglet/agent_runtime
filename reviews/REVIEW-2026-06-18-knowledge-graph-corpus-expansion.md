---
title: Knowledge Graph Corpus Expansion
date: 2026-06-18
signal: pass
score: 100
tags: [knowledge-graph, llm-wiki, corpus, runtime-assets, graph-integrity]
---

# Knowledge Graph Corpus Expansion

## Bottom Line

The knowledge graph now ingests product documentation, Python modules, file
nodes, config/schema files, and runtime assets in addition to work items,
reviews, claims, git, and domains. The previous dangling preservation-claim
edge for `TASK-AR-590` is no longer emitted because inactive claim edges to
missing tasks are pruned while active claim gaps remain lint-visible.

## Signal

| Check | Result |
| --- | --- |
| Graph check | pass, `findings=[]` |
| Graph build | pass, `2129` nodes and `3066` edges with `--git-limit 0` |
| New kinds present | `doc`, `module`, `file`, `config`, `schema`, `asset` |
| Knowledge stack tests | pass, `54` tests |
| Knowledge lint gate | pass |
| Owner governance | pass |

## Scope

- Added deterministic doc ingest for `docs/**/*.md` and root operator docs.
- Added Python module/file ingest with `ast` import edges and test backlinks.
- Added config/schema ingest for root config, `schemas/**`, and template config.
- Added runtime asset nodes from `RUNTIME-ASSET-REGISTRY.json` plus metric
  metadata from `runtime_asset_usage`.
- Mirrored the implementation into the host-project template.
- Regenerated the host lock fixture.

## Decision

Soft derived edges (`references`, `documents`, `imports`, `tests`,
`tested_by`, `defined_in`, `configures`, `validates`, `enforces`, `used_by`)
are pruned when the endpoint is absent. Structural `partOf` edges and active
claim `executes` edges still surface dangling endpoints so real integrity
breakage stays visible.

## Next

- Continue LLM-Wiki unit 2 with the deterministic wiki page API.
- Extend `knowledge_lint` with kind-specific checks for the new corpus when the
  wiki API and UI start depending on those fields.
- Keep the preserved `claude/llm-wiki` branch unmodified until a fresh
  integration decision is made.
