from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import multipane_process_audit


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "multipane_process_audit.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False) + "\n")


def test_process_audit_reports_missing_scribe_and_retro(tmp_path: Path) -> None:
    _write(tmp_path / "reviews" / "REVIEW-1.md", "# Review\n")
    _write(
        tmp_path / "agents" / "project" / "MULTIPANE-PROCESS-POLICY.yml",
        "required_artifacts:\n  - REVIEW\n  - RETRO\nrequired_roles:\n  - scribe\n",
    )

    report = multipane_process_audit.audit(tmp_path)

    assert "artifact:RETRO" in report["missing"]
    assert "role:scribe" in report["missing"]
    assert report["status"] == "watch"
    assert report["observed"]["artifacts"]["REVIEW"] == 1


def test_process_audit_counts_claim_roles_without_prose_mentions(tmp_path: Path) -> None:
    _write(
        tmp_path / "agents" / "project" / "MULTIPANE-PROCESS-POLICY.yml",
        "required_roles:\n  - qa\n  - scribe\nmonitored_roles:\n  - reviewer\n",
    )
    _write_json(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-qa.json",
        {"claim_id": "CLAIM-qa", "agent_role": "qa", "status": "released"},
    )
    _write(tmp_path / "reviews" / "REVIEW-scribe-mention.md", "scribe mentioned in prose only\n")

    report = multipane_process_audit.audit(tmp_path)

    assert "role:qa" not in report["missing"]
    assert "role:scribe" in report["missing"]
    assert report["observed"]["roles"]["qa"] == 1


def test_process_audit_cli_check_does_not_fail_watch_findings(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "project" / "MULTIPANE-PROCESS-POLICY.yml", "required_artifacts:\n  - RETRO\n")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert "multipane-process-audit: watch" in result.stdout
    assert "artifact:RETRO" in result.stdout
