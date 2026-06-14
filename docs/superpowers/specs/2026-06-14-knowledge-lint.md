---
type: spec
id: SPEC-2026-06-14-knowledge-lint
audience: owner
status: active
tags: [knowledge-graph, lint, freshness, gate, agent-primitive]
---

# Knowledge Lint — sub-project #3

## Bottom Line

- Summary: `knowledge_lint` is the **lint** primitive of the agent knowledge stack. It validates the knowledge graph (#1) and the digest memory pages (#2) for integrity + **freshness** issues an agent would otherwise act on blindly, with `block`/`watch` severity and a CI-wireable exit code.
- Boundary: deterministic-only. No LLM. Reads the live graph + persisted memory pages; it does not mutate them (reporting gate, not a fixer). Re-`remember` is the agent's remediation, not lint's job.

## Why

`knowledge_graph.check_graph` only checks `schema` + dangling edges, and silently hides duplicate ids (set-dedup) and memory staleness (it never looks at memory). The agent's real failure mode is **acting on a stale or structurally-broken page**: a remembered digest whose graph fingerprint drifted, or a memory page for an entity that no longer exists. Lint makes those first-class, severity-classified findings.

## Checks

| code | severity | meaning |
| --- | --- | --- |
| `stale-memory` | block | a remembered page's stored fingerprint ≠ live graph fingerprint (#2 `is_stale`) |
| `orphan-memory` | block | a remembered page whose entity is absent from the live graph |
| `duplicate-id` | block | the same `id` appears on >1 node (build_index silently overwrites) |
| `dangling-edge` | block if rel ∈ {partOf, dependsOn, blocks}; else watch | a forward edge whose target is not a node |
| `orphan-entity` | watch | a node with no forward and no backward edges (isolated knowledge) |

`STRUCTURAL_RELS = {"partOf", "dependsOn", "blocks"}` — a broken structural edge corrupts task/taskset topology (block); a dangling `mentions`/`references` from a git commit or review is informational (watch).

## API (`scripts/knowledge_lint.py`)

- `Finding` — `{"code", "severity", "id", "detail"}` dict.
- `lint_structural(graph, idx) -> list[Finding]` — duplicate-id (from raw `graph["nodes"]`), dangling-edge, orphan-entity.
- `lint_memory(root, idx) -> list[Finding]` — orphan-memory, stale-memory (reuses `knowledge_digest`).
- `lint(root, graph) -> list[Finding]` — builds the index, combines both, sorted by (severity, code, id) for stable output.
- `summarize(findings) -> {"block": n, "watch": n, "total": n}`.

## CLI

```
python scripts/knowledge_lint.py check [--strict] [--json]   # exit 1 if any block (or any finding under --strict)
python scripts/knowledge_lint.py check --memory-only         # skip structural (fast freshness probe)
```

- Default: exit 1 iff a `block` finding exists; `watch` findings print but do not fail.
- `--strict`: any finding (incl. watch) fails — for an opt-in stricter gate lane.
- Human output mirrors the repo gate style (`knowledge-lint: pass` / one line per finding); `--json` emits `{findings, summary}`.

## Wiring

Mirrored to `templates/project/scripts/` (regen fixture lock). Not auto-added to the blocking governance chain in this PR — registered as available, owner decides the lane. Designed so `check` (block-only) can later drop into `owner_governance_gate` as a non-blocking watch step.

## Test (TDD)

`tests/test_knowledge_lint.py`: duplicate-id, dangling structural=block vs informational=watch, orphan-entity watch, stale-memory + orphan-memory via tmp memory dir, `lint` combine+sort, summarize counts, CLI exit codes (clean=0, block=1, --strict watch=1).
