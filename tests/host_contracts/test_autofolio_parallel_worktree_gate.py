from __future__ import annotations

from pathlib import Path

import pytest

from scripts.parallel_worktree_gate import ClaimRecord, _continuity_findings


def _active_claim(root: Path) -> ClaimRecord:
    return ClaimRecord(path=root / "claim.json", payload={"status": "claimed"})


def _write_status(root: Path, relative_path: str, text: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("marker", ["다음 세션", "다음 단계", "인수인계"])
def test_continuity_accepts_host_status_with_korean_resume_marker(
    tmp_path: Path, marker: str
):
    _write_status(
        tmp_path,
        "agents/lead_engineer/STATUS.md",
        f"# STATUS\n\n## 활성 작업 ({marker} 시작점)\n",
    )

    assert _continuity_findings(tmp_path, [_active_claim(tmp_path)]) == []


@pytest.mark.parametrize("marker", ["Handoff Checklist", "Next Steps"])
def test_continuity_preserves_root_status_english_markers(
    tmp_path: Path, marker: str
):
    _write_status(tmp_path, "STATUS.md", f"# STATUS\n\n## {marker}\n")

    assert _continuity_findings(tmp_path, [_active_claim(tmp_path)]) == []


def test_continuity_prefers_root_status_over_valid_host_fallback(tmp_path: Path):
    _write_status(tmp_path, "STATUS.md", "# STATUS\n\n## Current Work\n")
    _write_status(
        tmp_path,
        "agents/lead_engineer/STATUS.md",
        "# STATUS\n\n## 활성 작업 (다음 세션 시작점)\n",
    )

    findings = _continuity_findings(tmp_path, [_active_claim(tmp_path)])

    assert len(findings) == 1
    assert findings[0].startswith("STATUS.md: continuity:status-handoff-missing:")
    assert "agents/lead_engineer/STATUS.md" not in findings[0]


def test_continuity_missing_status_lists_both_candidate_paths(tmp_path: Path):
    findings = _continuity_findings(tmp_path, [_active_claim(tmp_path)])

    assert len(findings) == 1
    assert "continuity:status-missing" in findings[0]
    assert "STATUS.md" in findings[0]
    assert "agents/lead_engineer/STATUS.md" in findings[0]


def test_continuity_host_status_missing_marker_names_selected_path(tmp_path: Path):
    _write_status(
        tmp_path,
        "agents/lead_engineer/STATUS.md",
        "# STATUS\n\n## Current Work\n",
    )

    findings = _continuity_findings(tmp_path, [_active_claim(tmp_path)])

    assert len(findings) == 1
    assert findings[0].startswith(
        "agents/lead_engineer/STATUS.md: continuity:status-handoff-missing:"
    )


def test_continuity_allows_fresh_host_without_status_or_active_claim(tmp_path: Path):
    assert _continuity_findings(tmp_path, []) == []
