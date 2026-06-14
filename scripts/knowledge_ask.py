"""Agent knowledge ask — RAG Q&A grounded in the graph, LLM opt-in (sub-project #4).

Retrieval and context assembly are deterministic and always run: a question is
tokenised, matched against the graph (#1) across terms, and each hit is expanded
into a grounded context pack (root + neighbors + backlinks) with citations. That
pack IS the default answer — an agent reasons over it with zero model spend. The
``--llm`` flag adds a synthesized prose answer only when a provider key is present
(repo convention: OPENAI_API_KEY / ANTHROPIC_API_KEY); otherwise it degrades to the
deterministic pack with a note. No network calls happen unless --llm is set AND a
provider is configured.

CLI:
  python scripts/knowledge_ask.py ask "how is claim reaping concurrency-safe?" [--k 5] [--llm] [--json]
  python scripts/knowledge_ask.py ask "..." --graph path/to/KNOWLEDGE-GRAPH.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import knowledge_graph as kg

_STOPWORDS = {
    "the", "and", "for", "are", "was", "how", "why", "what", "when", "where", "who",
    "does", "did", "can", "could", "would", "should", "into", "with", "from", "this",
    "that", "these", "those", "has", "have", "had", "its", "our", "you", "your", "all",
    "any", "out", "via", "use", "used", "using", "made", "make",
}
_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")

Synthesizer = Callable[[str, list[dict[str, Any]]], str]


def _terms(question: str) -> list[str]:
    out: list[str] = []
    for raw in _WORD_RE.findall((question or "").lower()):
        if len(raw) >= 3 and raw not in _STOPWORDS and raw not in out:
            out.append(raw)
    return out


def retrieve(graph: dict, idx: kg.GraphIndex, question: str, *, k: int = 5) -> list[dict]:
    """Deterministic multi-term retrieval: score entities by distinct matching terms
    (weighted by per-term search rank), return the top-k seed nodes."""
    scores: dict[str, float] = defaultdict(float)
    for term in _terms(question):
        hits = kg.search(graph, term, limit=20)
        for rank, node in enumerate(hits):
            eid = str(node.get("id") or "")
            if eid:
                scores[eid] += 1.0 + 1.0 / (rank + 1)  # term-match + rank weight
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    seeds: list[dict] = []
    for eid, _ in ranked[:k]:
        node = idx.by_id.get(eid)
        if node:
            seeds.append(node)
    return seeds


def _provider_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


def _summarize_node(node: dict | None) -> str:
    if not node:
        return "?"
    return f"{node.get('id')} ({node.get('kind')}): {node.get('title', '')}".strip()


def _build_prompt(question: str, context: list[dict[str, Any]]) -> str:
    lines = [
        "You are answering from a knowledge graph. Use ONLY the context below.",
        "Cite the entity ids you rely on in square brackets, e.g. [TASK-AR-1].",
        "If the context is insufficient, say so plainly.",
        "",
        f"Question: {question}",
        "",
        "Context:",
    ]
    for pack in context:
        root = pack.get("root") or {}
        lines.append(f"- {_summarize_node(root)}")
        for n in pack.get("neighbors", []):
            lines.append(f"    related: {_summarize_node(n)}")
        for b in pack.get("backlinks", []):
            lines.append(f"    backlink: {_summarize_node(b)}")
    lines += ["", "Answer:"]
    return "\n".join(lines)


def _default_synthesizer(question: str, context: list[dict[str, Any]]) -> str:
    """Lazy, optional provider call. Imported only when invoked so the module never
    hard-depends on an SDK; raises if unavailable so answer() can degrade."""
    prompt = _build_prompt(question, context)
    import anthropic  # noqa: F401  (lazy, optional)

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = getattr(msg, "content", []) or []
    return "".join(getattr(p, "text", "") for p in parts).strip()


def answer(
    root: Path,
    graph: dict,
    question: str,
    *,
    k: int = 5,
    use_llm: bool = False,
    synthesizer: Synthesizer | None = None,
) -> dict[str, Any]:
    idx = kg.build_index(graph)
    seeds = retrieve(graph, idx, question, k=k)
    citations = [str(s.get("id")) for s in seeds]
    context = [kg.context_pack(idx, cid) for cid in citations]

    result: dict[str, Any] = {
        "question": question,
        "mode": "deterministic",
        "citations": citations,
        "context": context,
        "answer": None,
        "note": None,
    }
    if not use_llm:
        return result

    fn = synthesizer or (_default_synthesizer if _provider_configured() else None)
    if fn is None:
        result["note"] = "llm-requested-but-no-provider: returning deterministic evidence pack"
        return result
    try:
        result["answer"] = fn(question, context)
        result["mode"] = "llm"
    except Exception as exc:  # provider/SDK failure → degrade, never crash the agent
        result["note"] = f"llm-synthesis-failed: {type(exc).__name__}; returning deterministic pack"
    return result


# --------------------------------------------------------------------------- CLI


def _load_graph(args: argparse.Namespace) -> dict:
    if getattr(args, "graph", None):
        return json.loads(Path(args.graph).read_text(encoding="utf-8"))
    root = Path(args.root)
    from_file = root / kg.GRAPH_REL
    if getattr(args, "from_file", False) and from_file.exists():
        return json.loads(from_file.read_text(encoding="utf-8"))
    return kg.build_graph(root, git_limit=getattr(args, "git_limit", 200))


def _render_human(res: dict[str, Any]) -> str:
    lines = [f"Q: {res['question']}"]
    if res.get("answer"):
        lines += ["", res["answer"], ""]
    elif res.get("note"):
        lines.append(f"(note: {res['note']})")
    lines.append("Citations:")
    for pack in res["context"]:
        root = pack.get("root") or {}
        lines.append(f"  - {_summarize_node(root)}")
        rel = [n.get("id") for n in pack.get("neighbors", [])]
        bl = [b.get("id") for b in pack.get("backlinks", [])]
        if rel:
            lines.append(f"      related: {', '.join(rel)}")
        if bl:
            lines.append(f"      backlinks: {', '.join(bl)}")
    if not res["citations"]:
        lines.append("  (no matching entities)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent knowledge ask — RAG Q&A, LLM opt-in")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--git-limit", type=int, default=200)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="answer a question grounded in the graph")
    ask.add_argument("question")
    ask.add_argument("--graph", default=None, help="explicit KNOWLEDGE-GRAPH.json path")
    ask.add_argument("--from-file", action="store_true")
    ask.add_argument("--k", type=int, default=5)
    ask.add_argument("--llm", action="store_true", help="opt-in LLM synthesis (needs provider key)")
    ask.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command != "ask":
        parser.error("unknown command")

    graph = _load_graph(args)
    res = answer(Path(args.root), graph, args.question, k=args.k, use_llm=args.llm)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(_render_human(res))
    return 0


if __name__ == "__main__":
    kg.enable_utf8_stdout()  # graph titles carry unicode; avoid cp949 console crashes
    raise SystemExit(main())
