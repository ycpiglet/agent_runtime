from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "evidence_index_generator.py"


def test_evidence_index_generator_writes_and_checks_all_reviews(tmp_path: Path) -> None:
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-a.md").write_text(
        "---\ntype: review\nid: REVIEW-a\nstatus: pass\nsignal: pass\n---\n# Review A\n",
        encoding="utf-8",
    )
    (reviews / "REPORT-b.json").write_text("{}\n", encoding="utf-8")

    write = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--write", "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert write.returncode == 0, write.stdout + write.stderr
    assert check.returncode == 0, check.stdout + check.stderr
    text = (reviews / "INDEX.md").read_text(encoding="utf-8")
    assert "`reviews/REVIEW-a.md`" in text
    assert "`reviews/REPORT-b.json`" in text


def test_evidence_index_generator_check_fails_when_index_missing_review(tmp_path: Path) -> None:
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-a.md").write_text("# Review A\n", encoding="utf-8")
    (reviews / "INDEX.md").write_text("# Evidence Index\n\n## Bottom Line\n\n## Action Board\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 1
    assert "missing-review:reviews/REVIEW-a.md" in result.stdout
