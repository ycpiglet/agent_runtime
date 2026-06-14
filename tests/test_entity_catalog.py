import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import entity_catalog as ec  # noqa: E402


def test_real_catalog_builds_and_validates() -> None:
    catalog = ec.build_catalog()
    assert catalog["schema"] == ec.SCHEMA
    assert catalog["entity_count"] > 0
    # Only watch-level findings allowed on the real repo (dangling = archived refs).
    hard = [f for f in ec.check_catalog(catalog) if not f.startswith("watch:")]
    assert hard == [], hard
    kinds = catalog["kind_counts"]
    assert kinds.get("task", 0) > 0
    assert kinds.get("taskset", 0) > 0
    assert "host_feedback" in kinds


def test_relations_are_typed_and_directional() -> None:
    catalog = ec.build_catalog()
    # host-feedback entities address tasks
    host = [e for e in catalog["entities"] if e["kind"] == "host_feedback"]
    assert host and any(r["type"] == "addresses" for e in host for r in e["relations"])
    # tasks are partOf a taskset (parent relation derived from classification)
    tasks = [e for e in catalog["entities"] if e["kind"] == "task"]
    assert any(r["type"] == "partOf" for e in tasks for r in e["relations"])
    # review/verification records reference the task in their filename
    reviews = [e for e in catalog["entities"] if e["kind"] in ("verification", "council", "review")]
    assert any(r["type"] == "references" for e in reviews for r in e["relations"])


def test_check_flags_structural_errors() -> None:
    bad = {"schema": ec.SCHEMA, "entities": [{"kind": "", "id": "", "title": ""}]}
    findings = ec.check_catalog(bad)
    assert any("missing-kind" in f for f in findings)
    assert any("missing-id" in f for f in findings)
    assert any("missing-title" in f for f in findings)


def test_every_entity_has_uniform_envelope() -> None:
    catalog = ec.build_catalog()
    for entity in catalog["entities"]:
        assert set(entity.keys()) >= {"kind", "id", "title", "metadata", "relations"}
        assert isinstance(entity["relations"], list)
        for relation in entity["relations"]:
            assert set(relation.keys()) == {"type", "target"}
