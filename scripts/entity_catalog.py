"""Unified artifact entity catalog (TASK-AR-539).

A Backstage-style typed entity graph over the generated manifests (manifest-first,
TASK-AR-537): every meaningful artifact becomes an entity with a uniform envelope
``{kind, id, title, metadata, relations}`` and typed, directional relations.
The decision console (TASK-AR-540..545) reads ``ENTITY-CATALOG.json`` instead of
re-deriving the graph from raw files, so plan/review/work-item/host-feedback all
browse + cross-link uniformly.

Sources (read, never re-scanned from scratch where a manifest exists):
- ``WORK-ITEM-CLASSIFICATION.json`` -> initiative/taskset/task/unit entities,
  ``partOf`` relation from ``parent_id``, ordinal number + status as metadata.
- ``HOST-FEEDBACK-QUEUE.json`` -> ``host_feedback`` entities, ``addresses`` each
  linked task, with category/status/priority/source metadata.
- ``reviews/*.md`` filenames -> ``review`` entities (council/seminar/meeting/
  research/verification/review by prefix), ``references`` the TASK-AR-NNN parsed
  from the name (cheap -- no file reads).

  --check   validate envelopes + report dangling internal relation targets.
  --write   emit ENTITY-CATALOG.json.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLASSIFICATION = ROOT / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json"
HOST_QUEUE = ROOT / "agents" / "project" / "work-items" / "HOST-FEEDBACK-QUEUE.json"
REVIEWS_DIR = ROOT / "reviews"
OUTPUT = ROOT / "agents" / "project" / "work-items" / "ENTITY-CATALOG.json"
SCHEMA = "agent-runtime-entity-catalog/v1"

TASK_REF_RE = re.compile(r"TASK-AR-[0-9]+")
REVIEW_KIND_BY_PREFIX = {
    "W4B": "verification",
    "VERIFY": "verification",
    "COUNCIL": "council",
    "SEMINAR": "seminar",
    "MEETING": "meeting",
    "RESEARCH": "research",
    "REVIEW": "review",
    "GOVERNANCE": "review",
}
REVIEW_DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def _entity(kind: str, eid: str, title: str, *, metadata: dict | None = None, relations: list | None = None) -> dict:
    return {
        "kind": kind,
        "id": eid,
        "title": title,
        "metadata": metadata or {},
        "relations": relations or [],
    }


def _rel(rel_type: str, target: str) -> dict:
    return {"type": rel_type, "target": target}


def build_catalog(root: Path = ROOT) -> dict:
    entities: list[dict] = []

    # 1. Work hierarchy (initiative/taskset/task/unit) from the classification graph.
    classification = root / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json"
    if classification.exists():
        payload = json.loads(classification.read_text(encoding="utf-8"))
        for record in payload.get("records", []):
            level = str(record.get("level") or "work_item")
            eid = str(record.get("id") or "").strip()
            if not eid:
                continue
            relations = []
            parent = str(record.get("parent_id") or "").strip()
            if parent:
                relations.append(_rel("partOf", parent))
            entities.append(
                _entity(
                    level,
                    eid,
                    str(record.get("title") or eid),
                    metadata={
                        "ordinal": record.get("number"),
                        "status": record.get("status"),
                        "path": record.get("path"),
                    },
                    relations=relations,
                )
            )

    # 2. Host feedback items -> addresses the tasks they map to.
    host_queue = root / "agents" / "project" / "work-items" / "HOST-FEEDBACK-QUEUE.json"
    if host_queue.exists():
        payload = json.loads(host_queue.read_text(encoding="utf-8"))
        for entry in payload.get("entries", []):
            eid = str(entry.get("id") or "").strip()
            if not eid:
                continue
            relations = [_rel("addresses", task) for task in entry.get("tasks", [])]
            entities.append(
                _entity(
                    "host_feedback",
                    eid,
                    str(entry.get("title") or eid),
                    metadata={
                        "category": entry.get("category"),
                        "status": entry.get("status"),
                        "priority": entry.get("priority"),
                        "source": entry.get("source"),
                    },
                    relations=relations,
                )
            )

    # 3. Review/governance records -> references the task(s) named in the filename.
    reviews_dir = root / "reviews"
    if reviews_dir.exists():
        for path in sorted(reviews_dir.glob("*.md")):
            name = path.stem
            if name.upper() == "INDEX":
                continue
            prefix = name.split("-", 1)[0].upper()
            kind = REVIEW_KIND_BY_PREFIX.get(prefix, "review")
            date_match = REVIEW_DATE_RE.search(name)
            refs = sorted(set(TASK_REF_RE.findall(name)))
            relations = [_rel("references", ref) for ref in refs]
            entities.append(
                _entity(
                    kind,
                    name,
                    name,
                    metadata={
                        "date": date_match.group(1) if date_match else None,
                        "path": f"reviews/{path.name}",
                    },
                    relations=relations,
                )
            )

    kind_counts = Counter(entity["kind"] for entity in entities)
    return {
        "schema": SCHEMA,
        "generated_at": date.today().isoformat(),
        "entity_count": len(entities),
        "kind_counts": dict(sorted(kind_counts.items())),
        "entities": entities,
    }


def check_catalog(catalog: dict) -> list[str]:
    findings: list[str] = []
    if str(catalog.get("schema") or "") != SCHEMA:
        findings.append(f"schema:expected-{SCHEMA}")
    ids = set()
    for index, entity in enumerate(catalog.get("entities", [])):
        for field in ("kind", "id", "title"):
            if not str(entity.get(field) or "").strip():
                findings.append(f"entity:{index}:missing-{field}")
        ids.add(str(entity.get("id")))
    # Dangling internal relation targets (INIT/TASKSET/TASK/UNIT that are not in the
    # catalog) are reported as watch-level findings, not hard failures -- a record
    # may legitimately reference archived/external work.
    internal = re.compile(r"^(INIT-|TASKSET-|TASK-AR-|UNIT-)")
    dangling = 0
    for entity in catalog.get("entities", []):
        for relation in entity.get("relations", []):
            target = str(relation.get("target") or "")
            if internal.match(target) and target not in ids:
                dangling += 1
    if dangling:
        findings.append(f"watch:dangling-internal-relations:{dangling}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified artifact entity catalog (TASK-AR-539)")
    parser.add_argument("--check", action="store_true", help="validate envelopes; non-zero only on structural errors")
    parser.add_argument("--write", action="store_true", help="emit ENTITY-CATALOG.json")
    args = parser.parse_args()

    catalog = build_catalog()
    findings = check_catalog(catalog)
    hard = [f for f in findings if not f.startswith("watch:")]
    print(f"entity-catalog: {catalog['entity_count']} entities; kinds={catalog['kind_counts']}")
    if args.check:
        for finding in findings:
            print(f"entity-catalog: {finding}")
        print(f"findings={len(hard)}")
        return 1 if hard else 0
    if args.write:
        if hard:
            for finding in hard:
                print(f"entity-catalog: fail: {finding}")
            return 1
        OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote={OUTPUT}")
        return 0
    print(json.dumps(catalog["kind_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
