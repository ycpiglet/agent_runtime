# LLM-Wiki Implementation Plan - Unit 1 Registration Baseline

## Goal

Register the LLM-Wiki delivery sequence in the current line and keep it aligned
with the already-landed work:

- Unit 1: corpus expansion (`TASK-AR-590`) - completed by
  `reviews/REVIEW-2026-06-18-knowledge-graph-corpus-expansion.md`.
- Unit 2: wiki page API (`TASK-AR-591`) - completed by
  `reviews/REVIEW-2026-06-18-wiki-page-api-envelope.md`.
- Unit 3: wiki page view (`TASK-AR-592`) - completed by
  `reviews/REVIEW-2026-06-18-wiki-page-view.md`.
- Unit 4: search + ask (`TASK-AR-593`) - next implementation unit.
- Unit 5: mini-graph lens refinement (`TASK-AR-594`) - follow-on visual/insight
  unit.
- Unit 6: nav integration (`TASK-AR-595`) - promote Search/Wiki as a core hub.
- Unit 7: lint extension + closeout (`TASK-AR-596`) - final QA/doc-steward
  closeout.

## Current-Line Import Rule

The original registration branch is preserved at `claude/llm-wiki` and should
not be mutated directly. This current-line registration imports its intent while
respecting newer taskset registry orders. The taskset order is `624` because
orders `618` through `623` are already assigned to design-system tasksets.

## Interfaces

### `/api/wiki/page`

Already implemented. It returns a deterministic page envelope:

```json
{
  "id": "TASK-AR-1",
  "kind": "task",
  "title": "Example",
  "summary": "...",
  "metadata": {},
  "relations": [],
  "backlinks": [],
  "minigraph": {"nodes": [], "edges": []}
}
```

### `/api/wiki/search`

Planned for `TASK-AR-593`. It should return deterministic ranked results:

```json
{
  "resource": "wiki_search",
  "query": "string",
  "items": [
    {"id": "TASK-AR-1", "kind": "task", "title": "Title", "snippet": "...", "score": 1.0}
  ],
  "total": 1
}
```

### `/api/wiki/ask`

Planned for `TASK-AR-593`. Default is deterministic evidence-only. `llm=1` is
opt-in and must degrade to deterministic evidence if provider configuration is
missing:

```json
{
  "resource": "wiki_ask",
  "query": "string",
  "llm_used": false,
  "answer": "",
  "cited": ["TASK-AR-1"],
  "evidence": [{"id": "TASK-AR-1", "title": "Title", "excerpt": "..."}]
}
```

## Constraints

- Deterministic-first; no model call unless `llm=1` is explicit and a provider
  key is available.
- Stdlib-only server paths; PyYAML-free.
- Console JS remains ASCII-safe and `node --check` clean.
- CSS uses design tokens, not raw color literals.
- Wiki links must resolve to real pages or be omitted.
- Preserve current responsive, accessibility, SSE, i18n, and validation
  behavior.

## Verification

For registration import:

- `python scripts/backlog_board.py --write`
- `python scripts/work_item_classifier.py --write`
- `python scripts/entity_catalog.py --write`
- `python scripts/evidence_index_generator.py --write`
- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`
- `python scripts/knowledge_graph.py check --json --git-limit 0`

For `TASK-AR-593`:

- Unit tests for `/api/wiki/search` and `/api/wiki/ask`.
- UI console tests for the shared Wiki search/ask controls.
- Existing wiki/knowledge regression suite.
- Owner governance gate before closeout.
