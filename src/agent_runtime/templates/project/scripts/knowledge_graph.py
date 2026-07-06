"""Agent-first knowledge graph: substrate + ingest + query (sub-project #1).

A self-contained typed entity graph over the product's artifacts, for AGENTS (the
primary user) to ingest and query the product's knowledge. Nodes use the same
envelope as entity_catalog -- ``{kind, id, title, metadata, relations}`` with typed
directional relations -- so this reconciles with the Decision Console's
entity_catalog when that lands on main (this is its deterministic superset: more
ingest sources + traversal/backlinks/path/context-pack query + an in-memory index).

Deterministic, no LLM (digest/memory/lint/RAG/UI are later sub-projects #2-5).

Ingest sources (v1): work items (WORK-ITEM-CLASSIFICATION.json), reviews/decisions
(reviews/*.md), git/PR/commit (git log), claims (agents/runtime/task_claims/*.json).

Storage (hybrid): ``build --write`` persists a canonical
agents/project/work-items/KNOWLEDGE-GRAPH.json (reviewable/diffable); query commands
rebuild from sources and build an in-memory index (forward/backward adjacency +
text). SQLite/FTS is the documented growth path.

CLI:
  python scripts/knowledge_graph.py build --write
  python scripts/knowledge_graph.py neighbors TASK-AR-1 --json
  python scripts/knowledge_graph.py context-pack TASK-AR-1 --json
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA = "agent-runtime-knowledge-graph/v1"
GRAPH_REL = "agents/project/work-items/KNOWLEDGE-GRAPH.json"
DOMAINS_REL = "agents/project/work-items/DOMAINS.json"

TASK_REF_RE = re.compile(r"TASK-AR-[0-9]+")
# Work-item entity ids a narrative record may cite in its body (tasks, tasksets,
# initiatives). Used to wire review/meeting -> work-item `references` edges so
# digest backlinks and ask grounding light up (previously bodies were not scanned).
ENTITY_REF_RE = re.compile(r"\b(?:TASK-AR-[0-9]+|TASKSET-[A-Z0-9][A-Z0-9-]+|INIT-[A-Z0-9][A-Z0-9-]+)\b")
WIKI_LINK_RE = re.compile(r"\[\[([^\]\n]+)\]\]")
MAX_BODY_REFS = 40
MAX_TEXT_SCAN_CHARS = 200_000
PR_RE = re.compile(r"\(#(\d+)\)")
REVIEW_DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
REVIEW_KIND_BY_PREFIX = {
    "W4B": "verification",
    "VERIFY": "verification",
    "COUNCIL": "council",
    "SEMINAR": "seminar",
    "MEETING": "meeting",
    "RESEARCH": "research",
    "REVIEW": "review",
    "GOVERNANCE": "review",
    "RETRO": "retro",
    "COMPOUND": "compound",
    "CALL": "call",
}
ACTIVE_CLAIM_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working", "active", "running"}
SOFT_REL_TYPES = {
    "references",
    "documents",
    "imports",
    "tests",
    "tested_by",
    "defined_in",
    "configures",
    "validates",
    "enforces",
    "used_by",
}


def enable_utf8_stdout() -> None:
    """Reconfigure stdout/stderr to UTF-8 so entity titles (em-dashes, Korean) and the
    `—` in lint output don't crash on a cp949/legacy console. Best-effort no-op where
    unsupported. Shared by the knowledge_* CLIs; call from their __main__."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError, OSError):
            pass


def _node(kind: str, eid: str, title: str = "", *, metadata: dict | None = None, relations: list | None = None) -> dict:
    return {"kind": kind, "id": eid, "title": title or eid, "metadata": metadata or {}, "relations": relations or []}


def _rel(rel_type: str, target: str) -> dict:
    return {"type": rel_type, "target": target}


