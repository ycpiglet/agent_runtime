import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reviews_maintenance as rm  # noqa: E402


def _mk(reviews: Path, name: str) -> None:
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / name).write_text("---\ntype: review\n---\n# x\n", encoding="utf-8")


def test_scan_buckets_by_month(tmp_path: Path) -> None:
    reviews = tmp_path / "reviews"
    _mk(reviews, "REVIEW-2026-06-01-a.md")
    _mk(reviews, "MEETING-2026-06-02-b.md")
    _mk(reviews, "SEMINAR-2026-07-01-c.md")
    _mk(reviews, "no-date-here.md")
    info = rm.scan(reviews)
    assert info["file_count"] == 4
    assert info["by_month"] == {"2026-06": 2, "2026-07": 1}
    assert info["undated"] == 1
    assert info["months"] == 2


def test_check_passes_below_threshold_and_flags_above(tmp_path: Path, monkeypatch) -> None:
    reviews = tmp_path / "reviews"
    for i in range(3):
        _mk(reviews, f"REVIEW-2026-06-{i:02d}-x.md")
    # Below threshold -> no findings.
    assert rm.threshold_findings(rm.scan(reviews)) == []
    # Lower the threshold to force a finding (sharding becomes due).
    monkeypatch.setattr(rm, "MONTH_FILE_THRESHOLD", 2)
    findings = rm.threshold_findings(rm.scan(reviews))
    assert any("reviews-shard-due:2026-06" in f for f in findings)


def test_plan_is_readonly_and_maps_to_month_dirs(tmp_path: Path) -> None:
    reviews = tmp_path / "reviews"
    _mk(reviews, "REVIEW-2026-06-01-a.md")
    before = {p.name for p in reviews.glob("*.md")}
    plan = rm.shard_plan(reviews)
    after = {p.name for p in reviews.glob("*.md")}
    assert before == after  # planner never moves files
    assert plan["mapping"] == [("REVIEW-2026-06-01-a.md", "reviews/2026-06/REVIEW-2026-06-01-a.md")]
