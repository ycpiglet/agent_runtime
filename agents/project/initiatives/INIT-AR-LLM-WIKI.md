---
title: LLM-Wiki + Graph (agent + human)
status: active
owner: lead-engineer
task_set_id: TASKSET-AR-LLM-WIKI
created_at: 2026-06-17T22:30:00+09:00
updated_at: 2026-06-18T23:30:00+09:00
---

# INIT-AR-LLM-WIKI - LLM-Wiki + Graph (agent + human)

Extend the merged knowledge stack (`knowledge_graph`, `knowledge_digest`,
`knowledge_lint`, and `knowledge_ask`) with a human-browsable wiki surface and
expanded graph corpus so both agents and people can search, browse, and
understand product structure, docs, config, code, and runtime assets through
their relationships.

The core stance is deterministic-first and LLM opt-in: the console Wiki view is
backed by `/api/wiki/*` routes that reuse the existing graph/digest/ask modules.
The per-page mini-graph is the primary insight lens because it is contextual and
bounded, while the global knowledge graph remains the secondary overview.

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`
- Preservation source: `claude/llm-wiki` at `5846e40`
- Current-line registration note: imported after design-system tasksets occupied
  registry orders `618` through `623`; this taskset uses order `624`.

## Units

| Task | Status | Owner | Scope |
| --- | --- | --- | --- |
| `TASK-AR-590` | completed | worker-engineer | Expand the graph corpus across docs/code/config/assets. |
| `TASK-AR-591` | completed | worker-engineer | Add deterministic `/api/wiki/page` read envelope. |
| `TASK-AR-592` | completed | uiux | Add console Wiki page view and local mini-graph. |
| `TASK-AR-593` | planned | uiux | Add deterministic search + ask API/UI with LLM opt-in. |
| `TASK-AR-594` | planned | uiux | Refine the per-page mini-graph lens and typed controls. |
| `TASK-AR-595` | planned | uiux | Promote Wiki/Search as a core navigation hub with cross-links. |
| `TASK-AR-596` | planned | qa | Extend lint and close the taskset with W4b evidence. |

## Boundary

The preserved `claude/llm-wiki` branch remains an archival source, not an
implementation branch to mutate from the root checkout. Current-line work uses
fresh records here and must preserve existing console maturity behavior.
