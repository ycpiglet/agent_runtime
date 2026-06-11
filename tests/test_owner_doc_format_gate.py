from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_owner_doc_format_gate_rejects_missing_risks_and_next_steps(tmp_path: Path) -> None:
    doc = tmp_path / "owner-report.md"
    doc.write_text(
        """---
signal: pass
score: 100
---

# Owner Report

## Bottom Line
- Summary.

## Signal
- pass

## Decision
- continue

## Action Board

| Item | State |
| --- | --- |
| A | pass |
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/owner_doc_format_gate.py", str(doc)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    assert "risk:missing" in result.stdout
    assert "next:missing" in result.stdout