def _dedupe_relations(relations: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for relation in relations:
        rel_type = str(relation.get("type") or "")
        target = str(relation.get("target") or "")
        if not rel_type or not target or (rel_type, target) in seen:
            continue
        seen.add((rel_type, target))
        unique.append({"type": rel_type, "target": target})
    return unique


def _repo_rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def _read_scan_text(path: Path) -> str:
    return _read_text(path)[:MAX_TEXT_SCAN_CHARS]


# --------------------------------------------------------------------------- ingest


def ingest_work_items(root: Path) -> list[dict]:
    path = Path(root) / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    nodes: list[dict] = []
    for record in payload.get("records", []):
        eid = str(record.get("id") or "").strip()
        if not eid:
            continue
        relations = []
        parent = str(record.get("parent_id") or "").strip()
        if parent:
            relations.append(_rel("partOf", parent))
        nodes.append(_node(
            str(record.get("level") or "work_item"), eid, str(record.get("title") or eid),
            metadata={"ordinal": record.get("number"), "status": record.get("status"), "path": record.get("path")},
            relations=relations,
        ))
    return nodes


def ingest_reviews(root: Path) -> list[dict]:
    reviews_dir = Path(root) / "reviews"
    if not reviews_dir.is_dir():
        return []
    nodes: list[dict] = []
    for path in sorted(reviews_dir.glob("*.md")):
        name = path.stem
        if name.upper() == "INDEX":
            continue
        prefix = name.split("-", 1)[0].upper()
        kind = REVIEW_KIND_BY_PREFIX.get(prefix, "review")
        date_match = REVIEW_DATE_RE.search(name)
        refs = _reference_targets(name, _read_text(path), self_id=name)
        nodes.append(_node(
            kind, name, name,
            metadata={"date": date_match.group(1) if date_match else None, "path": f"reviews/{path.name}"},
            relations=[_rel("references", ref) for ref in refs],
        ))
    return nodes


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _reference_targets(name: str, body: str, *, self_id: str = "") -> list[str]:
    """Work-item ids cited in a record's filename and body, deduped, self excluded,
    capped at MAX_BODY_REFS for stable fan-out. Sorted for deterministic output."""
    found = set(ENTITY_REF_RE.findall(name)) | set(ENTITY_REF_RE.findall(body))
    found.discard(self_id)
    return sorted(found)[:MAX_BODY_REFS]


def _markdown_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return fallback


def _is_doc_rel(rel: str) -> bool:
    path = Path(rel)
    name = path.name
    if rel.startswith("docs/") and name.lower().endswith(".md"):
        return True
    if "/" in rel:
        return False
    upper = name.upper()
    return (
        upper.startswith("README")
        or upper == "AGENTS.MD"
        or upper.startswith("OPS-") and upper.endswith(".MD")
        or upper.startswith("AGENT_") and upper.endswith(".MD")
        or upper.endswith("_BRIEF.MD")
    )


def _doc_id(rel: str) -> str:
    return f"doc:{rel}"


def _iter_doc_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        paths.update(path for path in docs_dir.rglob("*.md") if path.is_file())
    for pattern in ("README*", "*_BRIEF.md", "OPS-*.md", "AGENT_*.md", "AGENTS.md"):
        paths.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(paths, key=lambda path: _repo_rel(root, path))


def ingest_docs(root: Path) -> list[dict]:
    records: list[tuple[Path, str, str, str]] = []
    aliases: dict[str, str] = {}
    for path in _iter_doc_paths(root):
        rel = _repo_rel(root, path)
        text = _read_scan_text(path)
        title = _markdown_title(text, rel)
        eid = _doc_id(rel)
        records.append((path, rel, text, title))
        for alias in {rel, rel.removesuffix(".md"), Path(rel).stem, title}:
            normalized = alias.strip().lower()
            if normalized:
                aliases.setdefault(normalized, eid)

    nodes: list[dict] = []
    for _path, rel, text, title in records:
        eid = _doc_id(rel)
        relations: list[dict] = []
        for ref in _reference_targets(rel, text, self_id=eid):
            relations.append(_rel("references", ref))
            relations.append(_rel("documents", ref))
        for match in WIKI_LINK_RE.finditer(text):
            label = match.group(1).split("|", 1)[0].strip()
            target = aliases.get(label.lower()) or aliases.get(label.removesuffix(".md").lower())
            if target and target != eid:
                relations.append(_rel("references", target))
        nodes.append(_node("doc", eid, title, metadata={"path": rel}, relations=_dedupe_relations(relations)))
    return nodes


def _python_source_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for rel_base in ("scripts", "src/agent_runtime", "tests"):
        base = root / rel_base
        if base.is_dir():
            paths.update(path for path in base.rglob("*.py") if path.is_file())
    return sorted(paths, key=lambda path: _repo_rel(root, path))


def _module_name_for_rel(rel: str) -> str:
    dotted = rel.removesuffix(".py").replace("/", ".")
    if dotted.endswith(".__init__"):
        dotted = dotted[: -len(".__init__")]
    return dotted


def _module_id_for_rel(rel: str) -> str:
    return f"module:{_module_name_for_rel(rel)}"


def _file_id(rel: str) -> str:
    return f"file:{rel}"


def _module_aliases(rel: str) -> set[str]:
    dotted = _module_name_for_rel(rel)
    aliases = {dotted}
    if dotted.startswith("scripts."):
        aliases.add(dotted.split(".", 1)[1])
    if dotted.startswith("src.agent_runtime."):
        aliases.add("agent_runtime." + dotted.removeprefix("src.agent_runtime."))
    elif dotted == "src.agent_runtime":
        aliases.add("agent_runtime")
    return {alias for alias in aliases if alias}


def _import_targets(path: Path, alias_map: dict[str, str]) -> list[str]:
    try:
        tree = ast.parse(_read_text(path))
    except SyntaxError:
        return []
    targets: set[str] = set()
    for node in ast.walk(tree):
        candidates: list[str] = []
        if isinstance(node, ast.Import):
            candidates.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            module = node.module or ""
            if module:
                candidates.append(module)
                for alias in node.names:
                    if alias.name != "*":
                        candidates.append(f"{module}.{alias.name}")
        for candidate in candidates:
            target = alias_map.get(candidate)
            if target:
                targets.add(target)
    return sorted(targets)


def ingest_code_modules(root: Path) -> list[dict]:
    records: list[tuple[Path, str, str, str]] = []
    alias_map: dict[str, str] = {}
    by_stem: dict[str, list[str]] = {}
    for path in _python_source_paths(root):
        rel = _repo_rel(root, path)
        module_id = _module_id_for_rel(rel)
        file_id = _file_id(rel)
        records.append((path, rel, module_id, file_id))
        for alias in _module_aliases(rel):
            alias_map.setdefault(alias, module_id)
        by_stem.setdefault(path.stem, []).append(module_id)

    modules: dict[str, dict] = {}
    files: dict[str, dict] = {}
    for path, rel, module_id, file_id in records:
        files[file_id] = _node("file", file_id, rel, metadata={"path": rel})
        imports = [_rel("imports", target) for target in _import_targets(path, alias_map) if target != module_id]
        modules[module_id] = _node(
            "module",
            module_id,
            _module_name_for_rel(rel),
            metadata={"path": rel},
            relations=_dedupe_relations([_rel("defined_in", file_id), *imports]),
        )

    for _path, rel, module_id, _file_id_value in records:
        if not rel.startswith("tests/test_"):
            continue
        target_stem = Path(rel).stem.removeprefix("test_")
        for target in sorted(set(by_stem.get(target_stem, []))):
            if target == module_id:
                continue
            modules[module_id]["relations"].append(_rel("tests", target))
            modules[target]["relations"].append(_rel("tested_by", module_id))

    return [*files.values(), *modules.values()]


def _config_schema_kind(rel: str) -> str:
    name = Path(rel).name.lower()
    if rel.startswith("schemas/") or name.endswith(".schema.json"):
        return "schema"
    return "config"


def _config_schema_id(rel: str) -> str:
    kind = _config_schema_kind(rel)
    return f"{kind}:{rel}"


def _iter_config_schema_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in ("*.yml", "*.yaml", "*.toml"):
        paths.update(path for path in root.glob(pattern) if path.is_file())
    hooks = root / ".codex" / "hooks.json"
    if hooks.is_file():
        paths.add(hooks)
    for base_rel in ("schemas", "src/agent_runtime/templates"):
        base = root / base_rel
        if base.is_dir():
            paths.update(
                path for path in base.rglob("*")
                if path.is_file() and path.suffix.lower() in {".json", ".yml", ".yaml", ".toml"}
            )
    return sorted(paths, key=lambda path: _repo_rel(root, path))


def ingest_configs_and_schemas(root: Path) -> list[dict]:
    nodes: list[dict] = []
    for path in _iter_config_schema_paths(root):
        rel = _repo_rel(root, path)
        kind = _config_schema_kind(rel)
        edge_type = "validates" if kind == "schema" else "configures"
        refs = _reference_targets(rel, _read_scan_text(path), self_id="")
        nodes.append(_node(
            kind,
            _config_schema_id(rel),
            rel,
            metadata={"path": rel},
            relations=_dedupe_relations([_rel(edge_type, ref) for ref in refs]),
        ))
    return nodes


def _node_id_for_rel_path(rel: str) -> str | None:
    rel = rel.replace("\\", "/")
    if rel.endswith(".py") and (rel.startswith("scripts/") or rel.startswith("src/agent_runtime/") or rel.startswith("tests/")):
        return _file_id(rel)
    if _is_doc_rel(rel):
        return _doc_id(rel)
    if rel.startswith("reviews/") and rel.endswith(".md"):
        return Path(rel).stem
    if (
        rel.startswith("schemas/")
        or rel.startswith("src/agent_runtime/templates/")
        or Path(rel).suffix.lower() in {".yml", ".yaml", ".toml"}
        or rel == ".codex/hooks.json"
    ):
        return _config_schema_id(rel)
    return None


def _asset_node_id(kind: str, asset_id: str) -> str:
    clean = asset_id.strip().replace("\\", "/").replace(":", "_")
    prefix = f"{kind}."
    if clean.startswith(prefix):
        clean = clean[len(prefix):]
    clean = clean.replace(".", "/")
    return f"asset:{kind}/{clean}"


def ingest_assets(root: Path) -> list[dict]:
    try:
        import runtime_asset_usage
    except ImportError:
        return []

    registry_path = root / runtime_asset_usage.REGISTRY_PATH
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(registry, dict):
        return []
    findings, metrics = runtime_asset_usage.analyze(root)
    _ = findings
    by_id = {metric.asset_id: metric for metric in metrics}
    nodes: list[dict] = []
    for asset in registry.get("assets", []) or []:
        if not isinstance(asset, dict):
            continue
        asset_id = str(asset.get("id") or "").strip()
        kind = str(asset.get("kind") or "asset").strip() or "asset"
        if not asset_id:
            continue
        metric = by_id.get(asset_id)
        metadata = {
            "asset_id": asset_id,
            "status": asset.get("status"),
            "lifecycle": asset.get("lifecycle"),
        }
        if metric:
            metadata.update({
                "path_count": metric.path_count,
                "evidence_count": metric.evidence_count,
                "usage_count": metric.usage_count,
                "reuse": metric.distinct_evidence_hits,
            })
        relations: list[dict] = []
        for raw_path in asset.get("paths", []) or []:
            target = _node_id_for_rel_path(str(raw_path))
            if target:
                relations.append(_rel("defined_in", target))
        for raw_path in asset.get("evidence_paths", []) or []:
            target = _node_id_for_rel_path(str(raw_path))
            if target:
                relations.append(_rel("used_by", target))
        nodes.append(_node(
            "asset",
            _asset_node_id(kind, asset_id),
            asset_id,
            metadata=metadata,
            relations=_dedupe_relations(relations),
        ))
    return nodes


def ingest_claims(root: Path) -> list[dict]:
    claim_dir = Path(root) / "agents" / "runtime" / "task_claims"
    if not claim_dir.is_dir():
        return []
    nodes: list[dict] = []
    for path in sorted(claim_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        cid = str(payload.get("claim_id") or path.stem).strip()
        relations = []
        task_id = str(payload.get("task_id") or "").strip()
        if task_id:
            relations.append(_rel("executes", task_id))
        nodes.append(_node(
            "claim", cid, cid,
            metadata={"status": payload.get("status"), "agent_role": payload.get("agent_role"),
                      "active": str(payload.get("status") or "").lower() in ACTIVE_CLAIM_STATUSES},
            relations=relations,
        ))
    return nodes


def ingest_git(root: Path, limit: int = 200) -> list[dict]:
    if limit <= 0:
        return []
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", f"-{limit}", "--no-merges", "--pretty=format:%H%x09%cs%x09%s"],
            capture_output=True, text=True, timeout=20, encoding="utf-8", errors="replace",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    if result.returncode != 0:
        return []
    nodes: list[dict] = []
    seen_pr: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        sha, when, subject = parts
        relations = [_rel("mentions", ref) for ref in sorted(set(TASK_REF_RE.findall(subject)))]
        for pr_num in sorted(set(PR_RE.findall(subject))):
            pr_id = f"PR-{pr_num}"
            relations.append(_rel("partOf", pr_id))
            if pr_id not in seen_pr:
                seen_pr.add(pr_id)
                nodes.append(_node("pr", pr_id, subject[:120], metadata={"number": pr_num}))
        nodes.append(_node("commit", sha[:12], subject[:120], metadata={"date": when, "sha": sha}, relations=relations))
    return nodes


def _load_domains(root: Path) -> dict:
    path = Path(root) / DOMAINS_REL
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def ingest_domains(root: Path) -> list[dict]:
    """Capability domains (대분류) from DOMAINS.json as top-level nodes. The child->parent
    partOf edges (member -> domain, taskset -> initiative) are wired in build_graph so they
    only attach to entities that actually exist."""
    payload = _load_domains(root)
    nodes: list[dict] = []
    for domain in payload.get("domains", []) or []:
        did = str(domain.get("id") or "").strip()
        if not did:
            continue
        nodes.append(_node(
            "domain", did, str(domain.get("title") or did),
            metadata={"summary": domain.get("summary")},
        ))
    return nodes


def _domain_membership(root: Path) -> list[tuple[str, str]]:
    """(child_id, parent_id) partOf pairs from DOMAINS.json: each domain member -> domain,
    and each taskset -> its initiative."""
    payload = _load_domains(root)
    pairs: list[tuple[str, str]] = []
    for domain in payload.get("domains", []) or []:
        did = str(domain.get("id") or "").strip()
        for member in domain.get("members", []) or []:
            member = str(member or "").strip()
            if did and member:
                pairs.append((member, did))
    for initiative, tasksets in (payload.get("initiative_tasksets") or {}).items():
        for taskset in tasksets or []:
            taskset = str(taskset or "").strip()
            if taskset and initiative:
                pairs.append((taskset, str(initiative).strip()))
    return pairs


def build_graph(root: Path, *, git_limit: int = 200) -> dict:
    root = Path(root)
    nodes: list[dict] = []
    nodes.extend(ingest_work_items(root))
    nodes.extend(ingest_reviews(root))
    nodes.extend(ingest_claims(root))
    nodes.extend(ingest_git(root, limit=git_limit))
    nodes.extend(ingest_domains(root))
    nodes.extend(ingest_docs(root))
    nodes.extend(ingest_code_modules(root))
    nodes.extend(ingest_configs_and_schemas(root))
    nodes.extend(ingest_assets(root))
    seen: set[str] = set()
    unique: list[dict] = []
    for node in nodes:
        nid = str(node.get("id") or "")
        if not nid or nid in seen:
            continue
        seen.add(nid)
        unique.append(node)

    # Prune soft derived edges to non-existent targets. Body/code/config scanning
    # intentionally matches broadly; missing endpoints should not drown real graph
    # integrity gaps. Structural edges (partOf) and active claim executes edges keep
    # dangling targets so lint still flags actionable broken state.
    node_ids = {str(n.get("id") or "") for n in unique}
    for node in unique:
        relations = node.get("relations") or []
        kept = []
        for relation in relations:
            rel_type = str(relation.get("type") or "")
            target = str(relation.get("target") or "")
            if not target or target in node_ids:
                kept.append(relation)
                continue
            if rel_type in SOFT_REL_TYPES:
                continue
            if (
                rel_type == "executes"
                and str(node.get("kind") or "") == "claim"
                and not bool((node.get("metadata") or {}).get("active"))
            ):
                continue
            kept.append(relation)
        if len(kept) != len(relations):
            node["relations"] = kept

    # Wire capability-domain membership: attach a `partOf` edge from each existing child
    # to its existing parent (member -> domain, taskset -> initiative). Skipping missing
    # endpoints keeps the edges clean and resolves the orphan-initiative/domain lint.
    by_id = {str(n.get("id") or ""): n for n in unique}
    for child_id, parent_id in _domain_membership(root):
        child = by_id.get(child_id)
        if child is None or parent_id not in by_id:
            continue
        relations = child.setdefault("relations", [])
        edge = {"type": "partOf", "target": parent_id}
        if edge not in relations:
            relations.append(edge)

    edge_count = sum(len(n.get("relations") or []) for n in unique)
    return {
        "schema": SCHEMA,
        "generated_at": date.today().isoformat(),
        "node_count": len(unique),
        "edge_count": edge_count,
        "kind_counts": dict(sorted(Counter(n["kind"] for n in unique).items())),
        "nodes": unique,
    }


# --------------------------------------------------------------------------- index


@dataclass
class GraphIndex:
    by_id: dict[str, dict] = field(default_factory=dict)
    forward: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    backward: dict[str, list[tuple[str, str]]] = field(default_factory=dict)


def build_index(graph: dict) -> GraphIndex:
    idx = GraphIndex()
    for node in graph.get("nodes", []):
        nid = str(node.get("id") or "")
        if not nid:
            continue
        idx.by_id[nid] = node
        idx.forward.setdefault(nid, [])
        for relation in node.get("relations") or []:
            rel_type = str(relation.get("type") or "")
            target = str(relation.get("target") or "")
            if not target:
                continue
            idx.forward[nid].append((rel_type, target))
            idx.backward.setdefault(target, []).append((rel_type, nid))
    return idx


# --------------------------------------------------------------------------- query


def get(idx: GraphIndex, node_id: str) -> dict | None:
    return idx.by_id.get(node_id)


def neighbors(idx: GraphIndex, node_id: str, *, rel: str | None = None, depth: int = 1) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    frontier = [node_id]
    for _ in range(max(1, depth)):
        nxt: list[str] = []
        for nid in frontier:
            for rel_type, target in idx.forward.get(nid, []):
                if rel and rel_type != rel:
                    continue
                if (rel_type, target) not in seen:
                    seen.add((rel_type, target))
                    out.append((rel_type, target))
                    nxt.append(target)
        frontier = nxt
    return out


def backlinks(idx: GraphIndex, node_id: str, *, rel: str | None = None) -> list[tuple[str, str]]:
    return [(r, s) for r, s in idx.backward.get(node_id, []) if not rel or r == rel]


def path(idx: GraphIndex, source: str, target: str, *, max_depth: int = 8) -> list[str]:
    if source == target and source in idx.by_id:
        return [source]
    queue: deque[list[str]] = deque([[source]])
    visited = {source}
    while queue:
        trail = queue.popleft()
        if len(trail) > max_depth:
            continue
        for _, nxt in idx.forward.get(trail[-1], []):
            if nxt == target:
                return trail + [nxt]
            if nxt not in visited:
                visited.add(nxt)
                queue.append(trail + [nxt])
    return []


def context_pack(idx: GraphIndex, node_id: str, *, depth: int = 1) -> dict[str, Any]:
    root = idx.by_id.get(node_id)
    fwd_ids: list[str] = []
    for _, target in neighbors(idx, node_id, depth=depth):
        if target in idx.by_id and target not in fwd_ids:
            fwd_ids.append(target)
    bwd_ids: list[str] = []
    for _, source in backlinks(idx, node_id):
        if source in idx.by_id and source not in bwd_ids:
            bwd_ids.append(source)
    return {
        "root": root,
        "neighbors": [idx.by_id[i] for i in fwd_ids],
        "backlinks": [idx.by_id[i] for i in bwd_ids],
    }


_SCOPE_RE = re.compile(r"^(?:kind:|@)(\w[\w-]*)\s+(.*)$", re.IGNORECASE)


def search(graph: dict, query: str, *, kinds: list[str] | None = None, limit: int = 50) -> list[dict]:
    raw = (query or "").strip()
    scoped_kind: str | None = None
    match = _SCOPE_RE.match(raw)
    if match:
        scoped_kind, raw = match.group(1).lower(), match.group(2).strip()
    kind_filter = {scoped_kind} if scoped_kind else ({k.lower() for k in kinds} if kinds else None)
    needle = raw.lower()
    ranked: list[tuple[int, str, dict]] = []
    for node in graph.get("nodes", []):
        if kind_filter and str(node.get("kind", "")).lower() not in kind_filter:
            continue
        eid = str(node.get("id", ""))
        title = str(node.get("title", ""))
        if not needle:
            score = 1
        elif needle in eid.lower():
            score = 3
        elif needle in title.lower():
            score = 2
        elif needle in json.dumps(node.get("metadata", {}), ensure_ascii=False).lower():
            score = 1
        else:
            continue
        ranked.append((score, eid, node))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    return [node for _, _, node in ranked[:limit]]


def check_graph(graph: dict) -> list[str]:
    findings: list[str] = []
    if str(graph.get("schema") or "") != SCHEMA:
        findings.append(f"schema:expected-{SCHEMA}")
    ids = {str(n.get("id") or "") for n in graph.get("nodes", [])}
    for node in graph.get("nodes", []):
        nid = str(node.get("id") or "")
        for relation in node.get("relations") or []:
            target = str(relation.get("target") or "")
            if target and target not in ids:
                findings.append(f"dangling:{nid}->{relation.get('type')}->{target}")
    return findings


# --------------------------------------------------------------------------- CLI


def _load_or_build(args: argparse.Namespace) -> dict:
    if getattr(args, "from_file", False):
        path = Path(args.root) / GRAPH_REL
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return build_graph(Path(args.root), git_limit=getattr(args, "git_limit", 200))


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
    common.add_argument("--from-file", action="store_true", default=False,
                        help="load KNOWLEDGE-GRAPH.json instead of rebuilding")
    # SUPPRESS defaults so the same flags may follow the subcommand without
    # clobbering a value given before it.
    post = argparse.ArgumentParser(add_help=False)
    post.add_argument("--root", type=Path, default=argparse.SUPPRESS)
    post.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    post.add_argument("--git-limit", type=int, default=argparse.SUPPRESS)
    post.add_argument("--from-file", action="store_true", default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(description="Agent-first knowledge graph: build + query", parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", parents=[post], help="build the graph (optionally persist canonical JSON)")
    p_build.add_argument("--write", action="store_true")
    p_get = sub.add_parser("get", parents=[post]); p_get.add_argument("id")
    p_search = sub.add_parser("search", parents=[post]); p_search.add_argument("query"); p_search.add_argument("--kind", action="append", default=[]); p_search.add_argument("--limit", type=int, default=50)
    p_nb = sub.add_parser("neighbors", parents=[post]); p_nb.add_argument("id"); p_nb.add_argument("--rel"); p_nb.add_argument("--depth", type=int, default=1)
    p_bl = sub.add_parser("backlinks", parents=[post]); p_bl.add_argument("id"); p_bl.add_argument("--rel")
    p_path = sub.add_parser("path", parents=[post]); p_path.add_argument("source"); p_path.add_argument("target")
    p_cp = sub.add_parser("context-pack", parents=[post]); p_cp.add_argument("id"); p_cp.add_argument("--depth", type=int, default=1)
    sub.add_parser("check", parents=[post])

    args = parser.parse_args(argv)
    graph = _load_or_build(args)

    if args.command == "build":
        if args.write:
            out = Path(args.root) / GRAPH_REL
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _emit({"nodes": graph["node_count"], "edges": graph["edge_count"], "kinds": graph["kind_counts"],
               "written": bool(args.write)}, args.json,
              human=f"knowledge-graph: nodes={graph['node_count']} edges={graph['edge_count']} written={bool(args.write)}")
        return 0

    idx = build_index(graph)
    if args.command == "get":
        _emit(get(idx, args.id), args.json)
    elif args.command == "search":
        _emit(search(graph, args.query, kinds=args.kind or None, limit=args.limit), args.json)
    elif args.command == "neighbors":
        _emit({"id": args.id, "neighbors": [list(e) for e in neighbors(idx, args.id, rel=args.rel, depth=args.depth)]}, args.json)
    elif args.command == "backlinks":
        _emit({"id": args.id, "backlinks": [list(e) for e in backlinks(idx, args.id, rel=args.rel)]}, args.json)
    elif args.command == "path":
        _emit({"path": path(idx, args.source, args.target)}, args.json)
    elif args.command == "context-pack":
        _emit(context_pack(idx, args.id, depth=args.depth), args.json)
    elif args.command == "check":
        findings = check_graph(graph)
        _emit({"findings": findings, "ok": not findings}, args.json,
              human=f"knowledge-graph check: findings={len(findings)}")
        return 1 if findings else 0
    return 0


if __name__ == "__main__":
    enable_utf8_stdout()
    raise SystemExit(main())
