import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import work_index as wi  # noqa: E402


def test_real_read_surface_is_present() -> None:
    info = wi.scan()
    # Every canonical generated manifest must exist (the read surface is intact).
    assert info["missing"] == [], info["missing"]
    assert info["md_count"] > 0


def test_fts_threshold_not_tripped_below_limit(tmp_path: Path) -> None:
    info = wi.scan(tmp_path)
    # Empty root: no manifests, far below the FTS threshold.
    assert info["fts_recommended"] is False
    assert len(info["missing"]) == len(wi.READ_SURFACE)


def test_fts_threshold_logic_is_real(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "x.md").write_text("y", encoding="utf-8")
    info = wi.scan(tmp_path)
    assert info["md_count"] == 1
    assert info["fts_recommended"] is False  # 1 << 10_000
