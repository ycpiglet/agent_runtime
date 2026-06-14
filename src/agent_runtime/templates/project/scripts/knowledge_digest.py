"""Agent knowledge digest + memory (sub-project #2).

Builds on knowledge_graph (#1). **digest** condenses an entity plus its graph
context (related + backlinks) into an agent-consumable page; **memory** persists
those pages under agents/runtime/knowledge/ so an agent can recall them and check
freshness before execution (a page is stale when the entity's graph fingerprint
changed). Deterministic; LLM prose over a page is a later opt-in (#4).

CLI:
  python scripts/knowledge_digest.py digest TASK-AR-1 [--json]
  python scripts/knowledge_digest.py remember TASK-AR-1
  python scripts/knowledge_digest.py recall TASK-AR-1 --json
  python scripts/knowledge_digest.py check TASK-AR-1   # exit 1 if stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import knowledge_graph as kg

PAGE_SCHEMA = "agent-runtime-knowledge-page/v1"
MEMORY_REL = "agents/runtime/knowledge/pages"


def _summary(idx: kg.GraphIndex, eid: str) -> dict[str, Any]:
    node = idx.by_id.get(eid)
    if node:
        return {"id": eid, "kind": node.get("kind"), "title": node.get("title")}
    return {"id": eid, "kind": "?", "title": eid}


def _group(edges: list[tuple[str, str]], idx: kg.GraphIndex) -> list[dict[str, Any]]:
    by_rel: dict[str, list[dict[str, Any]]] = {}
    for rel, target in edges:
        by_rel.setdefault(rel, []).append(_summary(idx, target))
    return [{"relation": rel, "entities": by_rel[rel]} for rel in sorted(by_rel)]


def fingerprint(idx: kg.GraphIndex, entity_id: str) -> str:
    node = idx.by_id.get(entity_id)
    if node is None:
        return ""
    blob = json.dumps(
        {
            "node": {k: node.get(k) for k in ("kind", "id", "title", "metadata")},
            "forward": sorted(list(e) for e in idx.forward.get(entity_id, [])),
            "backward": sorted(list(e) for e in idx.backward.get(entity_id, [])),
        },
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def build_page(idx: kg.GraphIndex, entity_id: str, *, depth: int = 1) -> dict[str, Any] | None:
    root = idx.by_id.get(entity_id)
    if root is None:
        return None
    return {
        "schema": PAGE_SCHEMA,
        "id": entity_id,
        "kind": root.get("kind"),
        "title": root.get("title"),
        "metadata": root.get("metadata", {}),
        "related": _group(kg.neighbors(idx, entity_id, depth=depth), idx),
        "backlinks": _group(kg.backlinks(idx, entity_id), idx),
        "fingerprint": fingerprint(idx, entity_id),
        "generated_at": date.today().isoformat(),
    }


def _render_group(title: str, groups: list[dict[str, Any]]) -> list[str]:
    if not groups:
        return []
    lines = [f"## {title}"]
    for group in groups:
        joined = ", ".join(f"{e['id']} ({e['kind']})" for e in group["entities"])
        lines.append(f"- {group['relation']}: {joined}")
    lines.append("")
    return lines


def render_markdown(page: dict[str, Any]) -> str:
    lines = [
        f"# {page['id']}",
        "",
        f"- kind: {page['kind']}",
        f"- title: {page['title']}",
    ]
    if page.get("metadata"):
        lines.append(f"- metadata: {json.dumps(page['metadata'], ensure_ascii=False)}")
    lines.append("")
    lines += _render_group("Related", page.get("related", []))
    lines += _render_group("Backlinks", page.get("backlinks", []))
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- memory


def _slug(eid: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", eid).strip("_") or "entity"


def _memory_dir(root: Path) -> Path:
    return Path(root) / MEMORY_REL


def remember(root: Path, idx: kg.GraphIndex, entity_id: str) -> Path | None:
    page = build_page(idx, entity_id)
    if page is None:
        return None
    directory = _memory_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    slug = _slug(entity_id)
    json_path = directory / f"{slug}.json"
    json_path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / f"{slug}.md").write_text(render_markdown(page), encoding="utf-8")
    return json_path


def recall(root: Path, entity_id: str) -> dict[str, Any] | None:
    path = _memory_dir(root) / f"{_slug(entity_id)}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def list_memory(root: Path) -> list[str]:
    directory = _memory_dir(root)
    if not directory.is_dir():
        return []
    ids: list[str] = []
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8")).get("id")
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
        if value:
            ids.append(value)
    return ids


def is_stale(root: Path, idx: kg.GraphIndex, entity_id: str) -> bool:
    recalled = recall(root, entity_id)
    if recalled is None:
        return True
    return recalled.get("fingerprint") != fingerprint(idx, entity_id)


# --------------------------------------------------------------------------- CLI


def _emit(payload: Any, as_json: bool, human: str = "") -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(human or json.dumps(payload, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=Path.cwd())
    common.add_argument("--json", action="store_true", default=False)
    common.add_argument("--git-limit", type=int, default=200)
    post = argparse.ArgumentParser(add_help=False)
    post.add_argument("--root", type=Path, default=argparse.SUPPRESS)
    post.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    post.add_argument("--git-limit", type=int, default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(description="Agent knowledge digest + memory", parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)
    p_dig = sub.add_parser("digest", parents=[post]); p_dig.add_argument("id"); p_dig.add_argument("--markdown", action="store_true")
    p_rem = sub.add_parser("remember", parents=[post]); p_rem.add_argument("id")
    p_rec = sub.add_parser("recall", parents=[post]); p_rec.add_argument("id"); p_rec.add_argument("--markdown", action="store_true")
    sub.add_parser("list", parents=[post])
    p_chk = sub.add_parser("check", parents=[post]); p_chk.add_argument("id")

    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command == "recall":
        page = recall(root, args.id)
        if page is None:
            _emit({"id": args.id, "found": False}, args.json, human=f"knowledge-digest: no memory for {args.id}")
            return 1
        _emit(page, args.json, human=render_markdown(page) if getattr(args, "markdown", False) else json.dumps(page, ensure_ascii=False))
        return 0
    if args.command == "list":
        _emit(list_memory(root), args.json, human="\n".join(list_memory(root)))
        return 0

    graph = kg.build_graph(root, git_limit=getattr(args, "git_limit", 200))
    idx = kg.build_index(graph)

    if args.command == "digest":
        page = build_page(idx, args.id)
        if page is None:
            _emit({"id": args.id, "found": False}, args.json, human=f"knowledge-digest: unknown entity {args.id}")
            return 1
        if getattr(args, "markdown", False) and not args.json:
            print(render_markdown(page))
        else:
            _emit(page, args.json, human=render_markdown(page))
        return 0
    if args.command == "remember":
        path = remember(root, idx, args.id)
        if path is None:
            _emit({"id": args.id, "found": False}, args.json, human=f"knowledge-digest: unknown entity {args.id}")
            return 1
        _emit({"id": args.id, "path": str(path)}, args.json, human=f"remembered {args.id} -> {path}")
        return 0
    if args.command == "check":
        stale = is_stale(root, idx, args.id)
        _emit({"id": args.id, "stale": stale}, args.json, human=f"knowledge-digest: {args.id} stale={stale}")
        return 1 if stale else 0
    return 0


if __name__ == "__main__":
    kg.enable_utf8_stdout()
    raise SystemExit(main())
