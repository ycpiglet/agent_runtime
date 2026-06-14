"""Tests for knowledge_lint_gate — enforce lint only on large knowledge-data changes.

Small edits stay in existing context and rarely break the graph; a large batch is when
stale/dangling/duplicate creep in. The gate runs lint as a hard check only above a
(tunable) changed-file threshold, and is watch-only below it. Mirrors closure_gate.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import knowledge_lint_gate as klg  # noqa: E402


def test_assess_disabled_always_passes():
    result = klg.assess(ROOT, disabled=True)
    assert result["decision"] == "pass"
    assert result["enforced"] is False
    assert result["reason"] == "gate-disabled"


def test_assess_below_threshold_is_watch_and_skips_build(monkeypatch):
    # force a low change count; the graph build must NOT run (stays cheap)
    monkeypatch.setattr(klg, "count_changed_knowledge_files", lambda *a, **k: 2)
    monkeypatch.setattr(klg.kg, "build_graph", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not build")))
    result = klg.assess(ROOT, threshold=10, disabled=False)
    assert result["decision"] == "pass"
    assert result["enforced"] is False
    assert result["reason"] == "below-threshold"
    assert result["changed"] == 2


def test_assess_enforced_blocks_on_block_findings(monkeypatch):
    monkeypatch.setattr(klg, "count_changed_knowledge_files", lambda *a, **k: 25)
    monkeypatch.setattr(klg.kg, "build_graph", lambda *a, **k: {"nodes": []})
    monkeypatch.setattr(klg.kl, "lint", lambda root, graph: [
        {"code": "duplicate-id", "severity": "block", "id": "X", "detail": "dup"},
        {"code": "orphan-entity", "severity": "watch", "id": "Y", "detail": "lonely"}])
    result = klg.assess(ROOT, threshold=10, disabled=False)
    assert result["decision"] == "block"
    assert result["enforced"] is True
    assert len(result["blocks"]) == 1 and result["blocks"][0]["code"] == "duplicate-id"


def test_assess_enforced_clean_passes(monkeypatch):
    monkeypatch.setattr(klg, "count_changed_knowledge_files", lambda *a, **k: 25)
    monkeypatch.setattr(klg.kg, "build_graph", lambda *a, **k: {"nodes": []})
    monkeypatch.setattr(klg.kl, "lint", lambda root, graph: [])
    result = klg.assess(ROOT, threshold=10, disabled=False)
    assert result["decision"] == "pass"
    assert result["enforced"] is True


def test_count_changed_knowledge_files(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "REVIEW-a.md").write_text("a", encoding="utf-8")
    (reviews / "REVIEW-b.md").write_text("b", encoding="utf-8")
    (tmp_path / "unrelated.txt").write_text("x", encoding="utf-8")  # not a knowledge path
    # untracked knowledge files are counted
    count = klg.count_changed_knowledge_files(tmp_path, window_hours=24)
    assert count == 2


def test_cli_check_exit_zero_when_not_blocking(monkeypatch, capsys):
    monkeypatch.setattr(klg, "count_changed_knowledge_files", lambda *a, **k: 1)
    rc = klg.main(["--root", str(ROOT), "--check"])
    assert rc == 0
    assert "watch" in capsys.readouterr().out
