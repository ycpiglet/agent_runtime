"""Tests for compound_cadence_gate --obligation (soft obligation mode).

`--check` stays exit 0 (watch-only); `--obligation` exits 1 when a compound is
overdue (review:compound ratio over threshold), so a closeout/cadence step can
treat it as an actionable signal. Wired ADVISORY (non-blocking) into
owner_governance_gate.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "compound_cadence_gate.py"


def _make_reviews(root: Path, reviews: int, compounds: int) -> None:
    d = root / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    for i in range(reviews):
        (d / f"REVIEW-2026-06-22-{i:03d}.md").write_text("x\n", encoding="utf-8")
    for i in range(compounds):
        (d / f"COMPOUND-2026-06-22-{i:03d}.md").write_text("x\n", encoding="utf-8")


def _run(root: Path, *flags: str) -> int:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *flags],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).returncode


def test_obligation_fires_on_high_ratio(tmp_path: Path) -> None:
    _make_reviews(tmp_path, reviews=50, compounds=0)  # ratio = inf > threshold
    assert _run(tmp_path, "--obligation") == 1


def test_obligation_clean_on_low_ratio(tmp_path: Path) -> None:
    _make_reviews(tmp_path, reviews=3, compounds=3)  # ratio 1.0 <= 20
    assert _run(tmp_path, "--obligation") == 0


def test_check_stays_exit_zero_even_when_overdue(tmp_path: Path) -> None:
    _make_reviews(tmp_path, reviews=50, compounds=0)
    assert _run(tmp_path, "--check") == 0  # watch-only, never blocks


def test_owner_governance_gate_wires_compound_obligation_advisory() -> None:
    text = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    assert "compound_cadence_gate.py" in text and "--obligation" in text
    # Must be advisory + consumer-safe: existence-guarded, never sets `failed`.
    assert "compound_cadence_gate.py\").exists()" in text
