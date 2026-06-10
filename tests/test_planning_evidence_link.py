from __future__ import annotations

import json
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "planning_evidence_link.py"
SPEC = importlib.util.spec_from_file_location("planning_evidence_link", SCRIPT)
assert SPEC is not None
planning_evidence_link = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(planning_evidence_link)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_links_failed_grader_trace_to_block_proposal(tmp_path: Path) -> None:
    grader = _write(
        tmp_path / "grader.json",
        {
            "grader_results": [
                {
                    "case_id": "case-1",
                    "trace_id": "trace-1",
                    "score": 0.2,
                    "findings": ["wrong-route"],
                }
            ]
        },
    )

    report = planning_evidence_link.build_report([("grader", grader)])

    assert report["status"] == "block"
    assert report["proposals"][0]["kind"] == "grader_regression"
    assert report["proposals"][0]["trace_id"] == "trace-1"
    assert report["proposals"][0]["route"] == "TASK-AR-243"


def test_links_correction_proposal_to_watch_record(tmp_path: Path) -> None:
    correction = _write(
        tmp_path / "correction.json",
        {"status": "pass", "written": ["agents/project/corrections/example.md"]},
    )

    report = planning_evidence_link.build_report([("correction", correction)])

    assert report["status"] == "watch"
    assert report["proposals"][0]["kind"] == "correction_proposal"
    assert report["proposals"][0]["evidence_id"] == "agents/project/corrections/example.md"


def test_missing_a2a_chain_blocks_planning_acceptance(tmp_path: Path) -> None:
    a2a = _write(tmp_path / "a2a.json", {"status": "pass", "chain_results": []})

    report = planning_evidence_link.build_report([("a2a", a2a)])

    assert report["status"] == "block"
    assert report["proposals"][0]["kind"] == "missing_trace_chain"
    assert report["proposals"][0]["route"] == "TASK-AR-208"
