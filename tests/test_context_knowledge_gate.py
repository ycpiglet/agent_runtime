from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import context_knowledge_gate  # noqa: E402


def test_real_context_knowledge_gate_passes() -> None:
    findings = context_knowledge_gate.check_root(REPO_ROOT)

    assert findings == []


def test_ambiguous_eval_requires_full_query_contract(tmp_path: Path) -> None:
    path = tmp_path / "ambiguous.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "amb-001",
                "case_type": "ambiguous",
                "expected_outcome": "hold_for_query_contract",
                "query_contract": {
                    "business_scope": "scope",
                    "time_window": "unspecified",
                    "tolerance": "low",
                    "ambiguity_level": "high",
                    "source_tier": "context-knowledge",
                    "access_level": "project",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    findings = context_knowledge_gate._check_ambiguous_eval_file(path)

    assert f"{path.as_posix()}:amb-001:query_contract:missing:question" in findings
    assert f"{path.as_posix()}:amb-001:query_contract:missing:query_tolerance" in findings
    assert f"{path.as_posix()}:amb-001:query_contract:missing:tradeoff_preference" in findings


def test_context_knowledge_gate_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "context_knowledge_gate.py"),
            "--root",
            str(REPO_ROOT),
            "--check",
            "--out",
            str(out),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert "context-knowledge-gate: pass" in result.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
