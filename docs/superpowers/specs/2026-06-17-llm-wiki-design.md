# LLM-Wiki + Graph (agent + human) — design

Owner-approved 2026-06-17. Extends the merged knowledge stack (`knowledge_{graph,digest,lint,ask}`, PRs #143-#147, #150/#151) with a **human-browsable wiki surface** and an **expanded corpus** so that both agents and people can search, browse, and understand the product (structure, docs, resources) with their relationships.

## Why

The knowledge stack is agent-first and complete as primitives, but the human experience is missing: the only UI is a degree-ranked SVG graph (the Owner found it low-insight — "circles connected by lines, no insight"). The digest produces readable "wiki pages" but they are agent-only / on-demand / not surfaced. And the corpus only ingests project-management artifacts (work-items, reviews, commits, claims) — not the product **docs, code structure, config, or operational assets** the Owner wants mapped. This sub-project turns the engine into a real **LLM-Wiki**: contextual, cross-linked, searchable pages over the whole product, for agents and humans alike.

## What exists (do not rebuild)

- `scripts/knowledge_graph.py` — typed entity graph; ingest work-items/reviews/commits/claims; `build/neighbors/backlinks/path/context-pack/search/check`; optional `KNOWLEDGE-GRAPH.json`. Deterministic.
- `scripts/knowledge_digest.py` — per-entity markdown pages (summary + neighbors + backlinks + fingerprint); `digest/remember/recall/check`. Deterministic core.
- `scripts/knowledge_ask.py` — RAG: deterministic ranked retrieval -> context-pack -> cited evidence; `--llm` opt-in for prose. 
- `scripts/knowledge_lint.py` + `knowledge_lint_gate.py` — integrity/freshness; volume-gated in `owner_governance_gate.py`.
- Console: `/api/knowledge-graph` route + `ui_state.build_knowledge_graph_view()` (SVG, degree-ranked top-N).

All are stdlib-only and PyYAML-free. This spec **extends** them; it introduces no parallel engine.

## Decomposition (full vision, this spec)

Designed as one vision, built as seven units (each TDD + independent W4b). The whole vision is in scope; units are the delivery sequence.

## Architecture

Deterministic-first, LLM opt-in. The wiki surface is a new console view backed by new `/api/wiki/*` routes that call the existing graph/digest/ask modules. The graph is rebuilt on demand from committed sources (no new persistent store beyond the optional snapshot). One engine, two surfaces: agents via CLI/`context-pack`, humans via the console wiki.

### A. Corpus expansion (`knowledge_graph.py` ingest)

Add entity kinds + edges on top of the existing ones. All derivation is deterministic and stdlib (frontmatter via `org_model_gate.parse_frontmatter`; no PyYAML).

| New kind | Source | Node id scheme | Edges emitted |
|---|---|---|---|
| `doc` | `docs/**/*.md`, root `*_BRIEF.md`/`OPS-*.md`/`AGENT_*.md`, `README*` | `doc:<relpath>` | `references` (from `[[name]]` and path/id mentions in body), `documents` -> entity whose id appears |
| `module` / `file` | `src/agent_runtime/**`, `scripts/**` (`*.py`) | `module:<dotted>` / `file:<relpath>` | `imports` (parsed from `import`/`from` via stdlib `ast`), `tests`/`tested_by` (test file <-> target by name), `defined_in` |
| `config` / `schema` | `*.yml`, `*.toml`, `schemas/**`, `src/agent_runtime/templates/**` | `config:<relpath>` / `schema:<relpath>` | `configures` / `validates` -> referenced entity/path |
| `asset` | skills, gates, hooks, automation rules (reuse `runtime_asset_usage` registry) | `asset:<kind>/<name>` | `enforces`, `used_by` (mirror runtime_asset_usage linkage) |

Edges are typed and reversible (every edge yields a backlink). Dangling edges are tolerated by the graph and reported by lint (existing behavior). Ingest is incremental and bounded (skip binary/large files; cap body scan length).

### B. Wiki read API + page (layout A, 2-column)

`GET /api/wiki/page/:id` returns a deterministic page envelope:
`{ id, kind, title, summary, metadata{owner,status,updated_at,freshness,lineage,source}, relations:[{type,target_id,target_title,target_kind}], backlinks:[...], minigraph:{nodes,edges} }`
- `summary` comes from `knowledge_digest` (deterministic). An "Explain with AI" control calls the LLM opt-in path (lazy import; degrades to deterministic if no provider key).
- The console **Wiki view** renders layout A (Wikipedia/Notion 2-column): main column = summary + typed relationships + backlinks; right sidebar = metadata + mini-graph. Every link click navigates to the target's page (hash route `#/wiki/:id`); no dead links.

### C. Search & Ask

- `GET /api/wiki/search?q=` -> deterministic ranked results `{id,kind,title,snippet,score}` (reuse `knowledge_graph.search`). Instant, no LLM.
- `GET /api/wiki/ask?q=&llm=0|1` -> `{query, evidence:[{id,title,excerpt}], cited:[ids], answer?, llm_used:bool}` (reuse `knowledge_ask`). Default = cited evidence pack (deterministic); `llm=1` = synthesized prose if a provider key is present, else degrade with `llm_used:false`.
- A shared search/ask bar sits atop the Wiki view.

### D. Graph lens

The per-page **mini-graph** (local neighborhood: root + neighbors, typed/colored, click-to-navigate) is the primary graph value and directly answers the "no insight" complaint by being contextual and bounded. The global graph reuses the existing `/api/knowledge-graph` SVG as a secondary lens (no rebuild of that view in this spec).

### E. Navigation integration

The Wiki is a core destination in the in-flight decision-first IA nav (it satisfies the core-7 "Search/Wiki"): a single hub for search + entity pages + graph, naturally adjacent to Records. It is reachable from any entity surfaced elsewhere (e.g., an inbox item links to its wiki page).

## Constraints (hard)

- New server/ingest code is **stdlib-only and PyYAML-free** (frontmatter via `parse_frontmatter`); verified under a PyYAML-blocked pytest run.
- Console JS is **ASCII-only** (glyphs via `\uXXXX` escapes; `node --check` + cp949-safe); CSS colors are **token-only** (`var(--token)`, no raw hex/rgba).
- **Deterministic-first, LLM opt-in**: no model call unless an explicit control sets `llm=1` AND a provider key exists; always degrades gracefully.
- **No dead links**: every rendered relation/backlink resolves to a real page or is omitted.
- **Maturity-preserving**: the existing console behaviors (responsive, a11y, SSE, i18n, validation) and routes are not regressed; additive changes only.

## Build sequence (units)

1. **Corpus expansion** — extend `knowledge_graph.py` ingest with `doc/module/file/config/schema/asset` kinds + edges (`imports` via `ast`, `references` via body scan, `configures/validates/enforces/used_by`). Unit tests for each adapter.
2. **Wiki read API** — `/api/wiki/page/:id` envelope (digest summary + typed relations + backlinks + minigraph data), reusing graph/digest. Stdlib route + tests.
3. **Wiki page view (layout A)** — 2-column console view, hash route `#/wiki/:id`, click-navigation, metadata sidebar. E2E presence + DOM.
4. **Search & Ask** — `/api/wiki/search` + `/api/wiki/ask` (LLM opt-in, degrade) + shared search/ask bar UI. Tests for deterministic default + opt-in path (mocked provider).
5. **Mini-graph lens** — per-page local-neighborhood graph (typed, colored, click-to-navigate), tokenized/ASCII-safe. Tests.
6. **Nav integration** — Wiki as a core nav destination in the decision-first IA nav; cross-links from entities (e.g., inbox item -> wiki). E2E.
7. **Lint extension + closeout** — extend `knowledge_lint` for the new kinds/edges; full E2E + DOM budget; W4b + taskset closeout.

## Testing

Per unit: stdlib unit tests (ingest adapters, API envelopes) run under PyYAML-blocked simulation; console E2E via the existing `ThreadingHTTPServer` fixture (`tests/test_ui_console_e2e.py`) for routes/views; raw-hex + ASCII-only gates for any JS/CSS; live Playwright capture for visual review. Each code unit gets an independent W4b verification before closeout.

## Out of scope

LLM provider procurement/keys; replacing the global SVG graph; a standalone (non-console) wiki site; write/edit of wiki pages from the UI (read + search only); ingesting external (non-repo) resources.
