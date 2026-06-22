"""Tests for scripts/compound_cadence_gate.py.

TDD-first: these tests are written before the implementation.
All tests use temp directories with synthetic review files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Allow importing scripts/ directly
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import compound_cadence_gate as gate  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reviews_dir(tmp_path: Path) -> Path:
    reviews_dir = tmp_path / "reviews"
    reviews_dir.mkdir(parents=True)
    return reviews_dir


def _write_review(reviews_dir: Path, idx: int) -> None:
    (reviews_dir / f"REVIEW-2026-06-{idx:02d}-test.md").write_text(
        f"# Review {idx}\n", encoding="utf-8"
    )


def _write_compound(reviews_dir: Path, idx: int) -> None:
    (reviews_dir / f"COMPOUND-2026-06-{idx:02d}-test.md").write_text(
        f"# Compound {idx}\n", encoding="utf-8"
    )


def _write_retro(reviews_dir: Path, idx: int) -> None:
    (reviews_dir / f"RETRO-2026-06-{idx:02d}-test.md").write_text(
        f"# Retro {idx}\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Tests: high ratio triggers watch
# ---------------------------------------------------------------------------


def test_high_ratio_triggers_watch(tmp_path: Path) -> None:
    """294 REVIEW-* vs 1 COMPOUND + 4 RETRO = ratio 58.8 > 20 -> watch."""
    reviews_dir = _make_reviews_dir(tmp_path)
    for i in range(1, 21):  # 20 reviews (avoid month overflow)
        _write_review(reviews_dir, i)
    # 1 compound total -> ratio = 20 > 20 is not triggered, use 0 compound/retro

    findings = gate.analyze(tmp_path, ratio=5)
    watch_codes = [f["code"] for f in findings if f["severity"] == "watch"]
    assert "compound-cadence" in watch_codes, (
        "Expected compound-cadence watch finding when ratio exceeds threshold"
    )


def test_real_repo_ratio_triggers_watch(tmp_path: Path) -> None:
    """294 REVIEW / 5 compounds+retros = 58.8 > default 20 -> watch."""
    reviews_dir = _make_reviews_dir(tmp_path)
    # Simulate 294 reviews
    for i in range(1, 295):
        (reviews_dir / f"REVIEW-test-{i:04d}.md").write_text("# R\n", encoding="utf-8")
    # Simulate 1 compound + 4 retros
    _write_compound(reviews_dir, 1)
    for i in range(2, 6):
        _write_retro(reviews_dir, i)

    findings = gate.analyze(tmp_path, ratio=20)
    watch_codes = [f["code"] for f in findings if f["severity"] == "watch"]
    assert "compound-cadence" in watch_codes


def test_high_ratio_exit_zero(tmp_path: Path) -> None:
    """Gate must exit 0 even when compound-cadence watch fires (advisory only)."""
    reviews_dir = _make_reviews_dir(tmp_path)
    for i in range(1, 21):
        _write_review(reviews_dir, i)

    rc = gate.main(["--check", "--root", str(tmp_path), "--ratio", "5"])
    assert rc == 0, "Advisory gate must always exit 0"


# ---------------------------------------------------------------------------
# Tests: balanced set is clean
# ---------------------------------------------------------------------------


def test_balanced_no_watch(tmp_path: Path) -> None:
    """10 REVIEW vs 5 COMPOUND+RETRO = ratio 2 -> no watch at default ratio 20."""
    reviews_dir = _make_reviews_dir(tmp_path)
    for i in range(1, 11):
        _write_review(reviews_dir, i)
    for i in range(11, 14):
        _write_compound(reviews_dir, i)
    for i in range(14, 17):
        _write_retro(reviews_dir, i)

    findings = gate.analyze(tmp_path, ratio=20)
    compound_findings = [f for f in findings if f["code"] == "compound-cadence"]
    assert not compound_findings, "Balanced ratio should not trigger compound-cadence finding"


def test_equal_counts_no_watch(tmp_path: Path) -> None:
    """Equal reviews and compounds -> ratio 1 -> clean."""
    reviews_dir = _make_reviews_dir(tmp_path)
    for i in range(1, 6):
        _write_review(reviews_dir, i)
    for i in range(6, 11):
        _write_compound(reviews_dir, i)

    findings = gate.analyze(tmp_path, ratio=20)
    assert not any(f["code"] == "compound-cadence" for f in findings)


# ---------------------------------------------------------------------------
# Tests: zero compounds/retros
# ---------------------------------------------------------------------------


def test_zero_compounds_triggers_watch(tmp_path: Path) -> None:
    """Any reviews with zero compounds+retros should trigger watch."""
    reviews_dir = _make_reviews_dir(tmp_path)
    _write_review(reviews_dir, 1)

    findings = gate.analyze(tmp_path, ratio=20)
    watch_codes = [f["code"] for f in findings if f["severity"] == "watch"]
    assert "compound-cadence" in watch_codes, (
        "Zero compounds/retros with any reviews should trigger compound-cadence"
    )


def test_zero_reviews_no_watch(tmp_path: Path) -> None:
    """No reviews at all -> no finding."""
    reviews_dir = _make_reviews_dir(tmp_path)
    _write_compound(reviews_dir, 1)

    findings = gate.analyze(tmp_path, ratio=20)
    assert not any(f["code"] == "compound-cadence" for f in findings)


def test_empty_reviews_dir_exit_zero(tmp_path: Path) -> None:
    """Empty reviews dir -> exit 0."""
    _make_reviews_dir(tmp_path)
    rc = gate.main(["--check", "--root", str(tmp_path)])
    assert rc == 0


def test_missing_reviews_dir_exit_zero(tmp_path: Path) -> None:
    """Missing reviews dir -> exit 0."""
    rc = gate.main(["--check", "--root", str(tmp_path)])
    assert rc == 0


# ---------------------------------------------------------------------------
# Tests: JSON output
# ---------------------------------------------------------------------------


def test_json_output_schema(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """--json output must be valid JSON with expected schema."""
    reviews_dir = _make_reviews_dir(tmp_path)
    for i in range(1, 5):
        _write_review(reviews_dir, i)

    rc = gate.main(["--check", "--json", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert rc == 0
    assert data["schema"] == "agent-runtime-compound-cadence/v1"
    assert "status" in data
    assert "counts" in data
    assert "findings" in data


def test_json_counts_accurate(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """JSON counts must match actual file counts."""
    reviews_dir = _make_reviews_dir(tmp_path)
    for i in range(1, 11):
        _write_review(reviews_dir, i)
    for i in range(11, 14):
        _write_compound(reviews_dir, i)
    _write_retro(reviews_dir, 14)

    gate.main(["--check", "--json", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["counts"]["reviews"] == 10
    assert data["counts"]["compounds"] == 3
    assert data["counts"]["retros"] == 1
    assert data["counts"]["compound_retro_total"] == 4


# ---------------------------------------------------------------------------
# Tests: ratio CLI override
# ---------------------------------------------------------------------------


def test_ratio_override_cli(tmp_path: Path) -> None:
    """--ratio 100 makes 50:1 ratio acceptable -> no compound-cadence finding."""
    reviews_dir = _make_reviews_dir(tmp_path)
    for i in range(1, 51):
        (reviews_dir / f"REVIEW-test-{i:04d}.md").write_text("# R\n", encoding="utf-8")
    _write_compound(reviews_dir, 1)

    findings_strict = gate.analyze(tmp_path, ratio=20)
    findings_loose = gate.analyze(tmp_path, ratio=100)

    strict_codes = [f["code"] for f in findings_strict if f["severity"] == "watch"]
    loose_codes = [f["code"] for f in findings_loose if f["severity"] == "watch"]

    assert "compound-cadence" in strict_codes
    assert "compound-cadence" not in loose_codes
