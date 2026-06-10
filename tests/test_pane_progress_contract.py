from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "agents" / "project" / "evals" / "pane-progress-v1.jsonl"


def _rows() -> list[dict[str, object]]:
    return [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_pane_progress_goldset_exists_and_has_required_case_types():
    rows = _rows()
    case_types = {row["case_type"] for row in rows}
    assert {"typical", "edge", "adversarial", "ambiguous", "access-controlled"}.issubset(case_types)
    assert len(rows) >= 6


def test_pane_progress_goldset_rows_have_contract_metadata():
    for row in _rows():
        assert row["id"].startswith("pane-progress-")
        assert row["domain"] == "runtime-progress"
        assert row["source_refs"]
        contract = row["query_contract"]
        assert contract["resource"] in {"agents", "claims", "task_sets"}
        assert contract["requires"]
        assert row["expected_outcome"]
