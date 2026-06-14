"""Agent knowledge lint — integrity + freshness gate (sub-project #3).

Builds on knowledge_graph (#1) and knowledge_digest (#2). Where ``check_graph``
only validates schema + dangling edges, lint adds the failure modes an agent
actually trips on: **stale** or **orphaned** memory pages (it acted on a digest
whose graph drifted), silently-overwritten **duplicate ids**, and **orphan**
entities — each a severity-classified, CI-wireable finding. Deterministic; this
is a reporting gate, not a fixer (re-``remember`` is the agent's remediation).

CLI:
  python scripts/knowledge_lint.py check [--strict] [--json]
  python scripts/knowledge_lint.py check --memory-only
  python scripts/knowledge_lint.py check --graph path/to/KNOWLEDGE-GRAPH.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import knowledge_graph as kg
import knowledge_digest as kd

# A dangling edge of one of these relation types corrupts task/taskset topology
# (block); a dangling mentions/references from a commit or review is informational.
STRUCTURAL_RELS = {"partOf", "dependsOn", "blocks"}

# Work-item kinds that are *supposed* to participate in the topology — an isolated
# one is a planning defect worth flagging. Observational kinds (commit, claim,
# review, meeting, research, call, seminar, retro, pr) are leaves by nature, so
# their isolation is expected and must not drown the signal.
CONNECTED_KINDS = {"task", "taskset", "initiative", "unit", "verification", "domain"}

Finding = dict[str, Any]


def _finding(code: str, severity: str, eid: str, detail: str) -> Finding:
    return {"code": code, "severity": severity, "id": eid, "detail": detail}


def lint_structural(graph: dict, idx: kg.GraphIndex) -> list[Finding]:
    findings: list[Finding] = []
    nodes = graph.get("nodes", []) or []

    counts = Counter(str(n.get("id") or "") for n in nodes if n.get("id"))
    for eid, n in counts.items():
        if n > 1:
            findings.append(_finding("duplicate-id", "block", eid, f"{n} nodes share id {eid}"))

    for nid in idx.forward:
        for rel_type, target in idx.forward.get(nid, []):
            if target in idx.by_id:
                continue
            severity = "block" if rel_type in STRUCTURAL_RELS else "watch"
            findings.append(_finding("dangling-edge", severity, nid, f"{nid} -{rel_type}-> {target}"))

    for nid, node in idx.by_id.items():
        if str(node.get("kind") or "") not in CONNECTED_KINDS:
            continue
        if not idx.forward.get(nid) and not idx.backward.get(nid):
            findings.append(_finding("orphan-entity", "watch", nid, f"{nid} ({node.get('kind')}) has no relations"))

    return findings


def lint_memory(root: Path, idx: kg.GraphIndex) -> list[Finding]:
    findings: list[Finding] = []
    for eid in kd.list_memory(root):
        if eid not in idx.by_id:
            findings.append(_finding("orphan-memory", "block", eid, f"remembered {eid} absent from graph"))
        elif kd.is_stale(root, idx, eid):
            findings.append(_finding("stale-memory", "block", eid, f"remembered {eid} fingerprint drifted"))
    return findings


def _sort_key(f: Finding) -> tuple[int, str, str]:
    return (0 if f["severity"] == "block" else 1, f["code"], f["id"])


def lint(root: Path, graph: dict, *, memory_only: bool = False) -> list[Finding]:
    idx = kg.build_index(graph)
    findings = list(lint_memory(root, idx))
    if not memory_only:
        findings += lint_structural(graph, idx)
    return sorted(findings, key=_sort_key)


def summarize(findings: list[Finding]) -> dict[str, int]:
    block = sum(1 for f in findings if f["severity"] == "block")
    watch = sum(1 for f in findings if f["severity"] == "watch")
    return {"block": block, "watch": watch, "total": len(findings)}


# --------------------------------------------------------------------------- CLI


def _load_graph(args: argparse.Namespace) -> dict:
    graph_arg = getattr(args, "graph", None)
    if graph_arg:
        return json.loads(Path(graph_arg).read_text(encoding="utf-8"))
    root = Path(args.root)
    from_file = root / kg.GRAPH_REL
    if getattr(args, "from_file", False) and from_file.exists():
        return json.loads(from_file.read_text(encoding="utf-8"))
    return kg.build_graph(root, git_limit=getattr(args, "git_limit", 200))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent knowledge lint — integrity + freshness gate")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--git-limit", type=int, default=200)
    sub = parser.add_subparsers(dest="command", required=True)
    chk = sub.add_parser("check", help="lint the graph + memory")
    chk.add_argument("--graph", default=None, help="explicit KNOWLEDGE-GRAPH.json path (else build from --root)")
    chk.add_argument("--from-file", action="store_true", help="load root/KNOWLEDGE-GRAPH.json instead of rebuilding")
    chk.add_argument("--memory-only", action="store_true", help="skip structural checks (fast freshness probe)")
    chk.add_argument("--strict", action="store_true", help="fail on any finding, including watch")
    chk.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command != "check":
        parser.error("unknown command")

    graph = _load_graph(args)
    findings = lint(Path(args.root), graph, memory_only=args.memory_only)
    summary = summarize(findings)

    if args.json:
        print(json.dumps({"findings": findings, "summary": summary}, ensure_ascii=False, indent=2))
    elif not findings:
        print("knowledge-lint: pass")
    else:
        for f in findings:
            print(f"knowledge-lint: {f['severity']} {f['code']} {f['id']} — {f['detail']}")
        print(f"knowledge-lint: block={summary['block']} watch={summary['watch']} total={summary['total']}")

    fail = summary["total"] > 0 if args.strict else summary["block"] > 0
    return 1 if fail else 0


if __name__ == "__main__":
    kg.enable_utf8_stdout()
    raise SystemExit(main())
