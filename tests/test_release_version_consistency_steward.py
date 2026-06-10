from __future__ import annotations

from pathlib import Path

from scripts import release_version_consistency_steward as steward


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_release_steward_passes_matching_versions(tmp_path: Path) -> None:
    write(tmp_path / "pyproject.toml", "[project]\nversion = \"1.0.0\"\n")
    write(tmp_path / "agents/project/release/RELEASE.yml", "version: 1.0.0\n")
    report = steward.build_report(tmp_path)
    assert report["status"] == "pass"


def test_release_steward_blocks_mismatching_versions(tmp_path: Path) -> None:
    write(tmp_path / "pyproject.toml", "[project]\nversion = \"1.0.0\"\n")
    write(tmp_path / "agents/project/release/RELEASE.yml", "version: 1.0.1\n")
    report = steward.build_report(tmp_path)
    assert report["status"] == "block"
    assert report["findings"][0]["category"] == "release-version-mismatch"


def test_release_steward_watches_missing_release_state(tmp_path: Path) -> None:
    write(tmp_path / "pyproject.toml", "[project]\nversion = \"1.0.0\"\n")
    report = steward.build_report(tmp_path)
    assert report["status"] == "watch"
