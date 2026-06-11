from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "co_location_gate.py"
SPEC = importlib.util.spec_from_file_location("co_location_gate", MODULE_PATH)
assert SPEC and SPEC.loader
co_location_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(co_location_gate)


def _write_valid_inputs(root: Path) -> dict[str, Path]:
    artifact = root / "artifact.txt"
    artifact.write_text("ok\n", encoding="utf-8")

    skill_map = root / "skill.yml"
    skill_map.write_text(
        """
- skill_id: runtime-skill
  owner: lead-engineer
  scope: runtime
  criticality: high
  change_policy: hard
  linked_tasks:
    - TASK-AR-204
  artifacts:
    - path: artifact.txt
      kind: script
""".lstrip(),
        encoding="utf-8",
    )

    context_sources = root / "context.yml"
    context_sources.write_text(
        """
source_tiers:
  - id: canonical
    owner: lead-engineer
    access_level: local
    freshness_sla: 30d
    lineage: direct
    confidence_weight: 1.0
definition_policy: required
query_policy: required
required_metadata: []
required_fields: []
""".lstrip(),
        encoding="utf-8",
    )

    dataset_catalog = root / "datasets.yml"
    dataset_catalog.write_text(
        """
datasets:
  - id: regression
    owner: qa
    source_tier: canonical
    location: artifact.txt
    minimum_score: 0.90
""".lstrip(),
        encoding="utf-8",
    )

    return {
        "skill_map": skill_map,
        "context_sources": context_sources,
        "dataset_catalog": dataset_catalog,
    }


def test_default_evaluate_skips_live_migration_map(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    inputs = _write_valid_inputs(tmp_path)

    report = co_location_gate.evaluate(
        inputs["skill_map"],
        None,
        inputs["context_sources"],
        inputs["dataset_catalog"],
    )

    assert report["status"] == "pass"
    assert report["inputs"]["migration_map"] is None
    assert report["sections"]["migration_compat_map"]["status"] == "skipped"


def test_explicit_migration_map_still_validates_archive_input(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    inputs = _write_valid_inputs(tmp_path)
    migration_map = tmp_path / "migration.yml"
    migration_map.write_text(
        """
items:
  - id: archived-source
    status: kept
    owner: lead-engineer
    approved_by: TASK-AR-220
    decision_date: 2026-06-11
    justification: archived portability evidence
    expiry: 2026-12-31
""".lstrip(),
        encoding="utf-8",
    )

    report = co_location_gate.evaluate(
        inputs["skill_map"],
        migration_map,
        inputs["context_sources"],
        inputs["dataset_catalog"],
    )

    assert report["status"] == "pass"
    assert report["inputs"]["migration_map"] == migration_map.as_posix()
    assert report["sections"]["migration_compat_map"]["items"] == 1
