---
type: spec
id: SPEC-2026-06-14-knowledge-ask
audience: owner
status: active
tags: [knowledge-graph, rag, qa, llm-optin, agent-primitive]
---

# Knowledge Ask — sub-project #4 (RAG Q&A, LLM opt-in)

## Bottom Line

- Summary: `knowledge_ask` answers a natural-language question grounded in the knowledge graph (#1). **Retrieval and context assembly are deterministic and always run**; LLM prose synthesis is an **opt-in** that degrades gracefully to the deterministic evidence pack when no provider is configured.
- Boundary: deterministic-first. The default answer IS the cited evidence pack — an agent can reason over it directly with zero model spend. `--llm` adds a synthesized prose answer only when a provider key is present; otherwise it returns the same deterministic pack plus a `note`. No network calls in tests/CI.

## Why

`knowledge_graph.search` is substring-only — a real question ("how is claim reaping made concurrency-safe?") substring-matches poorly. Ask adds a deterministic multi-term retriever over the graph, expands each hit into a grounded context pack (root + neighbors + backlinks), and returns citations. That pack is the product; an LLM is an optional renderer over it, matching the repo's automation-first, provider-optional posture (cf. `provider_live_eval_runner`: `provider_configured = OPENAI_API_KEY or ANTHROPIC_API_KEY`).

## Retrieval (deterministic)

- `_terms(question)` — lowercase tokens, drop stopwords and len<3.
- `retrieve(graph, idx, question, *, k=5)` — for each term, run `kg.search`; aggregate per-entity score = (# distinct matching terms) weighted by `kg.search` rank position. Return top-`k` seed nodes (id-stable tiebreak).
- For each seed, `kg.context_pack(idx, id)` → `{root, neighbors, backlinks}`.

## Answer

- `answer(root, graph, question, *, k=5, use_llm=False, synthesizer=None) -> dict`
  - `{question, mode, citations:[id...], context:[pack...], answer:str|None, note:str|None}`
  - **deterministic** (default): `answer=None`, `mode="deterministic"`.
  - **llm** (`use_llm=True`): use `synthesizer` if injected, else `_default_synthesizer` when `_provider_configured()`; otherwise degrade → deterministic pack + `note="llm-requested-but-no-provider"`.
- `_provider_configured()` — env `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` (repo convention).
- `_build_prompt(question, context)` — grounded RAG prompt: answer using ONLY the provided graph context, cite entity ids, say so if insufficient. Deterministic string (testable without a model).
- `_default_synthesizer(question, context)` — lazy-import the provider SDK behind try/except; never imported at module load. If the SDK/key is unavailable it raises, and `answer` degrades. (Real but fully optional.)

## CLI

```
python scripts/knowledge_ask.py ask "how is claim reaping concurrency-safe?" [--k 5] [--llm] [--json]
```

- Default prints the cited evidence (citations + per-citation related/backlink ids).
- `--llm` adds the synthesized answer when a provider is configured, else prints the degrade note and the evidence.
- `--json` emits the full `answer()` dict.

## Wiring

Mirrored to `templates/project/scripts/` (regen fixture lock). Not added to any blocking gate (it's a query tool, not a gate).

## Test (TDD)

`tests/test_knowledge_ask.py`: `_terms` stopword/length filtering; `retrieve` ranks the on-topic entity first and respects `k`; `answer` deterministic shape (answer=None, citations non-empty); injected synthesizer drives the llm path (answer set, mode="llm"); `use_llm` with no provider + no synthesizer degrades (note set, answer=None); `_build_prompt` includes the question and a cited id; CLI deterministic exit 0 + json shape.
