# Knowledge Graph (agent-first) — design

Owner-approved 2026-06-14. Sub-project **#1** of "product 전용 LLM wiki + graph".

## Why
The product's main user is the **agent**, not a human. Agents need an
agent-optimized knowledge substrate (memory / ingest / digest / query / search /
lint over a graph), deterministic-first with LLM opt-in. Today the primitives are
scattered (`entity_catalog`, `kedb_search`, `query_tasks/reports`,
`secretary_digest`, `agent_context_packet`, `context_knowledge_gate`,
`ENTITY-CATALOG.json`). This unifies the graph + query slice.

## Decomposition (full vision)
1. **Graph substrate + ingest + query** ← this spec (no LLM).
2. digest + memory (agent-consumable wiki pages) — LLM opt-in.
3. lint + freshness gate over the graph.
4. RAG Q&A (retrieve from graph → cited answer) — LLM opt-in.
5. UI graph/wiki view (human; lowest priority — agents are the main user).

## #1 scope
A self-contained typed entity graph using the same envelope as `entity_catalog`
(`{kind, id, title, metadata, relations}`, typed directional relations), so it
reconciles with the Decision Console's `entity_catalog` when that lands on `main`
(this is its deterministic **superset**: +git/+claims ingest, traversal/backlinks/
path/context-pack query, in-memory index).

- **Self-contained (decision):** `entity_catalog.py` / `ENTITY-CATALOG.json` live on
  an unmerged branch (Decision Console), not `main`. To stay mergeable + unblocked,
  `knowledge_graph` does NOT import `entity_catalog`; it ingests raw sources
  directly. Reconcile (delegate to / subsume `entity_catalog`) when that lands.

### Ingest (deterministic, v1)
- work items — `WORK-ITEM-CLASSIFICATION.json` (initiative/taskset/task/unit, `partOf`).
- reviews/decisions — `reviews/*.md` (kind by prefix; `references` task refs in name).
- git/PR/commit — `git log` (commit nodes; `mentions`→task, `partOf`→`PR-<n>` from `(#n)`).
- claims — `agents/runtime/task_claims/*.json` (claim nodes; `executes`→task).

### Storage (hybrid)
Canonical `agents/project/work-items/KNOWLEDGE-GRAPH.json` via `build --write`
(reviewable snapshot); query commands rebuild from sources + build an **in-memory
index** (forward/backward adjacency + text). SQLite/FTS is the growth path.

### Query API (agent-first CLI/JSON)
`get`, `search` (scoped `kind:`/`@`, ranked), `neighbors` (forward, depth/rel),
`backlinks` (reverse), `path` (BFS shortest), `context-pack` (root + neighbors +
backlinks subgraph — the agent's "what do I need to know about X"), `check`
(dangling relations).

### Out of scope (#1)
digest/memory/wiki pages, LLM, lint-beyond-dangling, UI, RAG.

## Testing
`tests/test_knowledge_graph.py` — index/traversal/backlinks/path/context-pack/
search/check + per-source ingest (incl. a tmp git repo) + build + CLI. Real-repo
smoke: build = ~929 nodes / ~442 edges; queries resolve.
